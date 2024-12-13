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

from datetime import datetime

from core.config import Config
from core.ves import VesMessage
from util.datetime import yang_timestamp_with_miliseconds

ves_file_ready_notification_id = 0

class VesFileReady(VesMessage):
    file_location: str

    def __init__(self, file_location: str, file_size: int, expiry: datetime):
        super().__init__()

        self.file_location = file_location

        self.data["event"]["stndDefinedFields"] = {
            "schemaReference": "https://forge.3gpp.org/rep/sa5/MnS/blob/Rel-18/OpenAPI/TS28532_FileDataReportingMnS.yaml#components/schemas/NotifyFileReady",
            "stndDefinedFieldsVersion": "1.0",
            "data": {
                "href": "href1",
                # "notificationId": 0, # @notification-id@,
                "notificationType": "notifyFileReady",
                # "eventTime": "@timestampISO3milisec@",
                # "systemDN": "ManagedElement=@node-id@",
                "fileInfoList": [{
                    # "fileLocation": "sftp://@username@:@password@@@oamIp@:@port@@fileLocation@",
                    "fileSize": file_size, # @fileSize@,
                    # "fileReadyTime": "@timestampISO3milisec@",    # checkAL
                    "fileExpirationTime": yang_timestamp_with_miliseconds(expiry),
                    "fileCompression": "no",
                    "fileFormat": "xml",
                    "fileDataType": "Performance"
                }],
                "additionalText": "Have fun!"
            }
        }

        self.namespace = "3GPP-PerformanceAssurance"
        self.domain = "stndDefined"
        self.priority = "Low"
        self.event_type = "PyNTS_FileReady"

    def update(self) -> None:
        super().update()

        config: Config = Config()

        global ves_file_ready_notification_id

        ves_file_ready_notification_id = ves_file_ready_notification_id + 1
        self.data["event"]["stndDefinedFields"]["data"]["notificationId"] = ves_file_ready_notification_id
        self.data["event"]["stndDefinedFields"]["data"]["eventTime"] = self.timestampISO3milisec
        self.data["event"]["stndDefinedFields"]["data"]["systemDN"] = "ManagedElement=" + self.hostname

        self.data["event"]["stndDefinedFields"]["data"]["fileInfoList"][0]["fileLocation"] = f"sftp://{config.netconf_username}:{config.netconf_password}@{self.ipv4}:{config.sftp_listen_port}{self.file_location}"
        self.data["event"]["stndDefinedFields"]["data"]["fileInfoList"][0]["fileReadyTime"] = self.timestampISO3milisec

