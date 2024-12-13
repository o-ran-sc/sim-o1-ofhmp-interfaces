# /*************************************************************************
# *
# * Copyright 2024 highstreet technologies and others
# *
# * Licensed under the Apache License, Version 2.0 (the "License");
# * you may not use this file except in compliance with the License.
# * You may obtain a copy of the License at
# *
# *     http://www.apache.org/licenses/LICENSE-2.0
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.
# ***************************************************************************/

import requests
import threading

from core.dict_factory import DictFactory, BaseTemplate
from core.extension import Extension
from core.config import Config
from core.netconf import Netconf, Datastore
from util.crypto import CryptoUtils
from util.threading import sa_sleep
from util.logging import get_pynts_logger

logger = get_pynts_logger("o-ru-mplane")

ODL_CALLHOME_ALLOW_DEVICES_URL="/rests/data/odl-netconf-callhome-server:netconf-callhome-server/allowed-devices/device="
ODL_ADD_TRUSTED_CERT_URL="/rests/operations/netconf-keystore:add-trusted-certificate"
ODL_RM_TRUSTED_CERT_URL="/rests/operations/netconf-keystore:remove-trusted-certificate"
HTTP_YANG_JSON_HEADERS = {
                'content-type': 'application/yang-data+json',
                'accept': 'application/yang-data+json'
            }
HTTP_JSON_HEADERS = {
                'content-type': 'application/json',
                'accept': 'application/json'
            }

class Main(Extension):
    def init(self) -> None:
        self.netconf = Netconf()
        self.config = Config()
        self.crypto_util = CryptoUtils()
        
        DictFactory.add_template("o-ran-certificates", OranCertificatesTemplate)
        DictFactory.add_template("odl-netconf-callhome-server-ssh", OdlNetconfCallhomeServerSshTemplate)
        DictFactory.add_template("odl-netconf-callhome-server-tls", OdlNetconfCallhomeServerTlsTemplate)
        DictFactory.add_template("odl-netconf-callhome-trusted-cert", OdlNetconfCallhomeTrustedCertificateTemplate)
        DictFactory.add_template("odl-netconf-callhome-trusted-cert-remove", OdlNetconfCallhomeRemoveTrustedCertificateTemplate)
        

    def startup(self) -> None:
        self.update_o_ran_certificates()
        self.start_odl_allow_thread()
        logger.info("o-ru-mplane extension loaded")

    def update_o_ran_certificates(self) -> None:
        o_ran_certificates_template = DictFactory.get_template("o-ran-certificates")
        o_ran_certificates_template.update_key(["o-ran-certificates", "certificate-parameters", "cert-maps", "cert-to-name", 0, "fingerprint"], self.crypto_util.get_certificate_fingerprint(self.crypto_util.root_odu_ca_cert))

        self.netconf.set_data(Datastore.RUNNING, "", o_ran_certificates_template.data)
        self.netconf.set_data(Datastore.OPERATIONAL, "", o_ran_certificates_template.data)
        

    def start_odl_allow_thread(self):
      request_thread = threading.Thread(target=self.send_odl_callhome_allow_tls)
      request_thread.daemon = True  # Set as daemon so it exits when the main program exits
      request_thread.start()
    
    def send_odl_callhome_allow_tls(self) -> None:
        odl_trusted_cert_template = DictFactory.get_template("odl-netconf-callhome-trusted-cert")
        odl_trusted_cert_template.update_key(["input", "trusted-certificate", 0, "name"], self.config.hostname)
        odl_trusted_cert_template.update_key(["input", "trusted-certificate", 0, "certificate"], self.crypto_util.get_certificate_base64_encoding_no_markers(is_smo=True))
        
        odl_trusted_cert_template_remove = DictFactory.get_template("odl-netconf-callhome-trusted-cert-remove")
        odl_trusted_cert_template_remove.update_key(["input","name", 0], self.config.hostname)

        allow_tls_template = DictFactory.get_template("odl-netconf-callhome-server-tls")
        allow_tls_template.update_key(["odl-netconf-callhome-server:device", "unique-id"], self.config.hostname)
        allow_tls_template.update_key(["odl-netconf-callhome-server:device", "tls-client-params", "certificate-id"], self.config.hostname)

        success1 = False  # Flag to track the success of the first request
        success2 = False  # Flag to track the success of the second request
        while not (success1 and success2):
          if not success1:
            try:              
              # Trying to delete first the cert
              url = self.config.sdnr_restconf_url + ODL_RM_TRUSTED_CERT_URL
              payload = odl_trusted_cert_template_remove.data
              logger.debug(f"sending HTTP POST to {url} with payload {payload}")
              response = requests.post(url, auth=(self.config.sdnr_username, self.config.sdnr_password), json=payload, headers=HTTP_YANG_JSON_HEADERS, verify=False)
              if response.status_code >= 200 and response.status_code < 300:
                logger.debug(f"HTTP response to {url} succeded with code {response.status_code}")
              else:
                logger.error(f"HTTP POST request failed to {url} with payload {payload} with status_code={response.status_code}")             
            except requests.RequestException as e:
                logger.error(f"Error occurred in first request: {e}. Retrying in 10 seconds...")
            
            try:                                          
              url = self.config.sdnr_restconf_url + ODL_ADD_TRUSTED_CERT_URL
              payload = odl_trusted_cert_template.data
              logger.debug(f"sending HTTP POST to {url} with payload {payload}")
              response = requests.post(url, auth=(self.config.sdnr_username, self.config.sdnr_password), json=payload, headers=HTTP_YANG_JSON_HEADERS, verify=False)
              if response.status_code >= 200 and response.status_code < 300:
                logger.debug(f"HTTP response to {url} succeded with code {response.status_code}")
                success1 = True
              else:
                logger.error(f"HTTP POST request failed to {url} with payload {payload} with status_code={response.status_code}")
            except requests.RequestException as e:
                logger.error(f"Error occurred in first request: {e}. Retrying in 10 seconds...")

          if not success2:
            try:              
              url = self.config.sdnr_restconf_url + ODL_CALLHOME_ALLOW_DEVICES_URL + self.config.hostname
              payload = allow_tls_template.data
              logger.debug(f"sending HTTP PUT to {url} with payload {payload}")
              response = requests.put(url, auth=(self.config.sdnr_username, self.config.sdnr_password), json=payload, headers=HTTP_YANG_JSON_HEADERS, verify=False)
              if response.status_code >= 200 and response.status_code < 300:
                logger.debug(f"HTTP response to {url} succeded with code {response.status_code}")
                success2 = True
              else:
                  logger.error(f"HTTP PUT request failed to {url} with payload {payload} with status_code={response.status_code}")
            except requests.RequestException as e:
                logger.error(f"Error occurred in second request: {e}. Retrying in 10 seconds...")
          
          # Wait 10 seconds before retrying
          if not (success1 and success2):
              sa_sleep(10)


