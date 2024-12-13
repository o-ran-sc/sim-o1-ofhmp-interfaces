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

from core.dict_factory import DictFactory, BaseTemplate
from core.netconf import Datastore, Netconf
from util.crypto import CryptoUtils

logger = get_pynts_logger("feature-ietf-keystore-truststore")

class IetfKeystoreTruststoreFeature:
    def __init__(self) -> None:
        DictFactory.add_template("ietf-keystore", IetfKeystoreTemplate)
        DictFactory.add_template("ietf-truststore", IetfTruststoreTemplate)
        self.netconf: Netconf = Netconf()
        self.crypto: CryptoUtils = CryptoUtils()

    def configure(self) -> None:
        ietf_keystore_template = DictFactory.get_template("ietf-keystore")
        ietf_keystore_template.update_key(["ietf-keystore:keystore", "asymmetric-keys", "asymmetric-key", 0, "public-key"], self.crypto.get_public_key_ssh_format())
        ietf_keystore_template.update_key(["ietf-keystore:keystore", "asymmetric-keys", "asymmetric-key", 0, "cleartext-private-key"], self.crypto.get_private_key_base64_encoding_no_markers())
        ietf_keystore_template.update_key(["ietf-keystore:keystore", "asymmetric-keys", "asymmetric-key", 0, "certificates", "certificate", 0, "cert-data"], self.crypto.get_certificate_base64_encoding_no_markers(is_smo=False))                

        ietf_keystore_template.update_key(["ietf-keystore:keystore", "asymmetric-keys", "asymmetric-key", 1, "public-key"], self.crypto.get_public_key_base64_encoding_no_markers())
        ietf_keystore_template.update_key(["ietf-keystore:keystore", "asymmetric-keys", "asymmetric-key", 1, "cleartext-private-key"], self.crypto.get_private_key_base64_encoding_no_markers())
        ietf_keystore_template.update_key(["ietf-keystore:keystore", "asymmetric-keys", "asymmetric-key", 1, "certificates", "certificate", 0, "cert-data"], self.crypto.get_certificate_base64_encoding_no_markers(is_smo=False))            
        ietf_keystore_template.update_key(["ietf-keystore:keystore", "asymmetric-keys", "asymmetric-key", 1, "certificates", "certificate", 1, "cert-data"], self.crypto.get_certificate_base64_encoding_no_markers(is_smo=True))

        self.netconf.set_data(Datastore.RUNNING, "ietf-keystore", ietf_keystore_template.data, "merge")
        self.netconf.set_data(Datastore.OPERATIONAL, "ietf-keystore", ietf_keystore_template.data)

        ietf_truststore_template = DictFactory.get_template("ietf-truststore")
        ietf_truststore_template.update_key(["ietf-truststore:truststore", "certificate-bags", "certificate-bag", 0, "certificate", 0, "cert-data"], self.crypto.get_ca_certificate_base64_encoding_no_markers(is_smo=False))
        ietf_truststore_template.update_key(["ietf-truststore:truststore", "certificate-bags", "certificate-bag", 0, "certificate", 1, "cert-data"], self.crypto.get_ca_certificate_base64_encoding_no_markers(is_smo=True))

        self.netconf.set_data(Datastore.RUNNING, "ietf-truststore", ietf_truststore_template.data, "merge")
        self.netconf.set_data(Datastore.OPERATIONAL, "ietf-truststore", ietf_truststore_template.data)
        
        logger.info("succesfully configured ietf-keystore and ietf-truststore")


class IetfKeystoreTemplate(BaseTemplate):
    """A dictionary template for ietf-keystore objects."""
    def create_dict(self):
        return {
            "ietf-keystore:keystore":{
                "asymmetric-keys":{
                    "asymmetric-key":[
                        {
                            "name":"serverkey-ssh",
                            "public-key-format":"ietf-crypto-types:ssh-public-key-format",
                            "public-key":"PUB_KEY_TO_BE_REPLACED",
                            "private-key-format":"ietf-crypto-types:rsa-private-key-format",
                            "cleartext-private-key":"PRIV_KEY_TO_BE_REPLACED",
                            "certificates":{
                                "certificate":[
                                    {
                                        "name":"servercert-smo",
                                        "cert-data":"CERT_TO_BE_REPLACED"
                                    }
                                ]
                            }
                        },                        
                        {
                            "name":"serverkey-tls",
                            "public-key-format":"ietf-crypto-types:subject-public-key-info-format",
                            "public-key":"PUB_KEY_TO_BE_REPLACED",
                            "private-key-format":"ietf-crypto-types:rsa-private-key-format",
                            "cleartext-private-key":"PRIV_KEY_TO_BE_REPLACED",
                            "certificates":{
                                "certificate":[
                                    {
                                        "name":"servercert-odu",
                                        "cert-data":"CERT_TO_BE_REPLACED"
                                    },
                                    {
                                        "name":"servercert-smo",
                                        "cert-data":"CERT_TO_BE_REPLACED"
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }
        
    
class IetfTruststoreTemplate(BaseTemplate):
    """A dictionary template for ietf-truststore objects."""
    def create_dict(self):
        return {
            "ietf-truststore:truststore":{
                "certificate-bags":{
                    "certificate-bag":[
                        {
                            "name":"cacerts",
                            "description":"CA Certificates",
                            "certificate":[                                
                                {
                                    "name":"root_odu_cert",
                                    "cert-data":"TO_BE_REPLACED"
                                },
                                {
                                    "name":"root_smo_cert",
                                    "cert-data":"TO_BE_REPLACED"
                                }
                            ]
                        }
                    ]
                }
            }
        }
