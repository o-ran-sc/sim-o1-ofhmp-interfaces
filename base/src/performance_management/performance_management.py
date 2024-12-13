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
import re
import os
import subprocess
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timedelta
from typing import List
from core.config import Config
from core.ves import Ves
from util.datetime import seconds_to_duration, datetime_utcnow
from util.threading import stop_event, sa_sleep

from performance_management.ves_fileready import VesFileReady

logger = get_pynts_logger("performance-management")

# Event to signal threads to stop
pm_stop_event = threading.Event()

PM_DATA_PATH = "/ftp"

class PerformanceManagement:
    _instance = None

    config: Config

    points: List[str]
    points_id: dict
    log_period: int
    repetition_period: int

    values: dict

    template: str

    disabled: bool = False
    stopped: bool = True

    pm_roll_command: list = ["find", PM_DATA_PATH, "-mindepth", "1", "-mmin", "+1440", "-delete"]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init()

        return cls._instance

    def init(self):
        self.config = Config()
        self.ves = Ves()

        # check pm data path exists
        if not os.path.exists(PM_DATA_PATH):
            logger.warning(f"data path '{PM_DATA_PATH}' does not exist, disabling performance-management")
            self.disabled = True
            return

        # check vsftpd users
        vsftpd_userlist = "/etc/vsftpd.userlist"
        if not os.path.exists(vsftpd_userlist):
            logger.warning(f"vsftpd userlist conf file '{vsftpd_userlist}' does not exist, disabling performance-management")
            self.disabled = True
            return

        # add current user
        with open(vsftpd_userlist, 'w') as file:
            user = self.config.netconf_username
            file.write(f"{user}\n")

        # apply vsftpd changes
        os.system("killall -9 vsftpd")

        # read template from performance-management/template.xml
        template_path = '/data/performance-management/template.xml'
        if Path(template_path).exists():
            with open(template_path, 'r') as file:
                self.template = file.read()
        else:
            logger.warning("template file not found, disabling performance-management")
            self.disabled = True
            return

    def load_data(self, config=None):
        if config is None:
            # read config from performance-management/index.json
            pm_data_path = '/data/performance-management/index.json'
            if Path(pm_data_path).exists():
                # Read and parse the JSON file
                with open(pm_data_path, 'r') as file:
                    config = json.load(file)

                    self.log_period = config["config"]["log-period"]
                    self.repetition_period = config["config"]["repetition-period"]
                    self.points = config["config"]["points"]

                    self.values = config["values"]
            else:
                raise Exception("config file not found, stopping performance-management")

        # checkAL do all checks

        # check repetition and log period
        if self.repetition_period % 60 != 0:
            raise Exception(f"repetition-period {self.repetition_period} must have full minutes")

        if self.repetition_period % self.log_period != 0:
            raise Exception(f"repetition-period {self.repetition_period} must be a multiple of log-period {self.log_period}")

        self.pm_roll_command[5] = "+" + str(int(self.repetition_period / 60))

        # check that values have all the points defined
        for value in self.values:
            for point in self.points:
                if point not in value:
                    raise Exception(f"{point} not found within {value} values; stopping performance-management")

        self.points_id = {}
        counter = 1
        for point in self.points:
            self.points_id[point] = str(counter)
            counter = counter + 1

    def start(self, config=None):
        if self.disabled:
            return

        if self.stopped is False:
            return

        try:
            self.load_data(config)
        except Exception as e:
            logger.error(e)

        # clear stopped
        self.stopped = False
        pm_stop_event.clear()

        # start performance management thread
        logger.info("starting performance management thread...")
        thread = threading.Thread(target=self.performance_management_task)
        thread.start()


    def cleanup_reports(self):
        subprocess.run(self.pm_roll_command)
        logger.info(f"running: {self.pm_roll_command}")


    def generate_report(self, values:list, start_time:datetime, end_time:datetime|None=None) -> dict|None:
        def content() -> str:
            template = self.template

            difference = end_time - start_time
            suspect = False
            if difference.total_seconds() < self.log_period:
                suspect = True
                logger.info(f"suspect true because {difference.total_seconds()} < {self.log_period}")

            suspect_text = ""
            if suspect:
                suspect_text = "<suspect>true</suspect>"

            template = template.replace("@start-time@", start_time.strftime('%Y-%m-%dT%H:%M:%S') + "+00:00")
            template = template.replace("@end-time@",end_time.strftime('%Y-%m-%dT%H:%M:%S') + "+00:00")
            template = template.replace("@suspect@", suspect_text)

            log_period = seconds_to_duration(self.log_period)
            rep_period = seconds_to_duration(self.repetition_period)

            template = template.replace("@log-period@", log_period)
            template = template.replace("@rep-period@", rep_period)

            start_marker = "@point-start@"
            stop_marker = "@point-end@"
            pattern = re.escape(start_marker) + r'(.*?)' + re.escape(stop_marker)
            match = re.search(pattern, template, flags=re.DOTALL)
            point_iter = ""
            if match:
                point_iter = match.group(1)

            replacement = ""
            for point_name in self.points:
                new_point = point_iter
                new_point = new_point.replace("@point-id@", self.points_id[point_name])
                new_point = new_point.replace("@point-name@", point_name)
                replacement += new_point + "\n"
            template = re.sub(pattern, replacement, template, flags=re.DOTALL)


            start_marker = "@value-start@"
            stop_marker = "@value-end@"
            pattern = re.escape(start_marker) + r'(.*?)' + re.escape(stop_marker)
            match = re.search(pattern, template, flags=re.DOTALL)
            point_iter = ""
            if match:
                point_iter = match.group(1)

            replacement = ""
            for point_name in self.points:
                new_point = point_iter
                new_point = new_point.replace("@point-id@", self.points_id[point_name])
                new_point = new_point.replace("@value@", str(values[point_name]))
                replacement += new_point + "\n"
            template = re.sub(pattern, replacement, template, flags=re.DOTALL)

            # other vars and functions
            template = template.replace("@hostname@", self.config.hostname)

            return template

        if end_time is None:
            end_time = datetime_utcnow().replace(microsecond=0)

        filename = "A" + start_time.strftime('%Y%m%d.%H%M') + "+0000-" + end_time.strftime('%H%M') + f"+0000_1_{self.config.hostname}.xml"
        filepath = PM_DATA_PATH + "/" + filename
        filesize = 0
        with open(filepath, 'w') as file:
            filesize = file.write(content())

        expiration = datetime_utcnow() + timedelta(seconds=self.repetition_period)

        return {
            "location": filepath,
            "size": filesize,
            "expiry": expiration
        }

    def performance_management_task(self):
        start_time = datetime_utcnow()
        current_value_index = -1
        while not stop_event.is_set() and not pm_stop_event.is_set():
            now_ts = int(datetime_utcnow().timestamp())

            if now_ts % self.log_period == 0:
                current_value_index = current_value_index + 1
                if current_value_index >= len(self.values):
                    current_value_index = 0

                # generate report
                report = self.generate_report(self.values[current_value_index], start_time)
                start_time = datetime_utcnow().replace(microsecond=0)
                self.cleanup_reports()

                # send VES
                file_ready = VesFileReady(report['location'], report['size'], report['expiry'])
                self.ves.execute(file_ready)

                sa_sleep(1)

            sa_sleep(0.1)

        logger.info("thread finished")
