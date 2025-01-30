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

from core.dict_factory import DictFactory, BaseTemplate
from core.netconf import Netconf

logger = get_pynts_logger("ietf-netconf-acm")

class NetconfAcmFeature:
    def __init__(self) -> None:
        DictFactory.add_template("netconf-acm-enabled", NetconfAcmTemplateEnabled)
        DictFactory.add_template("netconf-acm-disabled", NetconfAcmTemplateDisabled)
        self.netconf: Netconf = Netconf()

    def configure(self, enabled: bool = False) -> None:
        nacm_template = DictFactory.get_template("netconf-acm-enabled") if enabled else DictFactory.get_template("netconf-acm-disabled")

        with self.netconf.connection.start_session("running") as sess:
            sess.replace_config(nacm_template.data, "ietf-netconf-acm")
        with self.netconf.connection.start_session("operational") as sess:
            sess.edit_batch(nacm_template.data, "ietf-netconf-acm")
            sess.apply_changes()
        logger.info("succesfully configured")


class NetconfAcmTemplateEnabled(BaseTemplate):
    """A dictionary template for netconf-acm objects, when ACM is enabled."""
    def create_dict(self):
        return {
                "nacm": {
                    "enable-nacm": True,
                    "groups": {
                        "group": [
                            {
                                "name": "sudo",
                                "user-name": ["sudo", "oranuser"]
                            },
                            {
                                "name": "smo",
                                "user-name": ["smo"]
                            },
                            {
                                "name": "hybrid-odu",
                                "user-name": ["hybrid-odu"]
                            },
                            {
                                "name": "carrier",
                                "user-name": ["carrier"]
                            }
                        ]
                    }
                }
            }
    

class NetconfAcmTemplateDisabled(BaseTemplate):
    """A dictionary template for netconf-acm objects, when ACM is disabled."""
    def create_dict(self):
        return {
                "nacm": {
                    "enable-nacm": False
                }
            }

