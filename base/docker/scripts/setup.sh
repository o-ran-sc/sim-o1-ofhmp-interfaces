#!/usr/bin/env bash

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

# env variables NP2_MODULE_DIR, NP2_MODULE_PERMS and LN2_MODULE_DIR must be defined
# and NP2_MODULE_OWNER, NP2_MODULE_GROUP will be used if defined when executing this script!

if [ -z "$NP2_MODULE_DIR" -o -z "$NP2_MODULE_PERMS" -o -z "$LN2_MODULE_DIR" -o -z "$PYNTS_MODULE_DIR" ]; then
    echo "Required environment variables not defined!"
    exit 1
fi

# import functions and modules arrays
script_directory=$(dirname "$0")
source "${script_directory}/common.sh"

# get path to sysrepoctl executable, this will be stored in $SYSREPOCTL
SYSREPOCTL_GET_PATH

NP2_MODDIR=${DESTDIR}${NP2_MODULE_DIR}
LN2_MODDIR=${DESTDIR}${LN2_MODULE_DIR}
PYNTS_MODDIR=${DESTDIR}${PYNTS_MODULE_DIR}

# get current modules
SCTL_MODULES=`$SYSREPOCTL -l`

# the install command will be stored in this variable
CMD_INSTALL=

# setup the cmd for install, modules are listed in common.sh
SETUP_CMD "$NP2_MODDIR" "${NP2_MODULES[@]}"

SETUP_CMD "$LN2_MODDIR" "${LN2_MODULES[@]}"

SETUP_CMD "$PYNTS_MODDIR" "${PYNTS_MODULES[@]}"

# install all the new modules
if [ ! -z "${CMD_INSTALL}" ]; then
    eval $CMD_INSTALL
    rc=$?
    if [ $rc -ne 0 ]; then
        exit $rc
    fi
fi
