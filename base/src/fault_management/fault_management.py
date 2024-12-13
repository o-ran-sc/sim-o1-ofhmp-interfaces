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
import threading
import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime
from util.datetime import ensure_aware, yang_datetime_to_datetime, datetime_utcnow
from util.threading import stop_event, sa_sleep
from core.netconf import Netconf, Datastore
from core.rest import Rest
from fault_management.alarm import Alarm

logger = get_pynts_logger("fault-management")

# Event to signal threads to stop
fault_stop_event = threading.Event()

class FaultManagement:
    _instance = None

    _ietf_alarms: bool = False
    _o_ran_fm: bool = False

    netconf: Netconf
    rest: Rest

    alarms: dict[str, Alarm]
    last_changed: datetime

    alarm_config: dict
    alarm_steps: list

    disabled: bool = False
    stopped: bool = True

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init()

        return cls._instance

    def init(self):
        self.netconf = Netconf()
        self.rest = Rest()

        self.alarms = {}

        self.last_changed = datetime_utcnow()

        with self.netconf.connection.get_ly_ctx() as ctx:
            try:
                ctx.get_module("ietf-alarms")
                self._ietf_alarms = True
            except:
                self._ietf_alarms = False

            try:
                ctx.get_module("o-ran-fm")
                self._o_ran_fm = True
            except:
                self._o_ran_fm = False

        if self._ietf_alarms and self._o_ran_fm:
            logger.error(f"fault-management can't work with both ietf-alarms and o-ran-fm")
            self.disabled = True
            return

        if self._ietf_alarms:
            logger.info("ietf-alarms found and registered as a fault-management provider")

        if self._o_ran_fm:
            logger.info("o-ran-fm found and registered as a fault-management provider")

        if not self._ietf_alarms and not self._o_ran_fm:
            logger.warn("fault-management disabled as there is no registered provider")
            self.disabled = True
            return

        self.rest.add_route("/fault-management", FaultManagementRest())
        self.rest.add_route("/fault-management/start", FaultManagementRest())
        self.rest.add_route("/fault-management/stop", FaultManagementRest())
        self.rest.add_route("/fault-management/counters", FaultManagementRest())
        self.rest.add_route("/fault-management/counters/clear", FaultManagementRest())

    def add_alarm(self, alarm: Alarm) -> None:
        if alarm.c_id in self.alarms:
            raise ValueError(f"Alarm with c_id {alarm.c_id} already exists.")

        self.alarms[alarm.c_id] = alarm

    def get_alarm(self, c_id) -> Alarm|None:
        return self.alarms.get(c_id, None)

    def contains_alarm(self, c_id) -> bool:
        return c_id in self.alarms

    def get_alarms(self) -> list[Alarm]:
        return list(self.alarms.values())

    def on_alarm_change(self, alarm: Alarm) -> None:
        alarm.last_changed = ensure_aware(alarm.last_changed)
        self.last_changed = ensure_aware(self.last_changed)
        if alarm.last_changed > self.last_changed:
            self.last_changed = alarm.last_changed

    def load_active_alarms(self) -> None:
        # load current alarms from datastore
        if self._ietf_alarms:
            xpath = "/ietf-alarms:alarms"

            # get active alarm list if any
            current_alarms_dict = self.netconf.get_data(Datastore.OPERATIONAL, xpath)
            if 'alarms' in current_alarms_dict and 'alarm-list' in current_alarms_dict['alarms']:
                alarm_list = current_alarms_dict['alarms']['alarm-list']

                if 'alarm' in alarm_list and 'last-changed' in alarm_list:
                    self.last_changed = yang_datetime_to_datetime(alarm_list["last-changed"])

                    for alarm in alarm_list['alarm']:
                        new_alarm = Alarm.from_ietf_alarm(alarm)
                        logger.info(f"added to alarm list {new_alarm.alarm_text}")

            # subscribe to active alarm list
            self.netconf.operational.subscribe_oper_data_request("ietf-alarms", xpath, self._callback_oper_ietf_alarms_list)

        if self._o_ran_fm:
            xpath = "/o-ran-fm:active-alarm-list"

            # get active alarm list if any
            current_alarms_dict = self.netconf.get_data(Datastore.OPERATIONAL, xpath)
            checkAL

            # subscribe to active alarm list
            # self.netconf.operational.subscribe_oper_data_request("o-ran-fm", xpath, self._callback_oper_o_ran_fm_list)

    def load_alarms(self, alarm_data = None):
        if alarm_data is None:
            # read data from fault-management/index.json
            alarms_path = '/data/fault-management/index.json'
            alarm_data = {}
            if Path(alarms_path).exists():
                # Read and parse the JSON file
                with open(alarms_path, 'r') as file:
                    alarm_data = json.load(file)
            else:
                raise Exception("settings file not found; stopping fault-management")

        alarm_steps = alarm_data["alarms"]

        total_delay = 0
        for step in alarm_steps:
            if 'delay' in step:
                total_delay += step["delay"]

        if total_delay == 0:
            raise Exception("for configured alarms there is a total delay of 0; stopping fault-management")

        self.alarm_config = alarm_data["config"]
        self.alarm_steps = alarm_steps

        if "loop" not in self.alarm_config:
            self.alarm_config["config"] = True

    def start(self, alarm_data = None) -> dict:
        if self.disabled:
            return {"code": 500, "message": "feature is disabled; check log"}

        if self.stopped is False:
            return {"code": 500, "message": "feature is already running"}

        try:
            self.load_alarms(alarm_data)
        except Exception as e:
            logger.error(e)
            return {"code": 500, "message": e.__traceback__}

        # clear stopped
        fault_stop_event.clear()
        self.stopped = False

        # start fault management thread
        logger.info("starting fault management thread...")
        thread = threading.Thread(target=self.fault_management_task)
        thread.start()
        return {"code": 200, "message": "ok"}

    def stop(self) -> dict:
        if self.stopped:
            return {"code": 500, "message": "feature is already stopped"}
        else:
            fault_stop_event.set()
            return {"code": 200, "message": "ok"}

    def _callback_oper_ietf_alarms_list(self, xpath: str, private_data: Any) -> Optional[dict]:
        return {
            "alarms": {
                "alarm-list":
                {
                    "number-of-alarms": len(self.alarms),
                    "last-changed": self.last_changed.replace(microsecond=0).isoformat(),
                    "alarm": [
                        a.to_ietf_alarm() for a in self.get_alarms()
                    ]
                }
            }
        }

    def _callback_oper_o_ran_fm_list(self, xpath: str, private_data: Any) -> Optional[dict]:
        return {
            "active-alarms": [
                a.to_oran_fm() for a in self.get_alarms() if not a.is_cleared
            ]
        }

    def send_notification(self, alarm: Alarm) -> None:
        xpath = ""
        if self._ietf_alarms:
            xpath = "/ietf-alarms:alarm-notification"
            self.netconf.running.notification_send(xpath, alarm.to_ietf_alarm_notif())
            logger.info(f"sending alarm notif {alarm.alarm_text}/cleared:{alarm.is_cleared} to {xpath}")

        if self._o_ran_fm:
            xpath = "/o-ran-fm:alarm-notif"
            self.netconf.running.notification_send(xpath, alarm.to_oran_fm_notif())
            logger.info(f"sending alarm notif {alarm.alarm_text}/cleared:{alarm.is_cleared} to {xpath}")

        if xpath == "":
            raise Exception("no alarm sent, as no provider found")

    def fault_management_task(self):
        current_step = -1
        while not self.stopped and not stop_event.is_set() and not fault_stop_event.is_set():
            current_step = current_step + 1
            if current_step >= len(self.alarm_steps):
                if self.alarm_config["loop"]:
                    current_step = 0
                else:
                    break

            step = self.alarm_steps[current_step]

            if 'alarm' in step:
                alarm = None
                if self._ietf_alarms:
                    alarm = Alarm.from_ietf_alarm_notif(step['alarm'])

                if self._o_ran_fm:
                    alarm = Alarm.from_oran_fm_notif(step['alarm'])

                alarm.alarm_notify()

            if 'delay' in step:
                current_delay = step['delay']
                sa_sleep(current_delay, fault_stop_event)

        self.stopped = True
        logger.info("thread finished")

