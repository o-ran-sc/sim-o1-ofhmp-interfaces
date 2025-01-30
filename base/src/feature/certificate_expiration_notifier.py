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

from util.logging import get_pynts_logger
import schedule
import threading

from core.config import Config
from core.netconf import Netconf
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta, timezone
from util.crypto import CryptoUtils
from util.threading import stop_event, sa_sleep

logger = get_pynts_logger("feature-certificate-expiration-notifier")

class CertificateExpirationNotifierFeature:
    def __init__(self) -> None:
        self.config = Config()
        self.cryptoUtils = CryptoUtils()
        self.netconf = Netconf()

    def start(self) -> None:
        certificate = x509.load_pem_x509_certificate(self.cryptoUtils.odu_certificate, default_backend())
        self.expiration_date = certificate.not_valid_after_utc
        self.formatted_date = self.expiration_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"  # YANG date-and-time format

        if self.config.is_tls_enabled():
            thread = threading.Thread(target=self.run_scheduler)
            thread.start()
        else:
            logger.debug("Not starting certificate expiration notification feature, TLS is not enabled...")

    def run_scheduler(self):
        # Schedule the job to run every day
        schedule.every().day.do(self.certificate_expiration_job)

        # Loop so that the scheduling task keeps on running all time.
        while not stop_event.is_set():
            schedule.run_pending()
            sa_sleep(3600)

        logger.info("thread finished")


    def certificate_expiration_job(self):
        # Get the current date and time
        current_date = datetime.now(timezone.utc)
        if self.expiration_date < (current_date + timedelta(days=30)):
            logger.debug(f"Certificate expiring in less that 30 days ({self.expiration_date}). Sending certificate-expiration notification..")

            if self.config.tls_callhome_endpoint:
                d = self.netconf.running.get_item("/ietf-netconf-server:netconf-server/call-home/netconf-client/endpoints/endpoint/tls/tls-server-parameters/server-identity/certificate/inline-definition")
            elif self.config.tls_listen_endpoint:
                d = self.netconf.running.get_item("/ietf-netconf-server:netconf-server/listen/endpoints/endpoint/tls/tls-server-parameters/server-identity/certificate/inline-definition")

            self.netconf.running.notification_send(d.xpath + "/certificate-expiration", {"expiration-date": self.formatted_date})








