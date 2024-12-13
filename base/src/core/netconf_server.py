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

from util.logging import get_pynts_logger
import requests

from core.config import Config
from core.netconf import Netconf, Datastore
from core.dict_factory import BaseTemplate, DictFactory
from util.crypto import CryptoUtils

logger = get_pynts_logger("netconf-server")

ODL_CALLHOME_ALLOW_DEVICES_URL="/rests/data/odl-netconf-callhome-server:netconf-callhome-server/allowed-devices/device="
ODL_ADD_TRUSTED_KEY_URL="/rests/operations/netconf-keystore:add-trusted-certificate"
HTTP_YANG_JSON_HEADERS = {
                'content-type': 'application/yang-data+json',
                'accept': 'application/yang-data+json'
            }
HTTP_JSON_HEADERS = {
                'content-type': 'application/json',
                'accept': 'application/json'
            }

"""
NetconfServer
Singleton
----
configures netconf server
"""
class NetconfServer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.debug("Created NetconfServer object")

            DictFactory.add_template("ssh-server-parameters", SshServerParametersTemplate)
            DictFactory.add_template("ssh-endpoint", SshEndpointTemplate)
            DictFactory.add_template("tls-server-parameters", TlsServerParametersTemplate)
            DictFactory.add_template("netconf-server-parameters", NetconfServerParametersTemplate)
            DictFactory.add_template("tls-endpoint", TlsEndpointTemplate)
            DictFactory.add_template("call-home-ssh-endpoint", CallhomeSshEndpointTemplate)
            DictFactory.add_template("call-home-tls-endpoint", CallhomeTlsEndpointTemplate)
            DictFactory.add_template("ietf-netconf-server", IetfNetconfServerTemplate)            

            cls._instance.set_config()

        return cls._instance

    def set_config(self) -> None:
        self.netconf: Netconf = Netconf()
        self.netconf.running.copy_config("startup", "ietf-netconf-server")  # reset the ietf-netconf-server module
        self.config: Config = Config()

        self.crypto: CryptoUtils = CryptoUtils()

        # for instance in range(1, self.config.endpoint_count):
        #     if self.config.ssh_listen_endpoint:
        #         self.ssh_endpoint_config(self.config.ssh_listen_port + instance)
        #     elif self.config.tls_listen_endpoint:
        #         self.tls_endpoint_config(self.config.tls_listen_port + instance)
        # try:
        #     self.send_odl_callhome_allow_ssh()
        # except Exception as e:
        #     logger.error(f"Could not send ODL CallHome allow SSH. Exception: {e}")
        # #self.ssh_callhome_endpoint_config()
        # try:
        #     self.send_odl_callhome_allow_tls()
        # except Exception as e:
        #     logger.error(f"Could not send ODL CallHome allow TLS. Exception: {e}")
        #self.tls_callhome_endpoint_config()
   

    def ssh_endpoint_config(self, port: int) -> None:
        ietf_netconf_server_template = DictFactory.get_template("ietf-netconf-server")
        ietf_netconf_server_template.delete_key(["ietf-netconf-server:netconf-server", "call-home"])

        ssh_endpoint_template = DictFactory.get_template("ssh-endpoint")
        ssh_endpoint_template.update_key(["name"], f"ssh-endpoint-{port}")
        ssh_endpoint_template.update_key(["ssh", "ssh-server-parameters"], DictFactory.get_template("ssh-server-parameters").data)
        ssh_endpoint_template.update_key(["ssh", "tcp-server-parameters", "local-port"], port)

        ietf_netconf_server_template.update_key(["ietf-netconf-server:netconf-server", "listen", "endpoints", "endpoint"], ssh_endpoint_template.data, append_to_list=True)
        self.netconf.set_data(Datastore.RUNNING, "ietf-netconf-server", ietf_netconf_server_template.data, "merge")

        return ssh_endpoint_template.data

    def tls_endpoint_config(self, port: int) -> None:
        ietf_netconf_server_template = DictFactory.get_template("ietf-netconf-server")
        ietf_netconf_server_template.delete_key(["ietf-netconf-server:netconf-server", "call-home"])

        tls_endpoint_template = DictFactory.get_template("tls-endpoint")

        tls_endpoint_template.update_key(["name"], f"tls-endpoint-{port}")
        tls_endpoint_template.update_key(["tls", "tls-server-parameters"], DictFactory.get_template("tls-server-parameters").data)
        tls_endpoint_template.update_key(["tls", "netconf-server-parameters"], self.get_netconf_server_parameters_updated_keys(self.crypto))
        tls_endpoint_template.update_key(["tls", "tcp-server-parameters", "local-port"], port)

        ietf_netconf_server_template.update_key(["ietf-netconf-server:netconf-server", "listen", "endpoints", "endpoint"], tls_endpoint_template.data, append_to_list=True)
        self.netconf.set_data(Datastore.RUNNING, "ietf-netconf-server", ietf_netconf_server_template.data, "merge")

    @staticmethod
    def get_netconf_server_parameters_updated_keys(crypto: CryptoUtils) -> dict:
        netconf_server_parameters_template = DictFactory.get_template("netconf-server-parameters")

        netconf_server_parameters_template.update_key(["client-identity-mappings", "cert-to-name", 0, "fingerprint"], crypto.get_certificate_fingerprint(crypto.ca_cert))

        return netconf_server_parameters_template.data

    # def ssh_callhome_endpoint_config(self) -> None:
    #     ietf_netconf_server_template = DictFactory.get_template("ietf-netconf-server")
    #     ietf_netconf_server_template.delete_key(["ietf-netconf-server:netconf-server", "listen"])

    #     callhome_template = DictFactory.get_template("call-home-ssh-endpoint")

    #     # callhome_template.update_key(["ssh", "ssh-server-parameters"], self.get_ssh_server_parameters_updated_keys(self.crypto))
    #     callhome_template.update_key(["ssh", "ssh-server-parameters"], DictFactory.get_template("ssh-server-parameters").data)
    #     callhome_template.update_key(["ssh", "tcp-client-parameters", "remote-address"], self.config.sdnr_callhome_ip)
    #     callhome_template.update_key(["ssh", "tcp-client-parameters", "remote-port"], self.config.sdnr_callhome_ssh_port)

    #     ietf_netconf_server_template.update_key(["ietf-netconf-server:netconf-server", "call-home", "netconf-client", 0, "endpoints", "endpoint"], callhome_template.data, append_to_list=True)
    #     self.netconf.set_data(Datastore.RUNNING, "ietf-netconf-server", ietf_netconf_server_template.data, "merge")

    # def tls_callhome_endpoint_config(self) -> None:
    #     ietf_netconf_server_template = DictFactory.get_template("ietf-netconf-server")
    #     ietf_netconf_server_template.delete_key(["ietf-netconf-server:netconf-server", "listen"])

    #     callhome_template = DictFactory.get_template("call-home-tls-endpoint")

    #     callhome_template.update_key(["tls", "tls-server-parameters"], DictFactory.get_template("tls-server-parameters").data)
    #     callhome_template.update_key(["tls", "netconf-server-parameters"], self.get_netconf_server_parameters_updated_keys(self.crypto))

    #     callhome_template.update_key(["tls", "tcp-client-parameters", "remote-address"], self.config.sdnr_callhome_ip)
    #     callhome_template.update_key(["tls", "tcp-client-parameters", "remote-port"], self.config.sdnr_callhome_tls_port)

    #     ietf_netconf_server_template.update_key(["ietf-netconf-server:netconf-server", "call-home", "netconf-client", 0, "endpoints", "endpoint"], callhome_template.data, append_to_list=True)
    #     self.netconf.set_data(Datastore.RUNNING, "ietf-netconf-server", ietf_netconf_server_template.data, "merge")

    def send_odl_callhome_allow_ssh(self) -> None:
        allow_ssh_template = DictFactory.get_template("odl-netconf-callhome-server-ssh")

        allow_ssh_template.update_key(["odl-netconf-callhome-server:device", "unique-id"], self.config.hostname)
        allow_ssh_template.update_key(["odl-netconf-callhome-server:device", "ssh-client-params", "credentials", "username"], self.config.netconf_username)
        allow_ssh_template.update_key(["odl-netconf-callhome-server:device", "ssh-client-params", "credentials", "passwords"], self.config.netconf_password, append_to_list=True)
        allow_ssh_template.update_key(["odl-netconf-callhome-server:device", "ssh-client-params", "host-key"], self.crypto.get_public_key_ssh_format())

        url = self.config.sdnr_restconf_url + ODL_CALLHOME_ALLOW_DEVICES_URL + self.config.hostname

        logger.debug(f"sending HTTP PUT to {url} with payload {allow_ssh_template.data}")
        response = requests.put(url, auth=(self.config.sdnr_username, self.config.sdnr_password), json=allow_ssh_template.data, headers=HTTP_YANG_JSON_HEADERS)
        if response.status_code >= 200 and response.status_code < 300:
          logger.debug(f"HTTP response to {url} succeded with code {response.status_code}")
        else:
          logger.error(f"HTTP PUT request failed to {url} with payload {allow_ssh_template.data} with status_code={response.status_code}")

    def send_odl_callhome_allow_tls(self) -> None:
        odl_trusted_cert_template = DictFactory.get_template("odl-netconf-callhome-trusted-cert")

        odl_trusted_cert_template.update_key(["input", "trusted-certificate", 0, "name"], self.config.hostname)
        odl_trusted_cert_template.update_key(["input", "trusted-certificate", 0, "certificate"], self.crypto.get_certificate_base64_encoding_no_markers())

        url = self.config.sdnr_restconf_url + ODL_ADD_TRUSTED_KEY_URL
        logger.debug(f"sending HTTP POST to {url} with payload {odl_trusted_cert_template.data}")
        response = requests.post(url, auth=(self.config.sdnr_username, self.config.sdnr_password), json=odl_trusted_cert_template.data, headers=HTTP_JSON_HEADERS)
        if response.status_code >= 200 and response.status_code < 300:
          logger.debug(f"HTTP response to {url} succeded with code {response.status_code}")
        else:
          logger.error(f"HTTP POST request failed to {url} with payload {odl_trusted_cert_template.data} with status_code={response.status_code}")

        allow_tls_template = DictFactory.get_template("odl-netconf-callhome-server-tls")

        allow_tls_template.update_key(["odl-netconf-callhome-server:device", "unique-id"], self.config.hostname)
        allow_tls_template.update_key(["odl-netconf-callhome-server:device", "tls-client-params", "certificate-id"], self.config.hostname)

        url = self.config.sdnr_restconf_url + ODL_CALLHOME_ALLOW_DEVICES_URL + self.config.hostname
        logger.debug(f"sending HTTP PUT to {url} with payload {allow_tls_template.data}")
        response = requests.put(url, auth=(self.config.sdnr_username, self.config.sdnr_password), json=allow_tls_template.data, headers=HTTP_YANG_JSON_HEADERS)
        if response.status_code >= 200 and response.status_code < 300:
          logger.debug(f"HTTP response to {url} succeded with code {response.status_code}")
        else:
            logger.error(f"HTTP PUT request failed to {url} with payload {allow_tls_template.data} with status_code={response.status_code}")

