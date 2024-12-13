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
import schedule
import threading

from core.config import Config
from core.netconf import Netconf
from core.ves import VesMessage, Ves
from util.threading import stop_event, sa_sleep

logger = get_pynts_logger("ves-heartbeat")

class VesHeartbeatFeature:
    def __init__(self) -> None:
        self.config = Config()
        self.netconf = Netconf()
        self.ves = Ves()

    def start(self) -> None:
        logger.info("starting...")

        self.interval = 30
        self.ves_heartbeat: VesHeartbeat = VesHeartbeat(self.interval)
        thread = threading.Thread(target=self.run_scheduler)
        thread.start()

    def run_scheduler(self):
        # Schedule the job to run
        schedule.every(self.interval).seconds.do(self.heartbeat)

        # Loop so that the scheduling task keeps on running all time.
        while not stop_event.is_set():
            schedule.run_pending()
            sa_sleep(self.interval)

        logger.info("thread finished")


    def heartbeat(self):
        logger.info("heartbeat event")
        self.ves.execute(self.ves_heartbeat)


class VesHeartbeat(VesMessage):
    def __init__(self, interval: int):
        super().__init__()

        self.data["event"]["heartbeatFields"] = {
            "heartbeatFieldsVersion": "3.0",
            "heartbeatInterval": interval,
            "additionalFields": {
                "eventTime": "@timestampISO3milisec@"
            }
        }

        self.namespace = None
        self.domain = "HeartBeat"
        self.priority = "Low"
        self.event_type = "PyNTS_HeartBeat"

    def update(self) -> None:
        super().update()

        self.data["event"]["heartbeatFields"]["additionalFields"]["eventTime"] = self.timestampISO3milisec
