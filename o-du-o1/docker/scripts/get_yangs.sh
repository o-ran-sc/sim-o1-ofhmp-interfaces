#!/bin/bash

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

DIRBIN="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DIR_AVAILABLE_YANGS="$DIRBIN/available-yangs"
DIR_YANGS="/usr/local/share/yang/modules/pynts"
FILE_DOWNLOADZIP="/opt/dev/yangs.zip"
TMPFOLDER="/tmp/o1-yangs"
UNZIP=$(which unzip)
if [ -z "$UNZIP" ]; then
    echo "unable to find unzip. please install."
    exit 1
fi

# download
if [ ! -f "$FILE_DOWNLOADZIP" ]; then
    # latest commit, working since 2024-01-17
    wget --no-check-certificate -O "$FILE_DOWNLOADZIP" "https://forge.3gpp.org/rep/sa5/MnS/-/archive/Tag_Rel18_SA103/MnS-Tag_Rel18_SA103.zip?path=yang-models"

    # latest release
    # wget --no-check-certificate -O "$FILE_DOWNLOADZIP" "https://forge.3gpp.org/rep/sa5/MnS/-/archive/Tag_Rel17_SA96/MnS-Tag_Rel17_SA96.zip?path=yang-models"
fi
if [ ! -d "$DIR_AVAILABLE_YANGS" ]; then
    mkdir "$DIR_AVAILABLE_YANGS"
fi
# cleanup yang folders
rm -rf "$DIR_AVAILABLE_YANGS/"*
unzip -uj yangs.zip -d "$TMPFOLDER"
cp -r "$TMPFOLDER/"* "$DIR_AVAILABLE_YANGS/"

rm "$FILE_DOWNLOADZIP"

# fill yang folder
cp "$DIR_AVAILABLE_YANGS/"_3gpp-common*.yang "$DIR_YANGS"
cp "$DIR_AVAILABLE_YANGS/"ietf-*.yang "$DIR_YANGS/"

declare special_files=(
    "_3gpp-5g-common-yang-types.yang"
    "_3gpp-5gc-nrm-configurable5qiset.yang"
    "_3gpp-5gc-nrm-ecmconnectioninfo.yang"
    "_3gpp-nr-nrm-bwp.yang"
    "_3gpp-nr-nrm-ep.yang"
    "_3gpp-nr-nrm-gnbcucpfunction.yang"
    "_3gpp-nr-nrm-gnbcuupfunction.yang"
    "_3gpp-nr-nrm-gnbdufunction.yang"
    "_3gpp-nr-nrm-nrsectorcarrier.yang"
    "_3gpp-nr-nrm-nrcelldu.yang"
    "_3gpp-nr-nrm-rrmpolicy.yang"
    "_3gpp-nr-nrm-nrcellcu.yang"
    #"_3gpp-nr-nrm-ecmappingrule.yang"
)

for file in "${special_files[@]}"
do
   cp "$DIR_AVAILABLE_YANGS/$file" "$DIR_YANGS/"
done