class SshServerParametersTemplate(BaseTemplate):
    """A dictionary template for ssh-server-parameters objects."""
    def create_dict(self):
        config = Config()
        return {
              "server-identity": {
                "host-key": [
                  {
                    "name": "melacon-key",
                    "public-key": {
                      "central-keystore-reference": "serverkey-ssh"
                    }
                  }
                ]
              },
              "client-authentication": {
                "users": {
                  "user": [
                    {
                      "name": config.netconf_username,
                      "password": "$0$" + config.netconf_password,
                      # "public-keys": {
                      # "inline-definition": {
                      #     "public-key": [{
                      #       "name": "test",
                      #       "public-key-format": "ietf-crypto-types:ssh-public-key-format",
                      #       "public-key": "AAAAB3NzaC1yc2EAAAADAQABAAACAQCegtvGWzi2fA5Y/9W1lT2l+JlPtPxDJX/fNVrssJBAGErdpSquEV85qDRCmY5qWbQ8cHv9DgJ3/4OI8XmWZkwGM+N9zXnYlc5VQqCTM1wwridroJPjkIA6RRtW+SO06VyOtdN1pikCKvpPKt4LL59mQUREsf5+9w1zg5cc2bBsCFzXAiYtBpXO3d6ZyDKHPcND92ns+fpQ4EV3GydVJYH6Sqv/Aix0BcVB6nK4gfl57yyWJR808ExGXR/ZoI+ZecaBYyuOAj2mv5Yf6U+roKEYj4JVVDh/+Az3lQpl99WxXi4ykLNf3UAZX9fLOqfiUzCWT8ow3zRYv9iwKCYy8c4nRDDpASjtCJqS/RfoCx2LAG+nynBT+qa2yCUT5dDI55GK/bOhoGtd5gMuC9grVD3/xe2/lgS2oAxci2bx4UIhvrUP8SrgNEc8+99NRvygdrvaRUNJ49OqMI1LgVhK2Aqq6hc6KyRYeal9K98AVJPXBocfnDsDw4d/uKBWI3fMJAf7qoIzhew03MxtetK1J4GhmD/TN2PrwSrFeO9iBUuaTcb6n/X9Gj0zQsLTZBNZMs+FBjQTr3fjA5WItAzoA+ZpAQtICg6y2KwUZwX3xaAHv4lHiO5nygAN453W9ksX8DBBppUWh6Lt3/TY/lYUV2rXMPhCwWMHpMzuP+q179iPaQ=="
                      #     }]
                      # }
                    }
                  ]
                }
              }
            }


