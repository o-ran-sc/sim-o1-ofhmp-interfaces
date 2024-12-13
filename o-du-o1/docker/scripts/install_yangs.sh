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
"_3gpp-common-yang-extensions.yang"
"_3gpp-common-yang-types.yang"
"_3gpp-common-top.yang"
"_3gpp-common-files.yang"
"_3gpp-common-measurements.yang"
"_3gpp-common-ep-rp.yang"
"_3gpp-common-subscription-control.yang"
"_3gpp-common-fm.yang"
"_3gpp-common-trace.yang"
"_3gpp-5gc-nrm-configurable5qiset.yang"
"_3gpp-5gc-nrm-ecmconnectioninfo.yang"
#"_3gpp-nr-nrm-ecmappingrule.yang"
"_3gpp-common-subnetwork.yang"
"_3gpp-common-managed-element.yang -e FmUnderManagedElement"
"_3gpp-5g-common-yang-types.yang"
"_3gpp-common-managed-function.yang -e MeasurementsUnderManagedFunction"
"_3gpp-common-managementdatacollection.yang"
"_3gpp-common-mnsregistry.yang"
"_3gpp-common-qmcjob.yang"
"_3gpp-nr-nrm-gnbdufunction.yang"
"_3gpp-nr-nrm-gnbcucpfunction.yang"
"_3gpp-nr-nrm-gnbcuupfunction.yang"
"_3gpp-nr-nrm-bwp.yang"
"_3gpp-nr-nrm-nrcelldu.yang"
"_3gpp-nr-nrm-nrsectorcarrier.yang"
"_3gpp-common-filemanagement.yang"
"_3gpp-nr-nrm-ep.yang"
"_3gpp-nr-nrm-rrmpolicy.yang"

"o-ran_3gpp-nr-nrm-gnbdufunction.yang"
"o-ran_3gpp-nr-nrm-nrcelldu.yang"
#"o-ran_3gpp-nr-nrm-rrmpolicy.yang"

"o-ran-operations.yang"
"o-ran-hardware.yang -e ENERGYSAVING"
"o-ran-interfaces.yang"

"o-ran-agg-ald-port.yang"
"o-ran-agg-ald.yang"
"o-ran-agg-antenna-calibration.yang"
"o-ran-agg-beamforming.yang"
"o-ran-agg-dhcp.yang"
"o-ran-agg-ecpri-delay.yang"
"o-ran-agg-ethernet-forwarding.yang"
"o-ran-agg-externalio.yang"
"o-ran-agg-fan.yang"
"o-ran-agg-hardware.yang"
"o-ran-agg-ietf-hardware.yang"
"o-ran-agg-ietf-interfaces.yang"
"o-ran-agg-ietf-ip.yang"
"o-ran-agg-ietf-netconf-acm.yang"
"o-ran-agg-interfaces.yang"
"o-ran-agg-laa-operations.yang"
"o-ran-agg-laa.yang"
"o-ran-agg-lbm.yang"
"o-ran-agg-module-cap.yang"
"o-ran-agg-mplane-int.yang"
"o-ran-agg-operations.yang"
#"o-ran-agg-performance-management.yang"
"o-ran-agg-processing-element.yang"
"o-ran-aggregation-base.yang"
"o-ran-agg-shared-cell.yang"
"o-ran-agg-software-management.yang"
"o-ran-agg-supervision.yang"
"o-ran-agg-transceiver.yang"
"o-ran-agg-udp-echo.yang"
"o-ran-agg-uplane-conf.yang"
"o-ran-agg-usermgmt.yang"
"o-ran-c-plane-tnl.yang"
"o-ran-cti-common.yang"
"o-ran-dhcp.yang"
"o-ran-du-f1-tnl.yang"
"o-ran-du-performance-management.yang"
"o-ran-nr-u.yang"
"o-ran-o1-ctiOdu.yang"
"o-ran-o-du-shared-o-ru.yang"
"o-ran-qos.yang"
"o-ran-rlc.yang"
"o-ran-synchronization.yang"
"o-ran-u-plane-tnl.yang"
"o-ran-usermgmt.yang -I /usr/local/share/yang/modules/pynts/o-ran-usermgmt.xml"
# "o-ran-wg5-delay-management.yang"
"o-ran-wg5-features.yang"
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
