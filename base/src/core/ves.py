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
import json
import threading

from core.config import Config
from util.docker import get_container_ip, get_hostname, get_container_mac_address
from util.datetime import timestamp_in_microseconds, yang_timestamp_with_miliseconds
import requests

logger = get_pynts_logger("ves")
lock = threading.Lock()

class VesMessage():
    data: dict

    domain: str
    event_type: str
    priority: str
    namespace: str|None

    timestampMicrosec: int
    timestampISO3milisec: int
    hostname: str
    mac_address: str
    ipv4: str|None
    ipv6: str|None

    def __init__(self, append_port: bool = False, port: int = 830):
        # commented fields are set on update()
        self.append_port = append_port
        self.port = port
        self.data = {
            "event": {
                "commonEventHeader": {
                    # "domain": "@domain@",
                    # "eventId": "ManagedElement=@node-id@",
                    # "eventName": "@domain@_@eventType@",
                    # "eventType": "@eventType@",
                    # "sequence": 0,  # @seqId@
                    # "priority": "@priority@",
                    "reportingEntityId": "",
                    # "reportingEntityName": "ManagedElement=@node-id@",
                    # "sourceId": "ManagedElement=@node-id@", # WAS "@managed-element-id@",
                    # "sourceName": "@node-id@",
                    # "startEpochMicrosec": 0, # @timestampMicrosec@
                    # "lastEpochMicrosec": 0, # @timestampMicrosec@
                    "nfNamingCode": "001",
                    # "nfVendorName": "@vendor@",
                    "timeZoneOffset": "+00:00",
                    "version": "4.1",
                    # "stndDefinedNamespace": "",    # @namespace@
                    "vesEventListenerVersion": "7.2.1"
                }
            }
        }

    def get(self) -> str:
        return json.dumps(self.data)

    def update(self) -> None:
        ves = Ves()

        self.timestampMicrosec = timestamp_in_microseconds()
        self.timestampISO3milisec = yang_timestamp_with_miliseconds()
        self.hostname = get_hostname() if self.append_port is False else get_hostname() + "_" + str(self.port)
        self.mac_address = get_container_mac_address()
        self.ipv4 = get_container_ip()
        self.ipv6 = None # checkAL


        self.data["event"]["commonEventHeader"]["domain"] = self.domain
        self.data["event"]["commonEventHeader"]["eventId"] = "ManagedElement=" + self.hostname + "_" + self.domain
        self.data["event"]["commonEventHeader"]["eventName"] = self.domain + "_" + self.event_type
        self.data["event"]["commonEventHeader"]["eventType"] = self.event_type
        self.data["event"]["commonEventHeader"]["sequence"] = ves.seq_id
        self.data["event"]["commonEventHeader"]["priority"] = self.priority
        self.data["event"]["commonEventHeader"]["reportingEntityName"] = "ManagementElement=" + self.hostname
        self.data["event"]["commonEventHeader"]["sourceId"] = "ManagementElement=" + self.hostname
        self.data["event"]["commonEventHeader"]["sourceName"] = self.hostname
        self.data["event"]["commonEventHeader"]["startEpochMicrosec"] = self.timestampMicrosec
        self.data["event"]["commonEventHeader"]["lastEpochMicrosec"] = self.timestampMicrosec

        self.data["event"]["commonEventHeader"]["nfVendorName"] = ves.vendor
        if self.namespace:
            self.data["event"]["commonEventHeader"]["stndDefinedNamespace"] = self.namespace

class Ves:
    _instance = None
    config: Config

    seq_id = 0
    vendor = ""

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            cls._instance.config = Config()
            cls._instance.seq_id = 0
            cls._instance.vendor = "pynts"
        return cls._instance


    def execute(self, message: VesMessage) -> bool:
        result = False
        with lock:
            url = self.config.ves_url

            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-MinorVersion': '1'
            }

            auth = None
            if self.config.ves_username != "" and self.config.ves_password != "":
                auth = (self.config.ves_username, self.config.ves_password)

            message.update()
            message_str = message.get()

            logger.debug(f"POST {url} -> {message_str}")

            if url != "":
                response = requests.post(url, headers=headers, auth=auth, data=message_str, verify=False, timeout=5.0)

                if response.status_code >= 200 and response.status_code < 300:
                    result = True
                else:
                    logger.error(f"request failed with status code {response.status_code} and response {response.text}")
            else:
                result = True

            if result:
                self.seq_id = self.seq_id + 1

        return result