class OranCertificatesTemplate(BaseTemplate):
    """A dictionary template for netconf-server-parameters objects."""
    def create_dict(self):
        config = Config()
        return { "o-ran-certificates": {
                    "certificate-parameters": {
                        "cert-maps": {
                            "cert-to-name": [
                                {
                                    "id": 1,
                                    "fingerprint": "FINGERPRINT_TO_BE_REPLACED",
                                    "map-type": "ietf-x509-cert-to-name:san-rfc822-name"
                                }
                            ]
                        }
                    }
                }
              }

class OdlNetconfCallhomeServerSshTemplate(BaseTemplate):
    """A dictionary template for odl-netconf-callhome-server-ssh objects."""
    def create_dict(self):
        return {
                    "odl-netconf-callhome-server:device": {
                        "unique-id": "TO_BE_REPLACED_HOSTNAME",
                        "ssh-client-params": {
                            "credentials": {
                                "username": "TO_BE_REPLACED_USERNAME",
                                "passwords": [ ]
                            },
                            "host-key": "TO_BE_REPLACED_SSHKEY"
                        }
                    }
                }

class OdlNetconfCallhomeServerTlsTemplate(BaseTemplate):
    """A dictionary template for odl-netconf-callhome-server-tls objects."""
    def create_dict(self):
        return {
                    "odl-netconf-callhome-server:device": {
                        "unique-id": "TO_BE_REPLACED_HOSTNAME",
                        "tls-client-params": {
                            "key-id": "ODL_private_key_0",  # hardcoded ODL key here
                            "certificate-id": "TO_BE_REPLACED_HOSTNAME"
                        }
                    }
                }


class OdlNetconfCallhomeTrustedCertificateTemplate(BaseTemplate):
    """A dictionary template for odl-netconf-callhome-trusted-cert objects."""
    def create_dict(self):
        return {
                "input": {
                    "trusted-certificate": [
                    {
                        "name": "TO_BE_REPLACED_HOSTNAME",
                        "certificate": "TO_BE_REPLACED_SERVER_CERT"
                    }
                    ]
                }
            }

class OdlNetconfCallhomeRemoveTrustedCertificateTemplate(BaseTemplate):
    """A dictionary template for removing odl-netconf-callhome-trusted-cert objects."""
    def create_dict(self):
        return {
                "input": {                    
                        "name": ["TO_BE_REPLACED_HOSTNAME"]
                }
            }
