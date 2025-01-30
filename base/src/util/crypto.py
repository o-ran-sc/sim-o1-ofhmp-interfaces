# /*************************************************************************
# *
# * Copyright 2025 highstreet technologies and others
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

import datetime
from util.logging import get_pynts_logger
from util.docker import get_hostname, get_container_ip
import ipaddress
import os

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.x509.oid import NameOID

logger = get_pynts_logger("crypto")

CERTIFICATE_VALIDITY_DAYS = 3650

PRIVATE_KEY_PATH="/home/oranuser/.ssh/private_key.pem"
PUBLIC_KEY_PATH="/home/oranuser/.ssh/public_key.pem"
ODU_CERTIFICATE_PATH="/home/oranuser/.ssh/odu_certificate.pem"
SMO_CERTIFICATE_PATH="/home/oranuser/.ssh/smo_certificate.pem"

# CA_PRIVATE_KEY_PATH="/home/oranuser/.ssh/ca.key"
# CA_CERT_PATH="/home/oranuser/.ssh/ca.pem"

ROOT_ODU_CA_PRIVATE_KEY_PATH="/home/oranuser/.ssh/ODU_rootCA.key"
ROOT_ODU_CA_CERT_PATH="/home/oranuser/.ssh/ODU_rootCA.crt"

ROOT_SMO_CA_PRIVATE_KEY_PATH="/home/oranuser/.ssh/SMO_rootCA.key"
ROOT_SMO_CA_CERT_PATH="/home/oranuser/.ssh/SMO_rootCA.crt"

