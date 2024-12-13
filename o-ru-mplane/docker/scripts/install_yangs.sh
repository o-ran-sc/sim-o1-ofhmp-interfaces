#!/usr/bin/env bash

# /*************************************************************************
# *
# * Copyright 2024 highstreet technologies GmbH and others
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

if [ -z "$NP2_MODULE_PERMS"  -o -z "$PYNTS_MODULE_DIR" ]; then
    echo "Required environment variables not defined!"
    exit 1
fi

# import functions and modules arrays
script_directory=$(dirname "$0")
source "${script_directory}/common.sh"

# array of modules to install
MODULES=(
"o-ran-ald.yang"
"o-ran-ald-port.yang"
"o-ran-antenna-calibration.yang"
"o-ran-beamforming.yang"
"o-ran-certificates.yang"
"o-ran-common-identity-refs.yang"
"o-ran-common-yang-types.yang"
"o-ran-compression-factors.yang"
"o-ran-delay-management.yang"
"o-ran-dhcp.yang"
"o-ran-ecpri-delay.yang"
"o-ran-ethernet-forwarding.yang"
"o-ran-externalio.yang"
"o-ran-fan.yang"
"o-ran-file-management.yang"
"o-ran-fm.yang"
"o-ran-hardware.yang -e ENERGYSAVING"
"o-ran-ieee802-dot1q-cfm.yang"
"o-ran-interfaces.yang"
"o-ran-laa.yang"
"o-ran-laa-operations.yang"
"o-ran-lbm.yang"
"o-ran-module-cap.yang"
"o-ran-mplane-int.yang"
"o-ran-operations.yang"
"o-ran-performance-management.yang"
"o-ran-processing-element.yang"
"o-ran-shared-cell.yang"
"o-ran-software-management.yang"
"o-ran-supervision.yang"
"o-ran-sync.yang"
"o-ran-trace.yang"
"o-ran-transceiver.yang"
"o-ran-troubleshooting.yang"
"o-ran-udp-echo.yang"
"o-ran-uplane-conf.yang"
"o-ran-usermgmt.yang -I /usr/local/share/yang/modules/pynts/o-ran-usermgmt.xml"
"o-ran-ves-subscribed-notifications.yang"
"o-ran-wg4-features.yang"
)

# get path to sysrepoctl executable, this will be stored in $SYSREPOCTL
SYSREPOCTL_GET_PATH

PYNTS_MODDIR=${DESTDIR}${PYNTS_MODULE_DIR}

# get current modules
SCTL_MODULES=`$SYSREPOCTL -l`

# the install command will be stored in this variable
CMD_INSTALL=

SETUP_CMD "$PYNTS_MODDIR" "${MODULES[@]}"

# install all the new modules
if [ ! -z "${CMD_INSTALL}" ]; then
    eval $CMD_INSTALL
    rc=$?
    if [ $rc -ne 0 ]; then
        exit $rc
    fi
fi
