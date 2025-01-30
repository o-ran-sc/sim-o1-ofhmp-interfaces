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

from core.ves import VesMessage
from alarm import Alarm

class VesAlarm(VesMessage):
    def __init__(self, alarm: Alarm):
        super().__init__()

        self.data["event"]["stndDefinedFields"] = {
            "schemaReference": "https://forge.3gpp.org/rep/sa5/MnS/blob/Rel-18/OpenAPI/TS28532_FaultMnS.yaml#components/schemas/NotifyNewAlarm",
            "stndDefinedFieldsVersion": "1.0",
            "data": {
                "href": "href1",
                "notificationId": 0, #@notification-id@,
                "notificationType": "notifyNewAlarm", #  notifyClearedAlarm
                "eventTime": "@timestampISO3milisec@",
                "systemDN": "ManagedElement=@node-id@",
                "alarmId": "@object-instance@-@alarm@",
                "alarmType": "@alarm-type@",
                "probableCause": "@alarm@",
                "specificProblem": "@alarm@",   # gone
                "perceivedSeverity": "@severity@",  # "CLEARED"

                # "clearUserId": "@vendor@",
                # "clearSystemId": "@vendor@"

                "backedUpStatus": True,
                "trendIndication": "MORE_SEVERE",
                "stateChangeDefinition": [{ "operational-state": "DISABLED" }],
                "proposedRepairActions": "Add more units",
                "additionalText": "Open Air Interface",
                "rootCauseIndicator": False
            }
        }

        self.namespace = "3GPP-FaultSupervision"
        self.domain = "stndDefined"
        self.priority = "Low"
        self.event_type = "PyNTS_Alarm"

    def update(self) -> None:
        super().update()

