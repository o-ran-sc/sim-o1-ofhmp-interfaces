import json
import os
import socket
import ssl
import threading

from concurrent.futures import ThreadPoolExecutor

import xml.etree.ElementTree as ET

from core.dict_factory import DictFactory, BaseTemplate
from core.extension import Extension
from core.config import Config
from core.netconf import Datastore, Netconf
from core.ves import Ves, VesMessage
from util.docker import get_hostname
from util.logging import get_pynts_logger
from util.threading import stop_event, sa_sleep
from libyang.util import LibyangError, DataType, c2str

from netconf_client.connect import connect_tls
from netconf_client.ncclient import Manager
from ncclient.transport.errors import SessionCloseError, TransportError

from feature.ves_pnfregistration import VesPnfRegistrationFeature

logger = get_pynts_logger("o-du-o1")

# Path to your TLS certificate, private key, and CA certificate
CERT_FILE = "/home/oranuser/.ssh/odu_certificate.pem"
KEY_FILE = "/home/oranuser/.ssh/private_key.pem"
CA_CERT_FILE = "/home/oranuser/.ssh/ODU_rootCA.crt"  # CA certificate to verify client certs

    
# Thread-safe dictionary to store active sessions
active_sessions = {}

# Lock to ensure thread-safe operations on the active_sessions dictionary
session_lock = threading.Lock()