class SshEndpointTemplate(BaseTemplate):
    """A dictionary template for ssh-endpoint objects."""
    def create_dict(self):
        return {
          "name": "ssh-password-auth-endpt",
          "ssh": {
            "tcp-server-parameters": {
              "local-address": "0.0.0.0",
              "local-port": 830
            },
            "ssh-server-parameters": {}
          }
        }


class TlsServerParametersTemplate(BaseTemplate):
    """A dictionary template for tls-server-parameters objects."""
    def create_dict(self):
        return {
              "server-identity": {
                "certificate": {
                    "central-keystore-reference": {
                        "asymmetric-key": "serverkey-tls",
                        "certificate": "servercert"
                    }
                }
              },
              "client-authentication": {
                "ca-certs": {
                    "central-truststore-reference": "cacerts"
                }
              }
            }

class NetconfServerParametersTemplate(BaseTemplate):
    """A dictionary template for netconf-server-parameters objects."""
    def create_dict(self):
        config = Config()
        return {
                  "client-identity-mappings": {
                      "cert-to-name": [
                          {
                              "id": 1,
                              "fingerprint": "FINGERPRINT_TO_BE_REPLACED",
                              "map-type": "ietf-x509-cert-to-name:specified",
                              "name": config.netconf_username,
                          }
                      ]
                  }
              }

