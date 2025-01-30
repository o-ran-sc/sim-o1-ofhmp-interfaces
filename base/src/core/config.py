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

from typing import Optional
from util.logging import get_pynts_logger
import os
import sys

from strenum import StrEnum
from util.docker import get_hostname, get_ip_from_env

logger = get_pynts_logger("config")

"""
Configuration class
Singleton
----
Builds config from:
- environment variables
- JSON config
- Netconf datastore
"""
class Config:
    _instance = None

    # environment variables
    network_function_type: str = "undefined"

    ssh_listen_endpoint: bool = True
    tls_listen_endpoint: bool = False
    ssh_callhome_endpoint: bool = False
    tls_callhome_endpoint: bool = False

    ssh_listen_port: int = 830      # default value, currently unmodifiable by env
    tls_listen_port: int = 6513     # default value, currently unmodifiable by env

    sftp_listen_port: int = 22      # default valuem currently unmodifiable by env

    netconf_username: str = "netconf"
    netconf_password: str = "netconf!"

    sdnr_username: str = "admin"
    sdnr_password: str = "admin"

    sdnr_restconf_url: str

    ves_url: str
    ves_username: str
    ves_password: str

    # json variables

    # netconf variables
    hostname: str = get_hostname()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.reload()
        return cls._instance

    def reload(self) -> None:
        logger.info("reloading config")

        self.netconf_function_type: str = os.environ.get("NETWORK_FUNCTION_TYPE", "undefined")

        self.ssh_listen_endpoint: bool = self.get_envvar_bool("SSH_LISTEN_ENDPOINT", "True")
        self.tls_listen_endpoint: bool = self.get_envvar_bool("TLS_LISTEN_ENDPOINT", "False")
        self.ssh_callhome_endpoint: bool = self.get_envvar_bool("SSH_CALLHOME_ENDPOINT", "False")
        self.tls_callhome_endpoint: bool = self.get_envvar_bool("TLS_CALLHOME_ENDPOINT", "False")

        endpoints = os.environ.get("ENDPOINT_COUNT", 1)
        try:
            self.endpoint_count: int = int(endpoints)
        except ValueError:
            logger.error(f"Got config ENDPOINT_COUNT=f{endpoints}, which is not integer. Defaulted to 1 endpoint count.")
            self.endpoint_count = 1

        self.netconf_username: str = os.environ.get("NETCONF_USERNAME", "netconf")
        self.netconf_password: str = os.environ.get("NETCONF_PASSWORD", "netconf!")

        self.sdnr_restconf_url: str = os.environ.get("SDNR_RESTCONF_URL", "")
        self.sdnr_username: str = os.environ.get("SDNR_USERNAME", "admin")
        self.sdnr_password: str = os.environ.get("SDNR_PASSWORD", "admin")

        self.ves_url = os.environ.get("VES_URL", "")
        self.ves_username = os.environ.get("VES_USERNAME", "sample1")
        self.ves_password = os.environ.get("VES_PASSWORD", "sample1")

    @staticmethod
    def get_envvar_bool(varname: str, default_value: str) -> bool:
        truthy_values = {'true', '1', 't', 'y', 'yes'}

        value = os.environ.get(varname, default_value)

        return value.lower() in truthy_values

    def is_tls_enabled(self) -> bool:
        return self.tls_listen_endpoint or self.tls_callhome_endpoint

    # def only_one_connection_type(self) -> bool:
    #     only_one_listen_true = sum([self.ssh_listen_endpoint, self.tls_listen_endpoint]) == 2
    #     only_one_callhome_true = sum([self.ssh_callhome_endpoint, self.tls_callhome_endpoint]) == 2
    #     if only_one_listen_true or only_one_callhome_true:
    #         logger.error(f"Expecting only one type of connection (either SSH or TLS, but not both) at the same time! Got SSH_ENDPOINT={self.ssh_listen_endpoint}, TLS_ENDPOINT={self.tls_listen_endpoint}, SSH_CALLHOME={self.ssh_callhome_endpoint} and TLS_CALLHOME={self.tls_callhome_endpoint}. Please re-check the config!")
    #         sys.exit("Invalid configuration for the SSH and TLS endpoints.")

    def to_dict(self) -> dict:
        return {
            "ssh_listen_endpoint": self.ssh_listen_endpoint,
            "tls_listen_endpoint": self.tls_listen_endpoint,

            "ssh_callhome_endpoint": self.ssh_callhome_endpoint,
            "tls_callhome_endpoint": self.tls_callhome_endpoint,

            "endpoint_count": self.endpoint_count,

            "netconf_username": self.netconf_username,
            "netconf_password": self.netconf_password,

            "sdnr_restconf_url": self.sdnr_restconf_url,
            "sdnr_username": self.sdnr_username,
            "sdnr_password": self.sdnr_password
        }
