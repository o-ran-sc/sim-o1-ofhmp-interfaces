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


# common.sh - contains common functions and variables for the scripts

# arrays of modules to (un)install
NP2_MODULES=(
"ietf-interfaces@2018-02-20.yang"
"ietf-ip@2018-02-22.yang"
"ietf-netconf@2013-09-29.yang -e writable-running -e candidate -e rollback-on-error -e validate -e startup -e url -e xpath -e confirmed-commit"
"ietf-netconf-nmda@2019-01-07.yang -e origin -e with-defaults"
"notifications@2008-07-14.yang"
"nc-notifications@2008-07-14.yang"
"ietf-netconf-monitoring@2010-10-04.yang"
"ietf-network-instance@2019-01-21.yang"
"ietf-subscribed-notifications@2019-09-09.yang -e encode-xml -e replay -e subtree -e xpath"
"ietf-yang-push@2019-09-09.yang -e on-change"
)

LN2_MODULES=(
"iana-ssh-encryption-algs@2022-06-16.yang"
"iana-ssh-key-exchange-algs@2022-06-16.yang"
"iana-ssh-mac-algs@2022-06-16.yang"
"iana-ssh-public-key-algs@2022-06-16.yang"
"iana-tls-cipher-suite-algs@2022-06-16.yang"
"ietf-x509-cert-to-name@2014-12-10.yang"
"iana-crypt-hash@2014-04-04.yang -e crypt-hash-md5 -e crypt-hash-sha-256 -e crypt-hash-sha-512"
"ietf-crypto-types@2023-12-28.yang -e cleartext-passwords -e cleartext-private-keys -e certificate-expiration-notification"
"ietf-keystore@2023-12-28.yang -e central-keystore-supported -e inline-definitions-supported -e asymmetric-keys"
"ietf-truststore@2023-12-28.yang -e central-truststore-supported -e inline-definitions-supported -e certificates -e public-keys"
"ietf-tcp-common@2023-12-28.yang -e keepalives-supported"
"ietf-tcp-server@2023-12-28.yang -e tcp-server-keepalives"
"ietf-tcp-client@2023-12-28.yang -e local-binding-supported -e tcp-client-keepalives"
"ietf-ssh-common@2023-12-28.yang -e transport-params"
"ietf-ssh-server@2023-12-28.yang -e local-users-supported -e local-user-auth-publickey -e local-user-auth-password -e local-user-auth-none -e ssh-server-keepalives"
"ietf-tls-common@2023-12-28.yang -e tls10 -e tls11 -e tls12 -e tls13 -e hello-params"
"ietf-tls-server@2023-12-28.yang -e server-ident-x509-cert -e client-auth-supported -e client-auth-x509-cert -e tls-server-keepalives"
"ietf-netconf-server@2023-12-28.yang -e ssh-listen -e tls-listen -e ssh-call-home -e tls-call-home -e central-netconf-server-supported"
"libnetconf2-netconf-server@2024-07-09.yang"
)

PYNTS_MODULES=(
"iana-if-type.yang"
"iana-hardware.yang"
"ietf-inet-types.yang"
"ietf-hardware.yang -e hardware-state"
"ietf-system.yang"
"ieee802-dot1q-types.yang"
"ieee802-dot1x-types.yang"
"ieee802-dot1q-cfm-types.yang"
"ieee802-types.yang"
"ieee802-dot1q-cfm.yang"
"ieee802-dot1x.yang"
"ietf-datastores.yang"
"ietf-dhcpv6-common.yang"
"ietf-dhcpv6-types.yang"
"ietf-netconf-acm.yang"
"ietf-netconf-notifications.yang"
"ietf-restconf.yang"
"ietf-yang-library.yang"
"ietf-yang-schema-mount.yang"
"ietf-yang-types.yang"

"onap-system.yang"
)

PERMS=${NP2_MODULE_PERMS}
OWNER=${NP2_MODULE_OWNER}
GROUP=${NP2_MODULE_GROUP}

# get path to the sysrepocfg executable
function SYSREPOCFG_GET_PATH() {
    if [ -n "$SYSREPOCFG_EXECUTABLE" ]; then
        # from env
        SYSREPOCFG="$SYSREPOCFG_EXECUTABLE"
    elif [ $(id -u) -eq 0 ] && [ -n "$USER" ] && [ $(command -v su) ]; then
        # running as root, avoid problems with sudo PATH
        SYSREPOCFG=$(su -c 'command -v sysrepocfg' -l "$USER")
    else
        # normal user
        SYSREPOCFG=$(command -v sysrepocfg)
    fi

    if [ -z "$SYSREPOCFG" ]; then
        echo "$0: Unable to find sysrepocfg executable." >&2
        exit 1
    fi
}

# get path to the sysrepoctl executable
function SYSREPOCTL_GET_PATH() {
    if [ -n "$SYSREPOCTL_EXECUTABLE" ]; then
        # from env
        SYSREPOCTL="$SYSREPOCTL_EXECUTABLE"
    elif [ $(id -u) -eq 0 ] && [ -n "$USER" ] && [ $(command -v su) ]; then
        # running as root, avoid problems with sudo PATH
        SYSREPOCTL=$(su -c 'command -v sysrepoctl' -l "$USER")
    else
        # normal user
        SYSREPOCTL=$(command -v sysrepoctl)
    fi

    if [ -z "$SYSREPOCTL" ]; then
        echo "$0: Unable to find sysrepoctl executable." >&2
        exit 1
    fi
}

