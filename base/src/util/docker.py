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

import os
import fcntl
import re
import socket
import struct

def get_network_interface_name() -> str:
    return os.environ.get("NETWORK_INTERFACE", "eth0")

def get_hostname() -> str:
    return os.environ.get("HOSTNAME", get_container_ip())

def get_container_ip() -> str:
    ifname = get_network_interface_name()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', bytes(ifname, 'utf-8')[:15]))
    return socket.inet_ntoa(info[20:24])

def get_container_mac_address() -> str:
    ifname = get_network_interface_name()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', bytes(ifname, 'utf-8')[:15]))
    return ':'.join('%02x' % b for b in info[18:24])


def is_valid_ip(ip):
    # Regex to check if it's a valid IPv4 address
    ipv4_regex = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    # Regex to check if it's a valid IPv6 address
    ipv6_regex = r"^(([0-9a-fA-F]{1,4}:){7}([0-9a-fA-F]{1,4}|:)|(([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6}))|:((:[0-9a-fA-F]{1,4}){1,7}|:))(\%[0-9a-zA-Z]{1,})?)$"

    return re.match(ipv4_regex, ip) is not None or re.match(ipv6_regex, ip) is not None


def get_ip_from_env(env_var_name: str, ipv6_enabled: bool = False, default_value: str = "172.60.0.71"):
    value = os.getenv(env_var_name)
    
    if value is None:
        return default_value #  TODO need to log error
    
    if is_valid_ip(value):
        return value
    else:
        try:
            # Get all the address information associated with the FQDN
            addr_info = socket.getaddrinfo(value, None)
            # Filter for the first IPv6 or IPv4 address
            for result in addr_info:
                if result[0] == (socket.AF_INET6 if ipv6_enabled else socket.AF_INET):
                    return result[4][0]
        except socket.gaierror:
            return default_value # TODO need to log error



# def get_container_ip() -> str:
#     try:
#         ip_address = subprocess.check_output(["hostname", "-i"]).decode().strip()
#     except subprocess.CalledProcessError as e:
#         ip_address = "Unable to determine IP address: " + str(e)
#     return ip_address