"""
CryptoUtils
Singleton
----
handles keys and certificates
"""
class CryptoUtils():
    _instance = None

    private_key: bytes
    private_key_rsa: bytes
    public_key_ssh: bytes
    public_key_pem: bytes
    odu_certificate: bytes
    smo_certificate: bytes

    root_odu_ca_private_key: bytes
    root_odu_ca_cert: bytes
    root_odu_ca_cert_decoded: str
    
    root_smo_ca_private_key: bytes
    root_smo_ca_cert: bytes
    root_smo_ca_cert_decoded: str
    
    # ca_private_key: bytes
    # ca_cert: bytes
    # ca_cert_decoded: str

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.debug("CryptoUtils NetconfServer object")
            cls._instance.initialize()

        return cls._instance

    def initialize(self) -> None:
        self.load_ca_keys_and_certs()
        self.generate_or_load_keys()
        self.generate_certificate(self.private_key_rsa, is_smo=False)
        self.generate_certificate(self.private_key_rsa, is_smo=True)
        with open(ODU_CERTIFICATE_PATH, 'wb') as f:
            f.write(self.odu_certificate)
        with open(SMO_CERTIFICATE_PATH, 'wb') as f:
            f.write(self.smo_certificate)

    def load_ca_keys_and_certs(self) -> None:
        # Load the CA's private key
        # with open(CA_PRIVATE_KEY_PATH, "rb") as key_file:
        #     self.ca_private_key = crypto_serialization.load_pem_private_key(
        #         key_file.read(),
        #         password=None,  # or your password here
        #         backend=crypto_default_backend()
        #     )

        # # Load the CA's certificate
        # with open(CA_CERT_PATH, "rb") as cert_file:
        #     self.ca_cert = x509.load_pem_x509_certificate(
        #         cert_file.read(),
        #         crypto_default_backend()
        #     )
        #     self.ca_cert_decoded = self.ca_cert.public_bytes(crypto_serialization.Encoding.PEM)
            
        # Load the Root ODU CA's private key
        with open(ROOT_ODU_CA_PRIVATE_KEY_PATH, "rb") as key_file:
            self.root_odu_ca_private_key = crypto_serialization.load_pem_private_key(
                key_file.read(),
                password=None,  # or your password here
                backend=crypto_default_backend()
            )

        # Load the Root ODU CA's certificate
        with open(ROOT_ODU_CA_CERT_PATH, "rb") as cert_file:
            self.root_odu_ca_cert = x509.load_pem_x509_certificate(
                cert_file.read(),
                crypto_default_backend()
            )
            self.root_odu_ca_cert_decoded = self.root_odu_ca_cert.public_bytes(crypto_serialization.Encoding.PEM)
            
        # Load the Root SMO CA's private key
        with open(ROOT_SMO_CA_PRIVATE_KEY_PATH, "rb") as key_file:
            self.root_smo_ca_private_key = crypto_serialization.load_pem_private_key(
                key_file.read(),
                password=None,  # or your password here
                backend=crypto_default_backend()
            )

        # Load the Root SMO CA's certificate
        with open(ROOT_SMO_CA_CERT_PATH, "rb") as cert_file:
            self.root_smo_ca_cert = x509.load_pem_x509_certificate(
                cert_file.read(),
                crypto_default_backend()
            )
            self.root_smo_ca_cert_decoded = self.root_smo_ca_cert.public_bytes(crypto_serialization.Encoding.PEM)

    def generate_or_load_keys(self) -> None:

        if os.path.exists(PRIVATE_KEY_PATH) and os.path.exists(PUBLIC_KEY_PATH):
            logger.info("Loading keys and certs, as they are already existing...")
            with open(PRIVATE_KEY_PATH, 'rb') as f:
                private_key = crypto_serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=crypto_default_backend()
                )
                
                self.private_key_rsa = private_key
                
                self.private_key = private_key.private_bytes(
                    crypto_serialization.Encoding.PEM,
                    crypto_serialization.PrivateFormat.PKCS8,
                    crypto_serialization.NoEncryption()
                )

            with open(PUBLIC_KEY_PATH, 'rb') as f:
                public_key = crypto_serialization.load_pem_public_key(
                    f.read(),
                    backend=crypto_default_backend()
                )
                
                self.public_key_pem = public_key.public_bytes(
                  encoding=crypto_serialization.Encoding.PEM,
                  format=crypto_serialization.PublicFormat.SubjectPublicKeyInfo
                )
                
                self.public_key_ssh = public_key.public_bytes(
                  encoding=crypto_serialization.Encoding.OpenSSH,
                  format=crypto_serialization.PublicFormat.OpenSSH
                )

            # with open(SMO_CERTIFICATE_PATH if is_smo else ODU_CERTIFICATE_PATH, 'rb') as f:
            #     certificate = x509.load_pem_x509_certificate(f.read(), crypto_default_backend())
            #     if is_smo:
            #       self.smo_certificate = certificate.public_bytes(crypto_serialization.Encoding.PEM)
            #     else:
            #       self.odu_certificate = certificate.public_bytes(crypto_serialization.Encoding.PEM)
        else:
            logger.info("Generating new keys and certs, as they are not existing...")
            key = rsa.generate_private_key(backend=crypto_default_backend(), public_exponent=65537, key_size=2048)
            
            self.private_key_rsa = key

            self.private_key = key.private_bytes(
                crypto_serialization.Encoding.PEM,
                crypto_serialization.PrivateFormat.PKCS8,
                crypto_serialization.NoEncryption()
            )
            with open(PRIVATE_KEY_PATH, 'wb') as f:
                f.write(self.private_key)

            self.public_key_pem = key.public_key().public_bytes(crypto_serialization.Encoding.PEM, crypto_serialization.PublicFormat.SubjectPublicKeyInfo)
            with open(PUBLIC_KEY_PATH, 'wb') as f:
                f.write(self.public_key_pem)

            self.public_key_ssh = key.public_key().public_bytes(crypto_serialization.Encoding.OpenSSH, crypto_serialization.PublicFormat.OpenSSH)            

    def generate_certificate(self, key: bytes, is_smo: bool = False) -> None:
        csr = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
            # Provide various details about who we are.
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"NJ"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"New Jersey"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Melacon"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u"5G"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"SMO") if is_smo else x509.NameAttribute(NameOID.COMMON_NAME, u"hybridOdu"),
        ])).sign(key, hashes.SHA256(), crypto_default_backend())


        # Generate the certificate
        one_day = datetime.timedelta(1, 0, 0)
        certificate = x509.CertificateBuilder().subject_name(
            csr.subject
        ).issuer_name(
            self.root_smo_ca_cert.subject if is_smo else self.root_odu_ca_cert.subject
        ).public_key(
            csr.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.today() - one_day
        ).not_valid_after(
            # Our certificate will be valid for CERTIFICATE_VALIDITY_DAYS days
            datetime.datetime.today() + datetime.timedelta(days=CERTIFICATE_VALIDITY_DAYS)
        ).add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(self.root_smo_ca_private_key.public_key() if is_smo else self.root_odu_ca_private_key.public_key()),
            critical=False,
        ).add_extension(
            x509.SubjectKeyIdentifier.from_public_key(csr.public_key()),
            critical=False,
        ).add_extension(
            x509.SubjectAlternativeName([
                # Describe what sites we want this certificate for.
                x509.RFC822Name("client.smo" if is_smo else "client.hybridOdu"),
                x509.RFC822Name(("client.smo@"+get_hostname()) if is_smo else ("client.hybridOdu@"+get_hostname())),
                x509.DNSName("client.smo" if is_smo else "client.hybridOdu"),
                x509.DNSName(("client.smo@"+get_hostname()) if is_smo else ("client.hybridOdu@"+get_hostname())),
                x509.IPAddress(ipaddress.ip_address(get_container_ip()))
            ]),
            critical=False,
        ).sign(self.root_smo_ca_private_key if is_smo else self.root_odu_ca_private_key, hashes.SHA256(), crypto_default_backend())

        # Serialize the certificate to PEM
        if is_smo:
          self.smo_certificate = certificate.public_bytes(crypto_serialization.Encoding.PEM)
        else:
          self.odu_certificate = certificate.public_bytes(crypto_serialization.Encoding.PEM)

    def get_public_key_ssh_format(self) -> str:
        ''' Method returning just the actual data of a SSH key, removing the extra ssh-rsa or whatever encoding algorithm
        '''
        return self.public_key_ssh.decode("utf-8").split(" ")[1]

    def get_private_key_base64_encoding_no_markers(self) -> str:
        ''' Method for getting just the base64 encoding of the private key, removing the ---- BEGIN... and ---- END lines.
        '''
        crypto_string = self.private_key.decode("utf-8")
        return "\n".join(crypto_string.split("\n")[1:-2])

    def get_public_key_base64_encoding_no_markers(self) -> str:
        ''' Method for getting just the base64 encoding of the private key, removing the ---- BEGIN... and ---- END lines.
        '''
        crypto_string = self.public_key_pem.decode("utf-8")
        return "\n".join(crypto_string.split("\n")[1:-2])

    def get_certificate_base64_encoding_no_markers(self, is_smo = False) -> str:
        ''' Method for getting just the base64 encoding of the private key, removing the ---- BEGIN... and ---- END lines.
        '''
        crypto_string = self.smo_certificate.decode("utf-8") if is_smo else self.odu_certificate.decode("utf-8")
        return "\n".join(crypto_string.split("\n")[1:-2])

    # def get_ca_certificate_base64_encoding_no_markers(self) -> str:
    #     ''' Method for getting just the base64 encoding of the private key, removing the ---- BEGIN... and ---- END lines.
    #     '''
    #     crypto_string = self.ca_cert_decoded.decode("utf-8")
    #     return "\n".join(crypto_string.split("\n")[1:-2])
      
    def get_ca_certificate_base64_encoding_no_markers(self, is_smo) -> str:
        ''' Method for getting just the base64 encoding of the private key, removing the ---- BEGIN... and ---- END lines.
        '''
        crypto_string = self.root_smo_ca_cert_decoded.decode("utf-8") if is_smo else self.root_odu_ca_cert_decoded.decode("utf-8")
        return "\n".join(crypto_string.split("\n")[1:-2])

    @staticmethod
    def get_certificate_fingerprint(cert: bytes) -> str:
        ''' Method for getting the fingerprint of a certificate, prepended by a byte representing the algorithm that was used for encoding
        '''
        # Compute the fingerprint using SHA-1
        fingerprint_bytes = cert.fingerprint(hashes.SHA1())

        # Prepend the byte 0x02 to the fingerprint bytes
        # 0x02 is SHA1 encoding, according to https://datatracker.ietf.org/doc/html/rfc5246#section-7.4.1.4.1
        fingerprint_bytes = b'\x02' + fingerprint_bytes

        # Convert the fingerprint to a more readable hex format
        fingerprint_hex = ':'.join([f"{byte:02X}" for byte in fingerprint_bytes])
        return fingerprint_hex