class FaultManagementRest:
        _instance = None
        fm: FaultManagement

        def __new__(cls):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.fm = FaultManagement()

            return cls._instance

        async def on_get(self, req, resp):
            if req.url.endswith("/fault-management"):
                resp.media = {"stopped": self.fm.stopped, "disabled": self.fm.disabled, "config": self.fm.alarm_config}
                resp.status = 200
            elif req.url.endswith("/fault-management/counters"):
                resp.media = self.get_alarm_counters()
                resp.status = 200
            else:
                resp.media = {"message": "not found"}
                resp.status = 404

        async def on_post(self, req, resp):
            if req.url.endswith("/fault-management/start"):
                data = await req.get_media()
                start = self.fm.start(data)
                resp.media = {"message": start["message"], "stopped": self.fm.stopped, "disabled": self.fm.disabled, "config": self.fm.alarm_config}
                resp.status = start["code"]

            elif req.url.endswith("/fault-management/stop"):
                stop = self.fm.stop()
                resp.media = {"message": stop["message"], "stopped": self.fm.stopped, "disabled": self.fm.disabled, "config": self.fm.alarm_config}
                resp.status = stop["code"]

            elif req.url.endswith("/fault-management/counters/clear"):
                self.clear_alarm_counters()
                resp.media = {"status": "cleared", "counters": self.get_alarm_counters()}
                resp.status = 200

            else:
                resp.media = {"message": "not found"}
                resp.status = 404

        def get_alarm_counters(self) -> dict:
            counters = {}
            for alarm in self.fm.alarms:
                counters[alarm] = self.fm.alarms[alarm].counters_get()
            return counters

        def clear_alarm_counters(self) -> None:
            for alarm in self.fm.alarms:
                self.fm.alarms[alarm].counters_clear()

