# /*************************************************************************
# *
# * Copyright 2025 highstreet technologies GmbH and others
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

FROM pynts-base:latest

RUN apt-get update && DEBIAN_FRONTEND="noninteractive" apt-get install -y \
  # basic tools
  wget && \
  apt-get clean && \
  rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

COPY ./o-du-o1/docker/yang /usr/local/share/yang/modules/pynts
COPY ./o-du-o1/docker/scripts/install_yangs.sh /opt/dev/scripts/install_yangs.sh

# get and install required YANG libraries
COPY ./o-du-o1/docker/scripts/get_yangs.sh /opt/dev/scripts/get_yangs.sh
RUN \
  /opt/dev/scripts/get_yangs.sh

RUN \
  /opt/dev/scripts/install_yangs.sh

COPY ./o-du-o1/docker/conf/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY ./o-du-o1/src /app/extensions/o-du-o1
RUN pip install -r /app/extensions/o-du-o1/requirements.txt

WORKDIR /app

ENV NETWORK_FUNCTION_TYPE="o-du-o1"

EXPOSE 830
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
