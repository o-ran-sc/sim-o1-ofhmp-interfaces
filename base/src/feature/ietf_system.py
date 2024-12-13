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
from util.docker import get_hostname, get_container_ip

logger = get_pynts_logger("feature-ietf-system")

class IetfSystemFeature:
    def __init__(self) -> None:
        DictFactory.add_template("ietf-system", IetfSystemTemplate)
        self.netconf: Netconf = Netconf()

    def configure(self) -> None:
        ietf_system_template = DictFactory.get_template("ietf-system")
        ietf_system_template.update_key(["ietf-system", "system", "hostname"], get_hostname())
        ietf_system_template.update_key(["ietf-system", "system", "onap-system:web-ui"], "http://" + get_container_ip())

        self.netconf.set_data(Datastore.RUNNING, "", ietf_system_template.data)
        self.netconf.set_data(Datastore.OPERATIONAL, "", ietf_system_template.data)
        logger.info("succesfully configured")


class IetfSystemTemplate(BaseTemplate):
    """A dictionary template for ietf-system objects."""
    def create_dict(self):
        return {
                "ietf-system": {
                    "system": {
                        "contact": "Network Topology Simulator",
                        "hostname": "TO_BE_REPLACED_HOSTNAME",
                        "onap-system:web-ui": "TO_BE_REPLACED_URL"
                    }
                }
            }