class TlsEndpointTemplate(BaseTemplate):
    """A dictionary template for tls-endpoint objects."""
    def create_dict(self):
        return {
          "name": "tls-auth-endpt",
          "tls": {
            "tcp-server-parameters": {
              "local-address": "0.0.0.0",
              "local-port": 6513
            },
            "tls-server-parameters": {},
            "netconf-server-parameters": {}
          }
        }

class CallhomeSshEndpointTemplate(BaseTemplate):
    """A dictionary template for call-home-ssh-endpoint objects."""
    def create_dict(self):
        return {
            "name": "default-ssh-callhome",
            "ssh": {
                "tcp-client-parameters": {
                "remote-address": "TO_BE_OVERWRITTEN",
                "remote-port": "TO_BE_OVERWRITTEN"
                },
                "ssh-server-parameters": {}
            }
        }


class CallhomeTlsEndpointTemplate(BaseTemplate):
    """A dictionary template for call-home-tls-endpoint objects."""
    def create_dict(self):
        return {
          "name": "tls-auth-endpt",
          "tls": {
            "tcp-client-parameters": {
              "remote-address": "TO_BE_OVERWRITTEN",
              "remote-port": "TO_BE_OVERWRITTEN"
            },
            "tls-server-parameters": {},
            "netconf-server-parameters": {}
          }
        }

class IetfNetconfServerTemplate(BaseTemplate):
    """A dictionary template for ietf-netconf-server objects."""
    def create_dict(self):
        return {
                "ietf-netconf-server:netconf-server": {
                    "listen": {
                    "endpoints": {
                        "endpoint": []
                    }
                    },
                    "call-home": {
                        "netconf-client": [{
                            "name": "default-client",
                            "endpoints": {
                                "endpoint": []
                            },
                            "connection-type": {
                                "persistent": {

                                }
                            }
                        }]
                    }
                }
            }


