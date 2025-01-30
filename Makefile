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

include .env
export

.PHONY: build-all
build-all: build-o-ru-mplane build-o-du-o1

.PHONY: build-o-ru-mplane
build-o-ru-mplane: build-image-base
	docker build -f o-ru-mplane/Dockerfile -t pynts-o-ru-mplane:${NTS_VERSION} -t pynts-o-ru-mplane:latest .

.PHONY: build-o-du-o1
build-o-du-o1: build-image-base
	docker build -f o-du-o1/Dockerfile -t pynts-o-du-o1:${NTS_VERSION} -t pynts-o-du-o1:latest .

.PHONY: build-image-base
build-image-base:
	docker build -f base/Dockerfile -t pynts-base:${NTS_VERSION} -t pynts-base:latest .

.PHONY: clean-image-base
clean-image-base:
	docker rmi pynts-base:latest || true
