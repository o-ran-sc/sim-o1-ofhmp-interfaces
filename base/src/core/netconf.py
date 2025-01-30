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

from util.logging import get_pynts_logger, get_pynts_log_level
import logging
from strenum import StrEnum
import sysrepo
from sysrepo.session import SysrepoSession
import json
import os
import re

logger = get_pynts_logger("netconf")

class Datastore(StrEnum):
    RUNNING = "running"
    OPERATIONAL = "operational"

class Netconf:
    _instance = None

    connection:sysrepo.SysrepoConnection
    running: SysrepoSession
    operational: SysrepoSession

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            sysrepo.configure_logging(
                stderr_level=logging.INFO,
                # stderr_level=get_pynts_log_level(),
                # syslog_level=get_pynts_log_level(),
                # syslog_app_name="sysrepo",
                py_logging=True,
            )
            cls._instance.connect()

        return cls._instance

    def connect(self) -> None:
        logger.info("connecting to sysrepo")
        self.connection = sysrepo.SysrepoConnection()
        self.running = self.connection.start_session(datastore="running")
        self.operational = self.connection.start_session(datastore="operational")
        logger.info("connected to sysrepo")

    def disconnect(self) -> None:
        self.connection.disconnect()
        logger.info("disconnected from sysrepo")

    def set_data(self, datastore: Datastore, xpath: str | None, data: dict | str, default_operation: str = "merge") -> None:
        if xpath is None or xpath == "":
            logger.info("setting multiple modules at once")
            for module in data:
                self.set_data(datastore, module, data[module], f"!{default_operation}")
        else:
            if xpath.endswith("/"):
                xpath = xpath[:-1]

            logger.info(f"setting {datastore}:'{xpath}'")
            logger.debug(f"to '{data}'")

            if type(data) is str:
                if datastore == Datastore.RUNNING:
                    self.running.set_item(xpath, data)
                elif datastore == Datastore.OPERATIONAL:
                    self.operational.set_item(xpath, data)
                else:
                    raise Exception(f"invalid datastore {datastore}")

            elif type(data) is dict:
                oper = default_operation
                if oper.startswith("!"):
                    oper = oper[1:]

                if xpath.startswith("/"):
                    xpath = xpath[1:]

                if datastore == Datastore.RUNNING:
                    self.running.edit_batch(data, xpath, default_operation=oper)
                elif datastore == Datastore.OPERATIONAL:
                    self.operational.edit_batch(data, xpath, default_operation=oper)
                else:
                    raise Exception(f"invalid datastore {datastore}")

        if not default_operation.startswith("!"):
            logger.info(f"applying datastore {datastore} changes")
            if datastore == Datastore.RUNNING:
                self.running.apply_changes()
            elif datastore == Datastore.OPERATIONAL:
                self.operational.apply_changes()
            else:
                raise Exception(f"invalid datastore {datastore}")

    def get_data(self, datastore: Datastore, xpath: str) -> dict:
        if datastore == Datastore.RUNNING:
            return self.running.get_data(xpath)
        elif datastore == Datastore.OPERATIONAL:
            return self.operational.get_data(xpath)
        else:
            raise Exception(f"invalid datastore {datastore}")


    def set_data_from_path(self, datastore: Datastore, module_name: str, format: str, file_path: str) -> None:
        logger.debug(f"Loading {format} data for {module_name} in datastore {datastore} from file {file_path}")
        with open(file_path, 'r') as file:

            if datastore == Datastore.OPERATIONAL:
                with self.connection.start_session("operational") as sess:
                    with self.connection.get_ly_ctx() as ctx:
                        data = ctx.parse_data_file(file, format, parse_only=True)
                        sess.edit_batch_ly(data)
                        sess.apply_changes()
            elif datastore == Datastore.RUNNING:
                with self.connection.start_session("running") as sess:
                    try:
                      data = sess.get_data(f"/{module_name}:*")
                    except sysrepo.SysrepoNotFoundError:
                      logger.debug(f"Did not find data for /{module_name}:*")
                      data = None
                    if not data:
                      with self.connection.get_ly_ctx() as ctx:
                          data = ctx.parse_data_file(file, format, parse_only=True)
                          # start with a fresh datastore, erase anything that was before
                          # sess.copy_config("startup", module_name)
                          sess.edit_batch_ly(data)
                          sess.apply_changes()      
                    else:
                      logger.debug(f"Skipping loading data from file {file_path} into module {module_name}. Data already present...")

    @staticmethod
    def get_datastore_files(directory: str, filter=None) -> list:
        extensions = ['json', 'xml']
        if filter is not None:
            extensions = filter.split("|")

        extensions_pattern = '|'.join(extensions)
        pattern_string = r'^(.+)-(running|operational)\.(' + extensions_pattern + ')$'
        pattern = re.compile(pattern_string)

        # Dictionary to store results
        results = []

        # Iterate over files in the specified directory
        for filename in os.listdir(directory):
            # Check if the filename matches the expected pattern
            match = pattern.match(filename)
            if match:
                # Extract parts of the filename
                module_name, datastore, extension = match.groups()
                # Append the results
                results.append({
                    'filename': f"{directory}/{filename}",
                    'module_name': module_name,
                    'datastore': datastore,
                    'extension': extension
                })

        def is_top_condition(entry) -> bool:
            return entry['module_name'] == "ietf-yang-schema-mount"

        top_entries = [entry for entry in results if is_top_condition(entry)]
        other_entries = [entry for entry in results if not is_top_condition(entry)]

        ordered_results = top_entries + other_entries

        return ordered_results
