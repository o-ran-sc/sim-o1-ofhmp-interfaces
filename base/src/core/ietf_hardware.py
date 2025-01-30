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

import uuid
from util.logging import get_pynts_logger

from core.config import Config
from core.netconf import Netconf, Datastore

from libyang.keyed_list import KeyedList


logger = get_pynts_logger("ietf-hardware")

"""
IetfHardware
Singleton
----
configures ietf-hardware
"""
class IetfHardware:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.debug("Created IetfHardware object")

            cls._instance.set_config()

        return cls._instance

    def set_config(self) -> None:
        self.netconf: Netconf = Netconf()
        self.config: Config = Config()
        self.namespace = uuid.NAMESPACE_URL
                
    def check_ietf_hardware(self):
      hardware = self.netconf.running.get_data("/ietf-hardware:hardware")
      # logger.debug(f"Found hardware: {hardware}")
      
      components = hardware
      try:
        for key in ['hardware', 'component']:
          components = components[key]
          
        if isinstance(components, list):
          for component in components:
            # Update alias and asset-id
            component['alias'] = f"{self.config.hostname}-{component['name']}"
            component['asset-id'] = uuid.uuid5(self.namespace, component['alias'])                        
            
            # Check if 'uri' is presents
            if 'uri' in component:
                uris = component['uri']
                
                new_uri = f"https://{self.config.hostname}.dcn/restconf/data/ietf-hardware:hardware/component/{component['name']}"
                if new_uri not in uris._map:
                  uris.append(new_uri)                
            else:
                component['uri'] = KeyedList()
                
                new_uri = f"https://{self.config.hostname}.dcn/restconf/data/ietf-hardware:hardware/component/{component['name']}"
                component['uri'].append(new_uri)                 
            
            # logger.debug(f"Transforming {component['name']} with alias {component['alias']} and asset-id {component['asset-id']}")
      except KeyError as e:
          logger.error(f"Keys not found in JSON object {hardware}. Error: {e}")
      except TypeError as e:
          logger.error(f"List not at the expected level in {hardware}. Error: {e}")
          
      # logger.debug(f"New hardware is: {hardware}")
      self.netconf.running.edit_batch(hardware, "ietf-hardware")
      self.netconf.running.apply_changes()
      with self.netconf.connection.start_session("operational") as sess:
        sess.edit_batch(hardware, "ietf-hardware")
        sess.apply_changes()
