#!/usr/bin/env bash

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
"ietf-alarms.yang"
"ietf-alarms-x733.yang"
"ietf-interface-protection.yang"
"ietf-microwave-radio-link.yang -e xpic -e mimo"
"ietf-microwave-types.yang"
"bbf-yang-types.yang"
"bbf-hardware.yang -e interface-hardware-reference -e interface-hardware-management"
"bbf-alarm-types.yang"
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
