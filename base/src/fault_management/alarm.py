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
from datetime import datetime
from util.datetime import yang_datetime_to_datetime, datetime_to_yang_datetime, datetime_utcnow
from strenum import StrEnum

logger = get_pynts_logger("alarm")

class PerceivedSeverity(StrEnum):
    CLEARED = "cleared"
    # indeterminate falls back to WARNING on o-ran-fm
    INDETERMINATE = "indeterminate"
    WARNING = "warning"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"

class Alarm:
    # combined id
    c_id: str
    _times_raised: int
    _times_cleared: int

    resource: str
    alarm_type_id: str
    alarm_type_qualifier: str

    is_cleared: bool
    perceived_severity: PerceivedSeverity

    time_created: datetime
    last_raised: datetime
    last_changed: datetime

    alarm_text: str

    def __init__(self) -> None:
        raise Exception("Can't create an empty alarm.")

    def __init__(self, resource: str, alarm_type_id: str, alarm_type_qualifier: str):
        self.resource = resource
        self.alarm_type_id = alarm_type_id
        self.alarm_type_qualifier = alarm_type_qualifier
        self.c_id = self.resource + self.alarm_type_id + self.alarm_type_qualifier
        self._times_raised = 0
        self._times_cleared = 0

        from fault_management.fault_management import FaultManagement
        self.fault_management: FaultManagement = FaultManagement()

    def alarm_raise(self, severity:PerceivedSeverity|None = None) -> None:
        if self.is_cleared:
            if severity is not None:
                if severity == PerceivedSeverity.CLEARED:
                    raise ValueError("Can't raise an alarm with CLEARED severity.")
                self.perceived_severity = severity
            self.is_cleared = False
            self.last_changed = datetime_utcnow()
            self.last_raised = self.last_changed

            self._times_raised = self._times_raised + 1

            self.fault_management.on_alarm_change(self)

    def alarm_clear(self) -> None:
        if not self.is_cleared:
            self.is_cleared = True
            self.last_changed = datetime_utcnow()

            self._times_cleared = self._times_cleared + 1

            self.fault_management.on_alarm_change(self)

    def alarm_notify(self) -> None:
        self.fault_management.send_notification(self)

    def counters_get(self) -> dict:
        return {"raised": self._times_raised, "cleared": self._times_cleared}

    def counters_clear(self) -> None:
        self._times_raised = 0
        self._times_cleared = 0


    @staticmethod
    def from_ietf_alarm(data: dict):
        alarm = Alarm(data["resource"], data["alarm-type-id"], data["alarm-type-qualifier"])

        a = alarm.fault_management.get_alarm(alarm.c_id)
        if a is None:
            alarm.fault_management.add_alarm(alarm)
        else:
            alarm = a

        alarm.is_cleared = data["is-cleared"]
        alarm.perceived_severity = PerceivedSeverity(data["perceived-severity"])
        alarm.alarm_text = data["alarm-text"]

        if "time-created" in data and "last-raised" in data and "last-changed" in data:
            alarm.time_created = yang_datetime_to_datetime(data["time-created"])
            alarm.last_raised = yang_datetime_to_datetime(data["last-raised"])
            alarm.last_changed = yang_datetime_to_datetime(data["last-changed"])
        else:
            alarm_time = datetime_utcnow()
            alarm.time_created = alarm_time
            alarm.last_raised = alarm_time
            alarm.last_changed = alarm_time

            if alarm.is_cleared:
                logger.warn(f"Alarm with id {alarm.c_id} was created as cleared.")


        if alarm.is_cleared:
            alarm._times_cleared = alarm._times_cleared + 1
        else:
            alarm._times_raised = alarm._times_raised + 1

        alarm.fault_management.on_alarm_change(alarm)
        return alarm


    @staticmethod
    def from_ietf_alarm_notif(notif: dict):
        alarm = Alarm(notif["resource"], notif["alarm-type-id"], notif["alarm-type-qualifier"])

        alarm_time = datetime_utcnow()
        if "time" in notif:
            alarm_time = yang_datetime_to_datetime(notif["time"])

        a = alarm.fault_management.get_alarm(alarm.c_id)
        if a is None:
            alarm.time_created = alarm_time
            alarm.last_raised = alarm_time
            alarm.fault_management.add_alarm(alarm)
        else:
            alarm = a

        if "perceived-severity" in notif:
            alarm.is_cleared = False
            perceived_severity = PerceivedSeverity(notif["perceived-severity"])
            if perceived_severity == PerceivedSeverity.CLEARED:
                if alarm.perceived_severity is None:
                    alarm.perceived_severity = PerceivedSeverity.INDETERMINATE
                alarm.is_cleared = True
            else:
                alarm.perceived_severity = perceived_severity
                alarm.last_raised = alarm_time

        if "is-cleared" in notif:
            alarm.is_cleared = notif["is-cleared"]

        if "alarm-text" in notif:
            alarm.alarm_text = notif["alarm-text"]

        alarm.last_changed = alarm_time

        if alarm.is_cleared:
            alarm._times_cleared = alarm._times_cleared + 1
        else:
            alarm._times_raised = alarm._times_raised + 1


        alarm.fault_management.on_alarm_change(alarm)
        return alarm

    def to_ietf_alarm(self) -> dict:
        data = {}
        data["resource"] = self.resource
        data["alarm-type-id"] = self.alarm_type_id
        data["alarm-type-qualifier"] = self.alarm_type_qualifier

        data["is-cleared"] = self.is_cleared
        data["perceived-severity"] = str(self.perceived_severity)

        data["time-created"] = datetime_to_yang_datetime(self.time_created)
        data["last-raised"] = datetime_to_yang_datetime(self.last_raised)
        data["last-changed"] = datetime_to_yang_datetime(self.last_changed)

        data["alarm-text"] = self.alarm_text

        return data



    def to_ietf_alarm_notif(self) -> dict:
        data = {}
        data["resource"] = self.resource
        data["alarm-type-id"] = self.alarm_type_id
        data["alarm-type-qualifier"] = self.alarm_type_qualifier

        if self.is_cleared:
            data["perceived-severity"] = PerceivedSeverity.CLEARED
        else:
            data["perceived-severity"] = str(self.perceived_severity)

        data["time"] = datetime_to_yang_datetime(self.last_changed)

        data["alarm-text"] = self.alarm_text

        return data




    # ietf-alarms                                         o-ran-fm

    # resource: str                       fault-source: str
    # alarm_type_id: str                  alarm_type: str ... e de fapt enum
    # alarm_type_qual: str                fault_id: uint16

    # is_cleared: bool                    is_cleared: bool
    # perceived_severity: enum            fault_severty: enum

    # time_created: datettime             ... se pot scoate din cod
    # last_raised: datettime              ... se pot scoate din cod
    # last_changed: datettime             event_time: datetime

    # alarm_text: str                     fault_text: str



    # @staticmethod
    # def from_oran_fm(data: dict):
    #     alarm = Alarm()
    #     alarm.resource = data["fault-source"]
    #     # alarm.alarm_type_id = data["alarm-type-id"]
    #     alarm.alarm_type_qual = data["fault-id"]

    #     alarm.is_cleared = data["is-cleared"]
    #     alarm.perceived_severity = data["fault-severity"]

    #     alarm_time = data["event-time"]

    #     # update these checkAL
    #     # alarm.time_created = data["time-created"]
    #     # alarm.last_raised = data["last-raised"] # checkAL
    #     # alarm.last_changed = data["last-changed"]

    #     alarm.alarm_text = data["fault-text"]



    #     return alarm

    # def to_oran_fm(self) -> dict:
    #     return {}

    # @staticmethod
    # def from_oran_fm_notif(notif: dict):
    #     return Alarm.from_oran_fm(notif)

    # def to_oran_fm_notif(self) -> dict:
    #     return self.to_oran_fm()
