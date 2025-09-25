# Environment Setup Requirements

## Resource Requirements

### Minimum Cluster Specifications
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB per node
- Nodes: 3 (1 control plane, 2 worker nodes)

### Required Software Versions
- Kubernetes: ≥ 1.28
- Helm: ≥ 3.12
- Istio: 1.20.0
- kubectl: matching cluster version

## Installation Steps

### 1. Required Tools Setup

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install istioctl
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.0 sh -
cd istio-1.20.0
sudo mv bin/istioctl /usr/local/bin/
```

### 2. Managed Kubernetes Cluster Setup

Ensure the cluster meets minimum specifications:
```bash
# Verify node resources
kubectl get nodes -o wide
kubectl describe nodes
```

### 3. Istio Installation

```bash
# Install Istio with default profile
istioctl install --set profile=default -y

# Enable automatic sidecar injection for default namespace
kubectl label namespace default istio-injection=enabled

# Verify installation
istioctl verify-install
```

## Fallback Development Setup

If managed Kubernetes cluster setup is delayed, use one of the following local alternatives:

### Option 1: Minikube

```bash
# Start minikube with required resources
minikube start \
  --cpus=4 \
  --memory=8192 \
  --disk-size=50g \
  --kubernetes-version=v1.28.0 \
  --driver=docker

# Enable ingress addon
minikube addons enable ingress
```

### Option 2: Kind

Create kind configuration file (kind-config.yaml):
```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
```

Create cluster:
```bash
# Install kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/

# Create cluster
kind create cluster --config kind-config.yaml
```

## Validation

After setup, validate the environment:

```bash
# Check Kubernetes
kubectl get nodes
kubectl get pods -A

# Check Istio
istioctl proxy-status
kubectl get pods -n istio-system
```

## Notes
- All commands assume Linux/Unix environment
- For Windows, adjust paths and commands accordingly
- Ensure firewall rules allow required ports
- Resource requirements are minimums - production may need more