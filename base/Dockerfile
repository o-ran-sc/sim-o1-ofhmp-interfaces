# syntax=docker/dockerfile:1

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

FROM ubuntu:22.04

RUN apt-get update && DEBIAN_FRONTEND="noninteractive" apt-get install -y \
  # basic tools
  tzdata build-essential git cmake pkg-config \
  # libyang dependencies
  libpcre2-dev \
  # libnetconf dependencies
  libssh-dev libssl-dev libcurl4-openssl-dev libpam-dev \
  # python bindings dependencies
  python3-dev python3-cffi python3-pip \
  # supervisor
  supervisor psmisc \
  # unzip
  unzip \
  # ftpd related
  openssl openssh-client openssh-server \
  vsftpd \
  && \
  apt-get clean && \
  rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

# add netconf user and configure access
RUN \
  adduser --system netconf && \
  groupadd -f netconf && \
  echo "netconf:netconf!" | chpasswd

# FTP and SFTP configuration
RUN \
  mkdir /ftp && \
  chown -R netconf /ftp && \
  mkdir /var/run/vsftpd && \
  mkdir /var/run/vsftpd/empty  && \
  mkdir /run/sshd && \
  echo "Match User netconf\n    ChrootDirectory /\n    X11Forwarding no\n    AllowTcpForwarding no\n    ForceCommand internal-sftp -d /ftp" >> /etc/ssh/sshd_config

COPY ./base/docker/conf/vsftpd.conf /etc/vsftpd.conf
COPY ./base/docker/conf/vsftpd.userlist /etc/vsftpd.userlist

# use /opt/dev as working directory
RUN mkdir /opt/dev
WORKDIR /opt/dev

# get required build libs from git
RUN \
  git config --global advice.detachedHead false && \
  git clone --single-branch --branch v3.4.2 https://github.com/CESNET/libyang.git && \
  # git clone --single-branch --branch v3.0.0 https://github.com/CESNET/libyang-python.git && \
  git clone --single-branch --branch master https://github.com/CESNET/libyang-python.git && \
  git clone --single-branch --branch v2.11.7 https://github.com/sysrepo/sysrepo.git && \
  git clone --single-branch --branch v1.7.3 https://github.com/sysrepo/sysrepo-python.git && \
  git clone --single-branch --branch v3.5.1 https://github.com/CESNET/libnetconf2.git && \
  git clone --single-branch --branch v2.2.31 https://github.com/CESNET/netopeer2.git

# build and install libyang
RUN \
  cd libyang && \
  mkdir build && cd build  && \
  cmake -DCMAKE_BUILD_TYPE:String="Debug" -DENABLE_BUILD_TESTS=OFF .. && \
  make -j4  && \
  make install && \
  ldconfig

# install libyang python bindings
RUN \
  cd libyang-python && \
  git reset --hard 012d144 && \
  pip3 install .

# build and install sysrepo
COPY ./base/docker/conf/pynts-sysrepo.patch /opt/dev/sysrepo/pynts-sysrepo.patch
RUN \
  cd sysrepo && \
  git apply pynts-sysrepo.patch && \
  mkdir build && cd build  && \
  cmake -DCMAKE_BUILD_TYPE:String="Debug" -DENABLE_TESTS=OFF -DNACM_RECOVERY_USER=root .. && \
  make -j4 && \
  make install && \
  ldconfig

# install sysrepo python bindings
COPY ./base/docker/conf/pynts-sysrepo-python.patch /opt/dev/sysrepo-python/pynts-sysrepo-python.patch
RUN \
  cd sysrepo-python && \
  git apply pynts-sysrepo-python.patch && \
  pip3 install .

# build and install libnetconf2
RUN \
  cd libnetconf2 && \
  mkdir build && cd build && \
  cmake -DCMAKE_BUILD_TYPE:String="Debug" -DENABLE_BUILD_TESTS=OFF .. && \
  make -j4 && \
  make install && \
  ldconfig

# build and install netopeer2
COPY ./base/docker/conf/pynts-netopeer2.patch /opt/dev/netopeer2/pynts-netopeer2.patch
RUN \
  cd netopeer2 && \
  git apply pynts-netopeer2.patch && \
  mkdir build && cd build && \
  cmake -DCMAKE_BUILD_TYPE:String="Debug" -DSYSREPO_SETUP=OFF .. && \
  make -j4 && \
  make install

ENV NP2_MODULE_PERMS=600
ENV NP2_MODULE_DIR=/usr/local/share/yang/modules/netopeer2/
ENV LN2_MODULE_DIR=/usr/local/share/yang/modules/libnetconf2/
ENV PYNTS_MODULE_DIR=/usr/local/share/yang/modules/pynts/

COPY ./base/docker/conf/ODU_rootCA.key /home/oranuser/.ssh/ODU_rootCA.key
COPY ./base/docker/conf/ODU_rootCA.crt /home/oranuser/.ssh/ODU_rootCA.crt
COPY ./base/docker/conf/ODU_client.key /home/oranuser/.ssh/ODU_client.key
COPY ./base/docker/conf/ODU_client.crt /home/oranuser/.ssh/ODU_client.crt
COPY ./base/docker/conf/SMO_rootCA.key /home/oranuser/.ssh/SMO_rootCA.key
COPY ./base/docker/conf/SMO_rootCA.crt /home/oranuser/.ssh/SMO_rootCA.crt
COPY ./base/docker/conf/end_odu_openssl.cnf /home/oranuser/.ssh/end_odu_openssl.cnf

COPY ./base/docker/yang /usr/local/share/yang/modules/pynts/
COPY ./base/docker/scripts /opt/dev/scripts
RUN \
  /opt/dev/scripts/setup.sh

COPY ./base/docker/conf/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# copy base code
COPY ./base/src /app

# install requirements
RUN pip install -r /app/requirements.txt

ENV NETWORK_FUNCTION_TYPE="undefined"
ENV NETCONF_USERNAME="netconf"
ENV NETCONF_PASSWORD="netconf!"