class Main(Extension):
    def init(self) -> None:
        self.netconf = Netconf()
        self.config = Config()
        self.ves: Ves = Ves()
                
        self.max_workers = 5  # Number of threads in the pool

        DictFactory.add_template("3gpp-managed-element", _3GPP_ManagedElementTemplate)

    def startup(self) -> None:
        logger.info("o-du-o1 extension loaded")
                
        self.ves_pnfregistration = VesPnfRegistrationFeature()
        self.ves_pnfregistration.start()        
        
        self.netconf.operational.subscribe_oper_data_request("o-ran-aggregation-base", "/o-ran-aggregation-base:aggregated-o-ru/*", self.o_ran_aggregation_base_oper_data_cb, oper_merge=True)
        logger.debug("subscribing to operational data requests: /o-ran-aggregation-base:aggregated-o-ru/*")                
                                
        host = "::"
        port = int(os.environ.get("O_DU_CALLHOME_PORT", 4335))  # Adjust to the appropriate port for CallHome

        listener_thread = threading.Thread(target=self.accept_tls_connections, args=(host, port))
        listener_thread.start()
        
        logger.debug(f"Active sessions: {list(active_sessions.keys())}")          

        # self.load_3gpp_data()      
        # self.connect_to_oru()


        ### Sample notification from YANG Schema Mount
        # with self.netconf.connection.get_ly_ctx() as ctx:
        #     data = self.netconf.operational.get_item("/o-ran-aggregation-base:aggregated-o-ru/aggregation[ru-instance='Baciells_sRU67XXX_B122601202134000326']/o-ran-agg-ietf-hardware:ietf-hardware-model")
        #     logger.debug(f"Found xPath: {data.xpath}")
        #     if data is not None:
        #         dnode = ctx.create_data_path(data.xpath + "/ietf-hardware:hardware-state-change")            
        #         while True:
        #             logger.debug(f"Sending notification with xpath {data.xpath + '/ietf-hardware:hardware-state-change'}")
        #             self.netconf.running.notification_send_ly(dnode)
        #             time.sleep(30)
        ### end sample notification from YANG Schema Mount 
        
    def o_ran_aggregation_base_oper_data_cb(self, xpath, private_data):
      
      global active_sessions
      num_of_sessions = len(list(active_sessions.keys()))
      if num_of_sessions == 0:
        return None

      agg_base_xml = f"<aggregated-o-ru xmlns=\"urn:o-ran:agg-base:1.0\">\n"

      for _, value in active_sessions.items():        
        mgr = value["session"]
        xml_data_str = mgr.get(filter="<filter><hw:hardware xmlns:hw=\"urn:ietf:params:xml:ns:yang:ietf-hardware\"/></filter>").data_xml        

        with self.netconf.connection.get_ly_ctx() as ctx:
          ietf_hw_xml = self.get_xml_string_from_response(xml_data_str)
          aggregation_instance_xml = f"<aggregation><ru-instance>{value['hostname']}</ru-instance><ietf-hardware-model xmlns=\"urn:o-ran:agg-ietf-hardware:1.0\">{ietf_hw_xml}</ietf-hardware-model></aggregation>"
          agg_base_xml += f"{aggregation_instance_xml}"
        
      agg_base_xml += f"</aggregated-o-ru>"                      
      logger.debug(f"Constructed XML: {agg_base_xml}")
                        
      data = ctx.parse_data_mem(agg_base_xml, "xml", parse_only=True)
      return data       

    def handle_callhome_session(self, conn, addr, session_id):
      """
      Handle a single NETCONF CallHome session over TLS.
      """
      logger.info(f"Handling CallHome connection from {addr}")
      try:
          # Establish a NETCONF session using netconf_client over the TLS connection
          session = connect_tls(sock=conn, keyfile=KEY_FILE,
                                                  certfile=CERT_FILE,
                                                  ca_certs=CA_CERT_FILE)
          mgr = Manager(session, timeout=3)

          hostname_xml_data_str = mgr.get_config(source="running", filter="<filter><sys:system xmlns:sys=\"urn:ietf:params:xml:ns:yang:ietf-system\"><sys:hostname/></sys:system></filter>").data_xml
          hostname_json = self.get_json_object_from_xml(hostname_xml_data_str)
          hostname_str = hostname_json.get("ietf-system:system", {"hostname": "error-oru"}).get("hostname", "error-oru")

          # Add the session to the active_sessions dictionary
          with session_lock:
              active_sessions[session_id] = {'address': addr, 'session': mgr, 'hostname': hostname_str}
              logger.info(f"Active sessions: {list(active_sessions.keys())}")

          mgr.create_subscription()
          
          self.sync_running(session_id)                  
                        
          while not stop_event.is_set():
            try:
                # Use a simple RPC like <get> to check if the session is alive
                mgr.get(filter="<filter></filter>")
                logger.debug(f"Session {session_id} with {hostname_str} {addr} is still active")
                
                # Optionally receive notifications or perform actual tasks here
                notification = mgr.take_notification(timeout=5)
                if notification:
                    self.handle_notification(notification.notification_xml, session_id)

            except SessionCloseError:
                logger.error(f"Remote side closed the NETCONF session {session_id} from {addr}")
                break
            except TransportError as e:
                logger.error(f"Transport error in session {session_id} from {addr}: {e}")
                break

      except Exception as e:
          logger.error(f"Error handling session {session_id} from {addr}: {e}")
      finally:
          conn.close()
          # Remove the session from the active_sessions dictionary
          with session_lock:
              if session_id in active_sessions:
                  self.netconf.running.delete_item(f"/o-ran-aggregation-base:aggregated-o-ru/aggregation[ru-instance=\"{active_sessions[session_id]['hostname']}\"]")
                  self.netconf.running.apply_changes()
                  del active_sessions[session_id]
                  logger.info(f"Session {session_id} with {addr} closed")
                  logger.debug(f"Active sessions: {list(active_sessions.keys())}")


    def accept_tls_connections(self, host, port, max_connections=5):
      """
      Listens for incoming NETCONF CallHome TLS connections.
      """
      server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
      server_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
      server_socket.bind((host, port))
      server_socket.listen(max_connections)
      logger.info(f"Listening for CallHome TLS connections on {host}:{port}")

      # Create an SSL context for mutual TLS authentication
      context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
      context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
      context.load_verify_locations(cafile=CA_CERT_FILE)
      context.verify_mode = ssl.CERT_REQUIRED

      session_id = 1
      with ThreadPoolExecutor(max_workers=max_connections) as executor:
          while not stop_event.is_set():
              conn, addr = server_socket.accept()
              # tls_conn = context.wrap_socket(conn)
              logger.info(f"Accepted TLS connection from {addr}")
              executor.submit(self.handle_callhome_session, conn, addr, session_id)
              session_id += 1

    def handle_notification(self, notification_xml, session_id) -> None:
      logger.debug(f"Handling NETCONF notification: {notification_xml}")
      # Parse the XML string
      root = ET.fromstring(notification_xml)
      # Namespace dictionary
      namespaces = {
          'nc': 'urn:ietf:params:xml:ns:netconf:notification:1.0',  # for the 'notification' element
      }
      # Find the eventTime element using the namespace
      event_time_element = root.find('nc:eventTime', namespaces)

      try:
        with self.netconf.connection.get_ly_ctx() as ctx:
          dnode = ctx.parse_op_mem("xml", notification_xml, DataType.NOTIF_NETCONF)
          # parse_op_mem removes the <notification> and <eventTime> tags and retrieves only the notification itself.
          # we need to add them back manually
          j_str = dnode.print_mem("json", with_siblings=True)
          j_obj = json.loads(j_str)
          json_ev_time = {"eventTime": event_time_element.text}     
          json_notif = {"notifications:notification": json_ev_time | j_obj}
          
          if 'ietf-netconf-notifications:netconf-config-change' in j_obj.keys():
            self.sync_running(session_id)
          self.send_ves_event_notification(json_notif, dnode.module().name(), dnode.name(), c2str(dnode.module().cdata.ns), active_sessions[session_id]['hostname'])
          logger.debug(f"Received notification on {event_time_element.text} with content {json_notif}")          
          dnode.free()          
      except LibyangError as e:
        logger.error(f"Failed to get JSON object from XML: {notification_xml}. Error: {e}")

    def send_ves_event_notification(self, json_notif: str, module: str, notif_name: str, namespace: str, source_hostname: str) -> None:
      logger.debug(f"Trying to wrap {module}:{notif_name} from namespace {namespace} which came from source {source_hostname}")
      ves_event = VesEventNotificationWrapper(notif=json_notif, namespace=namespace, schema=module, notif_name=notif_name, source_oru=source_hostname)
      self.ves.execute(ves_event)
      

    def sync_running(self, session_id) -> None:
      session_details = active_sessions[session_id]
      mgr = session_details['session']
      xml_data_str = mgr.get_config(source="running", filter="<filter><hw:hardware xmlns:hw=\"urn:ietf:params:xml:ns:yang:ietf-hardware\"/></filter>").data_xml

      with self.netconf.connection.get_ly_ctx() as ctx:              
          
          ietf_hw_xml = self.get_xml_string_from_response(xml_data_str)          
          agg_base_xml = f"""<aggregated-o-ru xmlns="urn:o-ran:agg-base:1.0">
                            <aggregation>
                              <ru-instance>{session_details['hostname']}</ru-instance>
                              <ietf-hardware-model  xmlns="urn:o-ran:agg-ietf-hardware:1.0"> 
                                {ietf_hw_xml}
                            </ietf-hardware-model>
                            </aggregation>
                          </aggregated-o-ru>
                          """
                          
          data = ctx.parse_data_mem(agg_base_xml, "xml", parse_only=True)
          
          with self.netconf.connection.start_session("running") as sess:
            sess.edit_batch_ly(data)
            sess.apply_changes()
          
          data.free()

    def load_3gpp_data(self) -> None:
        logger.info(f"Loading 3GPP data...")

        _3gpp_managed_element_template = DictFactory.get_template("3gpp-managed-element")

        _3gpp_managed_element_template.update_key(["_3gpp-common-managed-element:ManagedElement", 0, "_3gpp-nr-nrm-gnbdufunction:GNBDUFunction", 0, "attributes", "gNBDUName"], get_hostname())

        with self.netconf.connection.start_session("running") as sess:                    
            sess.edit_batch(_3gpp_managed_element_template.data, "_3gpp-common-managed-element")
            sess.apply_changes()
            
    def get_json_object_from_xml(self, xml_string) -> dict | None:
      byte_array = bytearray(xml_string)
      byte_array = byte_array.replace(b'<data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">', b'')
      byte_array = byte_array.replace(b'</data>', b'')
      modified_byte_string = bytes(byte_array)              
      
      try:
        with self.netconf.connection.get_ly_ctx() as ctx:
          dnode = ctx.parse_data_mem(modified_byte_string, "xml", validate_present=True, no_state=True)
          j_str = dnode.print_mem("json", with_siblings=True)
          j_obj = json.loads(j_str)
          dnode.free()
          return j_obj
      except LibyangError as e:
        logger.error(f"Failed to get JSON object from XML: {xml_string}. Error: {e}")
                
    def get_xml_string_from_response(self, input: str) -> str:
        byte_array = bytearray(input)
        byte_array = byte_array.replace(b'<data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">', b'')
        byte_array = byte_array.replace(b'</data>', b'')
        modified_byte_array = bytes(byte_array)
        modified_byte_string = modified_byte_array.decode('utf-8')
                                                  
        return modified_byte_string
      
    def get_timestamp_from_xml_notification(self, input: str) -> str:
        byte_array = bytearray(input)
        byte_array = byte_array.replace(b'<data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">', b'')
        byte_array = byte_array.replace(b'</data>', b'')
        modified_byte_array = bytes(byte_array)
        modified_byte_string = modified_byte_array.decode('utf-8')
                                                  
        return modified_byte_string
 
        

