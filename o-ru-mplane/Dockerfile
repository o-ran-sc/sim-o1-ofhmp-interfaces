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

FROM pynts-base:latest

COPY ./o-ru-mplane/docker/yang /usr/local/share/yang/modules/pynts
COPY ./o-ru-mplane/docker/scripts/install_yangs.sh /opt/dev/scripts/install_yangs.sh

RUN \
    /opt/dev/scripts/install_yangs.sh

COPY ./o-ru-mplane/src /app/extensions/o-ru-mplane
RUN pip install -r /app/extensions/o-ru-mplane/requirements.txt

WORKDIR /app

ENV NETWORK_FUNCTION_TYPE="o-ru-ofmp"
ENV HYBDIR_MPLANE=false

EXPOSE 830
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
