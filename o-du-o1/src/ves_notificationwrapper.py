import threading
from util.logging import get_pynts_logger

from core.config import Config
from core.netconf import Netconf
from core.ves import Ves, VesMessage
from util.threading import sa_sleep

logger = get_pynts_logger("feature-ves-pnfregistration")

SEND_TIMEOUT = 10  # seconds

class VesPnfRegistrationFeature:
    def __init__(self) -> None:
        self.ves: Ves = Ves()
        self.listen_endpoints: list = []

    def start(self) -> None:
        self.netconf = Netconf()

        self.get_listen_connections()
        self.start_pnf_registration_thread()                
      
    def start_pnf_registration_thread(self):
      logger.debug(f"Starting pnfRegistration thread...")
      request_thread = threading.Thread(target=self.send_pnf_registrations_in_background)
      request_thread.daemon = True  # Set as daemon so it exits when the main program exits
      request_thread.start()
  
    def send_pnf_registrations_in_background(self):
      logger.debug(f"Started pnfRegistration thread...")
      success = {i: False for i in range(len(self.listen_endpoints))}
      append_port = bool(len(self.listen_endpoints) > 1)      
      
      while not all(success.values()):        
        for i, instance in enumerate(self.listen_endpoints):
          if not success[i]:
            try:
              if instance['isTls']:
                pnf_registration_tls: VesMessage = VesPnfRegistrationTLS(instance['name'], instance['port'], append_port)
                result = self.ves.execute(pnf_registration_tls)
                if result is True:
                  success[i] = True
              elif not instance['isTls']:
                pnf_registration_ssh: VesMessage = VesPnfRegistrationSSH(instance['port'], instance['nc_user'], instance['nc_pass'], append_port)
                result = self.ves.execute(pnf_registration_ssh)
                if result is True:
                  success[i] = True
            except Exception as e:
              logger.error(f"Could not send vesPnfRegistration. Error: {e}")               
            
        # Wait 10 seconds before retrying any failed requests
        if not all(success.values()):    
            remaining_requests = len([key for key, value in success.items() if not value])
            logger.debug(f"Still need to send {remaining_requests} pnfRegistration messages...")
            sa_sleep(SEND_TIMEOUT)
            
        logger.info(f"VES pnfRegistration finished successfully!")                  
       
    def get_listen_connections(self):
      data = self.netconf.running.get_data("/ietf-netconf-server:netconf-server/listen/endpoints/endpoint")
      
      endpoints = data
      try:
        for key in ['netconf-server', 'listen', 'endpoints', 'endpoint']:
          endpoints = endpoints[key]
          
        if isinstance(endpoints, list):
          for endpoint in endpoints:
            if 'tls' in endpoint:
              try:
                port = endpoint['tls']['tcp-server-parameters']['local-port']
                name = endpoint['name']
                self.listen_endpoints.append({'name': name, 'port': port, 'isTls': True})
                logger.debug(f"Found TLS connection with port {port} and name {name}")
              except KeyError as e:
                logger.error(f"Could not find port in object {endpoint}. Error: {e}")
            elif 'ssh' in endpoint:
              try:
                port = endpoint['ssh']['tcp-server-parameters']['local-port']
                name = endpoint['name']
                users = endpoint['ssh']['ssh-server-parameters']['client-authentication']['users']['user']
                for user in users:
                  netconf_username = user['name']
                  netconf_password = user['password']
                  netconf_password = netconf_password[3:]  # prune the $0$ string that is prepended to the password
                                
                self.listen_endpoints.append({'name': name, 'port': port, 'isTls': False, 'nc_user': netconf_username, 'nc_pass': netconf_password})
                logger.debug(f"Found SSH connection with port {port} and name {name} and username {netconf_username} and pass {netconf_password}")
              except KeyError as e:
                logger.error(f"Could not find key in object {endpoint}. Error: {e}")
      except KeyError as e:
          logger.error(f"Keys not found in JSON object {data}. Error: {e}")
      except TypeError as e:
          logger.error(f"List not at the expected level in {data}. Error: {e}")
        

      