class _3GPP_ManagedElementTemplate(BaseTemplate):
    """A dictionary template for _3gpp-common-managed-element:ManagedElement objects."""
    def create_dict(self):
        return {
                "_3gpp-common-managed-element:ManagedElement": [
                    {
                        "id": "ManagedElement-001",
                        "attributes": {
                            "priorityLabel": 1
                        },
                        "_3gpp-nr-nrm-gnbdufunction:GNBDUFunction": [                
                            {
                                "id": "GNBDUFunction-001",
                                "attributes": {
                                    "priorityLabel": 1,
                                    "gNBId": 1,
                                    "gNBIdLength": 24,
                                    "gNBDUId": 1,
                                    "gNBDUName": "to_be_replaced"
                                },
                                "_3gpp-nr-nrm-nrcelldu:NRCellDU": [
                                    {
                                        "id": "NRCellDU-001",
                                        "attributes": {
                                            "priorityLabel": 1,
                                            "cellLocalId": 1,
                                            "pLMNInfoList": [
                                                {
                                                    "mcc": "310",
                                                    "mnc": "410",
                                                    "sst": 1,
                                                    "sd": "ff:ff:ff"
                                                },
                                                {
                                                    "mcc": "310",
                                                    "mnc": "410",
                                                    "sst": 2,
                                                    "sd": "ff:ff:ff"
                                                },
                                                {
                                                    "mcc": "310",
                                                    "mnc": "410",
                                                    "sst": 3,
                                                    "sd": "ff:ff:ff"
                                                },
                                                {
                                                    "mcc": "310",
                                                    "mnc": "410",
                                                    "sst": 4,
                                                    "sd": "ff:ff:ff"
                                                },
                                                {
                                                    "mcc": "310",
                                                    "mnc": "410",
                                                    "sst": 5,
                                                    "sd": "ff:ff:ff"
                                                },
                                                {
                                                    "mcc": "310",
                                                    "mnc": "410",
                                                    "sst": 6,
                                                    "sd": "ff:ff:ff"
                                                }
                                            ],
                                            "nPNIdentityList": [
                                                {
                                                    "idx": 0,
                                                    "plmnid": [
                                                        {
                                                            "mcc": "310",
                                                            "mnc": "410"
                                                        }
                                                    ],
                                                    "cAGIdList": "cAGIdList1",
                                                    "nIDList": "nIDList1"
                                                }
                                            ],
                                            "nRPCI": 1,
                                            "arfcnDL": 1,
                                            "rimRSMonitoringStartTime": "2024-06-19T20:00:00Z",
                                            "rimRSMonitoringStopTime": "2024-06-19T21:00:00Z",
                                            "rimRSMonitoringWindowDuration": 1,
                                            "rimRSMonitoringWindowStartingOffset": 1,
                                            "rimRSMonitoringWindowPeriodicity": 1,
                                            "rimRSMonitoringOccasionInterval": 1,
                                            "rimRSMonitoringOccasionStartingOffset": 0,
                                            "ssbFrequency": 1,
                                            "ssbPeriodicity": 5,
                                            "ssbSubCarrierSpacing": 15,
                                            "ssbOffset": 1,
                                            "ssbDuration": 1,
                                            "nRSectorCarrierRef": [
                                                "CN=NR-Sector-Carrier-001"
                                            ],
                                            "victimSetRef": "CN=Victim-Set-001",
                                            "aggressorSetRef": "CN=Aggressor-Set-001"
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }                

class VesEventNotificationWrapper(VesMessage):
    def __init__(self, notif: dict, namespace: str = None, schema: str = None, notif_name: str = None, source_oru: str = None):
        super().__init__()

        self.data["event"]["stndDefinedFields"] = {
              #"schemaReference": "https://gerrit.o-ran-sc.org/r/gitweb?p=scp/oam/modeling.git;a=blob;f=data-model/yang/published/o-ran/ru-fh/o-ran-file-management.yang",
              #"data": {},
              "stndDefinedFieldsVersion": "1.0"
            }

        self.namespace = namespace
        self.domain = "stndDefined"
        self.priority = "Normal"
        self.notification = notif
        self.schema = schema
        self.notif_name = notif_name
        self.event_type = f"ORU-YANG/{self.schema}:{self.notif_name}"
        self.source_oru = source_oru                

    def update(self) -> None:
        super().update()
        
        ves = Ves()
        
        self.data["event"]["commonEventHeader"]["eventName"] = self.event_type
        self.data["event"]["commonEventHeader"]["eventId"] = f"{self.domain}-ORU-YANG-{ves.seq_id}"

        self.data["event"]["stndDefinedFields"]["data"] = self.notification
        self.data["event"]["stndDefinedFields"]["schemaReference"] = f"https://o-ran-sc.org/any-standard-defined-message.yaml"
        
        if self.source_oru is not None:
          self.data["event"]["commonEventHeader"]["sourceName"] = self.source_oru
          self.data["event"]["commonEventHeader"]["sourceId"] = self.source_oru
