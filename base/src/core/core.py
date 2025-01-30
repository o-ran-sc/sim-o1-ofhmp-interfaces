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
from pathlib import Path
from libyang.util import LibyangError

from core.extension import Extension
from core.rest import Rest
from core.netconf import Netconf, Datastore
from core.config import Config
from core.netconf_server import NetconfServer
from core.ietf_hardware import IetfHardware

from fault_management.fault_management import FaultManagement
from performance_management.performance_management import PerformanceManagement

from feature.ietf_keystore_truststore import IetfKeystoreTruststoreFeature
from feature.ietf_system import IetfSystemFeature
from feature.certificate_expiration_notifier import CertificateExpirationNotifierFeature
from feature.netconf_acm import NetconfAcmFeature

from feature.ves_heartbeat import VesHeartbeatFeature
from feature.ves_pnfregistration import VesPnfRegistrationFeature

logger = get_pynts_logger("core")

class Core(Extension):
    def init(self) -> None:
        self.rest: Rest = Rest()
        self.netconf: Netconf = Netconf()   # initialize netconf sessions
        self.config: Config = Config()
        self.netconf_server: NetconfServer = NetconfServer()
        self.ietf_hardware: IetfHardware = IetfHardware()
        self.fault_management: FaultManagement = FaultManagement()
        self.performance_management: PerformanceManagement = PerformanceManagement()

    def startup(self) -> None:
        # load IetfKeystoreTruststoreFeature
        logger.info("loading IetfKeystoreTruststoreFeature")
        self.ietf_keystore_truststore_feature: IetfKeystoreTruststoreFeature = IetfKeystoreTruststoreFeature()
        self.ietf_keystore_truststore_feature.configure()
        
        # load IetfSystemFeature
        logger.info("loading IetfSystemFeature")
        self.ietf_system_feature: IetfSystemFeature = IetfSystemFeature()
        self.ietf_system_feature.configure()

        # # load NetconfAcmFeature
        # logger.info("loading NetconfAcmFeature")
        # self.netconf_acm_feature: NetconfAcmFeature = NetconfAcmFeature()
        # self.netconf_acm_feature.configure(enabled=True)

        # load CertificateExpirationNotifierFeature
        logger.info("loading CertificateExpirationNotifierFeature")
        self.certificate_expiration_notifier_feature: CertificateExpirationNotifierFeature = CertificateExpirationNotifierFeature()
        self.certificate_expiration_notifier_feature.start()


        # populate all data
        logger.info("attempting to populate netconf data")
        if Path("/data").exists():
            ds_files = self.netconf.get_datastore_files("/data", "json|xml")
            for ds_file in ds_files:
                try:
                    self.netconf.set_data_from_path(Datastore(ds_file['datastore']), ds_file['module_name'], ds_file['extension'], ds_file['filename'])
                except LibyangError as e:
                    logger.error(f"Could not load {ds_file['extension']} data in {ds_file['datastore']} for module {ds_file['module_name']} from {ds_file['filename']}")
                    logger.error(f"Exception: {e}")
        
        self.ietf_hardware.check_ietf_hardware()
        
        with self.netconf.connection.start_session("startup") as sess_start:
          logger.debug(f"Copying contents of running datastore into startup...")
          sess_start.copy_config("running")
          sess_start.apply_changes()
          logger.debug(f"Finished copying contents of running datastore into startup!")
        # ves pnfRegistration
        # self.ves_pnfregistration = VesPnfRegistrationFeature()
        # self.ves_pnfregistration.start()

        # # ves heartbeat
        # self.ves_heartbeat = VesHeartbeatFeature()
        # self.ves_heartbeat.start()

        # # fault management
        # self.fault_management.load_active_alarms()
        # self.fault_management.start()

        # # performance management
        self.performance_management.start()