# get path to the openssl executable
function OPENSSL_GET_PATH() {
    if [ -n "$OPENSSL_EXECUTABLE" ]; then
        # from env
        OPENSSL="$OPENSSL_EXECUTABLE"
    elif [ $(id -u) -eq 0 ] && [ -n "$USER" ] && [ $(command -v su) ]; then
        # running as root, avoid problems with sudo PATH
        OPENSSL=$(su -c 'command -v openssl' -l "$USER")
    else
        # normal user
        OPENSSL=$(command -v openssl)
    fi

    if [ -z "$OPENSSL" ]; then
        echo "$0: Unable to find sysrepoctl executable." >&2
        exit 1
    fi
}

# functions
function INSTALL_MODULE_CMD() {
    if [ -z "${CMD_INSTALL}" ]; then
        CMD_INSTALL="'$SYSREPOCTL' -s '$1' -v2"
    fi

    CMD_INSTALL="$CMD_INSTALL -i $1/$2 -p '$PERMS'"
    if [ ! -z "${OWNER}" ]; then
        CMD_INSTALL="$CMD_INSTALL -o '$OWNER'"
    fi
    if [ ! -z "${GROUP}" ]; then
        CMD_INSTALL="$CMD_INSTALL -g '$GROUP'"
    fi
}

function UPDATE_MODULE() {
    CMD="'$SYSREPOCTL' -U $1/$2 -s '$1' -v2"
    eval "$CMD"
    local rc=$?
    if [ $rc -ne 0 ]; then
        exit $rc
    fi
}

function CHANGE_PERMS() {
    CMD="'$SYSREPOCTL' -c $1 -p '$PERMS' -v2"
    if [ ! -z "${OWNER}" ]; then
        CMD="$CMD -o '$OWNER'"
    fi
    if [ ! -z "${GROUP}" ]; then
        CMD="$CMD -g '$GROUP'"
    fi

    eval "$CMD"
    local rc=$?
    if [ $rc -ne 0 ]; then
        exit $rc
    fi
}

function ENABLE_FEATURE() {
    "$SYSREPOCTL" -c $1 -e $2 -v2
    local rc=$?
    if [ $rc -ne 0 ]; then
        exit $rc
    fi
}

function SETUP_CMD() {
    module_dir="$1"     # first argument - module directory
    shift               # shift all args to the left
    modules=("$@")      # the rest of the arguments are module names (and their features)
    for i in "${modules[@]}"; do
        name=$(echo "$i" | sed 's/\([^@]*\).*/\1/')
        sctl_module=$(echo "$SCTL_MODULES" | grep "^$name \+|[^|]*| I")
        if [ -z "$sctl_module" ]; then
            # prepare command to install module with all its features
            INSTALL_MODULE_CMD "$module_dir" "$i"
            continue
        fi

        sctl_revision=$(echo "$sctl_module" | sed 's/[^|]*| \([^ ]*\).*/\1/')
        revision=$(echo "$i" | sed 's/[^@]*@\([^\.]*\).*/\1/')
        if [ "$sctl_revision" \< "$revision" ]; then
            # update module without any features
            file=$(echo "$i" | cut -d' ' -f 1)
            UPDATE_MODULE "$module_dir" "$file"
        fi

        sctl_owner=$(echo "$sctl_module" | sed 's/\([^|]*|\)\{3\} \([^:]*\).*/\2/')
        sctl_group=$(echo "$sctl_module" | sed 's/\([^|]*|\)\{3\}[^:]*:\([^ ]*\).*/\2/')
        sctl_perms=$(echo "$sctl_module" | sed 's/\([^|]*|\)\{4\} \([^ ]*\).*/\2/')
        if [ "$sctl_perms" != "$PERMS" ] || [ ! -z "${OWNER}" -a "$sctl_owner" != "$OWNER" ] || [ ! -z "${GROUP}" -a "$sctl_group" != "$GROUP" ]; then
            # change permissions/owner
            CHANGE_PERMS "$name"
        fi

        # parse sysrepoctl features and add extra space at the end for easier matching
        sctl_features="`echo "$sctl_module" | sed 's/\([^|]*|\)\{6\}\(.*\)/\2/'` "
        # parse features we want to enable
        features=$(echo "$i" | sed 's/[^ ]* \(.*\)/\1/')
        while [ "${features:0:3}" = "-e " ]; do
            # skip "-e "
            features=${features:3}
            # parse feature
            feature=$(echo "$features" | sed 's/\([^[:space:]]*\).*/\1/')

            # enable feature if not already
            sctl_feature=$(echo "$sctl_features" | grep " ${feature} ")
            if [ -z "$sctl_feature" ]; then
                # enable feature
                ENABLE_FEATURE $name $feature
            fi

            # next iteration, skip this feature
            features=$(echo "$features" | sed 's/[^[:space:]]* \(.*\)/\1/')
        done
    done
}
