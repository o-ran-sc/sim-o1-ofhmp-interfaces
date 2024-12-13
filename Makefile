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

.PHONY: k8s-infra
k8s-infra:
	sudo apt-get update && sudo apt-get upgrade -y
	sudo snap install microk8s --classic --channel=${MICRO_K8S_VERSION}
	sudo usermod -a -G microk8s ${USER}
	sudo chown -f -R ${USER} ~/.kube
	microk8s status --wait-ready
	microk8s enable dns
	microk8s enable storage
	microk8s enable registry
	
	sudo snap install kubectl --classic || true
	microk8s kubectl get pods -A


.PHONY: clean-k8s-infra
clean-k8s-infra:
	sudo microk8s reset
	sudo snap remove microk8s
# /k8s-minikube:
# 	sudo apt-get update && sudo apt-get upgrade -y
# 	sudo apt-get install -y apt-transport-https ca-certificates curl conntrack
	
# 	curl -LO "https://github.com/kubernetes-sigs/cri-tools/releases/download/${K8S_VERSION}/crictl-${K8S_VERSION}-linux-amd64.tar.gz"
# 	sudo tar -C /usr/local/bin -xzvf crictl-${K8S_VERSION}-linux-amd64.tar.gz
# 	crictl --version
# 	rm crictl-${K8S_VERSION}-linux-amd64.tar.gz

# 	curl -LO "https://github.com/Mirantis/cri-dockerd/releases/download/v0.3.15/cri-dockerd_0.3.15.3-0.ubuntu-jammy_amd64.deb"
# 	sudo dpkg -i cri-dockerd_0.3.15.3-0.ubuntu-jammy_amd64.deb
# 	rm cri-dockerd_0.3.15.3-0.ubuntu-jammy_amd64.deb


# 	curl -LO "https://github.com/containernetworking/plugins/releases/download/${CNI_PLUGIN_VERSION}/cni-plugins-linux-amd64-${CNI_PLUGIN_VERSION}.tgz"
# 	sudo mkdir -p "/opt/cni/bin"
# 	sudo tar -xf "cni-plugins-linux-amd64-${CNI_PLUGIN_VERSION}.tgz" -C "/opt/cni/bin"
# 	rm "cni-plugins-linux-amd64-${CNI_PLUGIN_VERSION}.tgz"

# 	curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
# 	sudo install minikube-linux-amd64 /usr/local/bin/minikube
# 	curl -LO "https://dl.k8s.io/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"
# 	chmod +x kubectl
# 	sudo mv kubectl /usr/local/bin/
# 	minikube start --kubernetes-version=${K8S_VERSION}
# 	kubectl get nodes
# 	touch $@
	
