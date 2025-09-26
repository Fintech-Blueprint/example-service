# Environment Setup Plan
**Date**: September 25, 2025
**Author**: Dev14-ai
**Purpose**: Establish required environment for service mesh validation

## 1. Infrastructure Requirements

### 1.1 Kubernetes Cluster
```yaml
version: "1.24+"
components:
  - api-server
  - controller-manager
  - scheduler
  - kubelet
  - kube-proxy
resources:
  nodes: 3
  cpu: "4 cores per node"
  memory: "8Gi per node"
  disk: "50Gi per node"
```

### 1.2 Service Mesh (Istio)
```yaml
version: "1.20.0"
components:
  - istiod
  - ingress-gateway
  - egress-gateway
features:
  - mTLS
  - authorization
  - monitoring
```

### 1.3 Monitoring Stack
```yaml
components:
  - prometheus
  - grafana
  - jaeger
storage:
  prometheus: "50Gi"
  grafana: "10Gi"
```

## 2. Setup Steps

### 2.1 Local Development Setup

#### Option 1: Automated Setup (Recommended)
We provide a bootstrap script that sets up the entire local environment:

```bash
# Make the script executable
chmod +x bootstrap-local-mesh.sh

# Run the bootstrap script
./bootstrap-local-mesh.sh
```

The script will:
1. Create a Kind cluster with proper resource allocation
2. Install Istio and all required components
3. Deploy service-a and service-b
4. Run validation scripts
5. Collect and hash evidence

#### Option 2: Manual Setup Steps

1. Create Kind cluster using provided configuration:
   ```bash
   kind create cluster --name sprint2-mesh --config config/local/kind-config.yaml
   ```

2. Alternative: Use Minikube (fallback option)
   ```bash
   minikube start --config config/local/minikube-config.yaml
   ```

3. Verify cluster health:
   ```bash
   kubectl get nodes
   kubectl get componentstatuses
   ```

4. Install Istio components:
   ```bash
   # Add Istio helm repo
   helm repo add istio https://istio-release.storage.googleapis.com/charts
   helm repo update

   # Create namespace
   kubectl create namespace istio-system

   # Install base
   helm install istio-base istio/base -n istio-system --version 1.20.0

   # Install istiod
   helm install istiod istio/istiod -n istio-system --version 1.20.0

   # Install gateway
   helm install istio-ingress istio/gateway -n istio-system --version 1.20.0
   ```

5. Enable Istio injection:
   ```bash
   kubectl label namespace default istio-injection=enabled
   ```

6. Deploy services:
   ```bash
   # Deploy service-a
   helm upgrade --install service-a config/local/services/service-a \
     --namespace default \
     --create-namespace

   # Deploy service-b
   helm upgrade --install service-b config/local/services/service-b \
     --namespace default \
     --create-namespace
   ```

### 2.2 Required Tools Setup

1. Install kubectl
   ```bash
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   chmod +x kubectl
   sudo mv kubectl /usr/local/bin/
   ```

2. Install Helm
   ```bash
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
   ```

3. Install istioctl
   ```bash
   curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.0 sh -
   cd istio-1.20.0
   sudo mv bin/istioctl /usr/local/bin/
   ```

### 2.2 Kubernetes Setup

#### Production Setup
1. Ensure cluster meets minimum specifications:
   - 3 nodes (1 control plane, 2 workers)
   - 4 CPU cores per node
   - 8 GB RAM per node
   - 50 GB disk per node

2. Verify cluster health
   ```bash
   kubectl get nodes -o wide
   kubectl get componentstatuses
   ```

#### Fallback Development Setup

If managed cluster is delayed, use one of these local alternatives:

##### Option 1: Minikube
```bash
minikube start \
  --cpus=4 \
  --memory=8192 \
  --disk-size=50g \
  --kubernetes-version=v1.28.0 \
  --driver=docker

# Enable ingress addon
minikube addons enable ingress
```

##### Option 2: Kind
Create kind configuration (kind-config.yaml):
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
kind create cluster --config kind-config.yaml
```

3. Setup default namespaces
   ```bash
   kubectl create ns service-a
   kubectl create ns service-b
   kubectl create ns monitoring
   ```

### 2.3 Istio Installation
1. Install Istio with default profile
   ```bash
   istioctl install --set profile=default -y
   ```

2. Enable automatic sidecar injection
   ```bash
   kubectl label namespace default istio-injection=enabled
   ```

3. Verify Istio installation
   ```bash
   istioctl verify-install
   kubectl get pods -n istio-system
   istioctl proxy-status
   ```

### 2.3 Monitoring Setup
1. Deploy Prometheus
   ```bash
   kubectl apply -f monitoring/prometheus/
   ```

2. Deploy Grafana
   ```bash
   kubectl apply -f monitoring/grafana/
   ```

3. Configure service monitors
   ```bash
   kubectl apply -f monitoring/service-monitors/
   ```

## 3. Validation Steps

### 3.1 Service Mesh Validation
```bash
# Check mTLS status
istioctl analyze

# Verify PeerAuthentication
kubectl get peerauthentication -A

# Check AuthorizationPolicy
kubectl get authorizationpolicy -A
```

### 3.2 Service Deployment
```bash
# Deploy services
kubectl apply -f services/service-a/
kubectl apply -f services/service-b/

# Verify deployments
kubectl get deployments -n service-a
kubectl get deployments -n service-b
```

### 3.3 Monitoring Validation
```bash
# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Access http://localhost:9090/targets

# Check Grafana dashboards
kubectl port-forward -n monitoring svc/grafana 3000:3000
# Access http://localhost:3000
```

## 4. Required Credentials

### 4.1 Kubernetes
```yaml
type: kubeconfig
location: ~/.kube/config
permissions: cluster-admin
```

### 4.2 Container Registry
```yaml
type: docker-registry
credentials: service-account
permissions: push/pull
```

## 5. Expected Outcomes

### 5.1 Kubernetes
- All nodes Ready
- All components healthy
- Namespaces created

### 5.2 Service Mesh
- Istio control plane operational
- mTLS enforced
- Authorization policies active

### 5.3 Monitoring
- Prometheus collecting metrics
- Grafana dashboards available
- Service metrics visible

## 6. Backup Plan

### 6.1 Local Development
```yaml
alternatives:
  - minikube
  - kind
  - k3d
requirements:
  cpu: "8 cores"
  memory: "16Gi"
  disk: "100Gi"
```

### 6.2 Minimal Setup
```yaml
components:
  required:
    - kubernetes-core
    - istio-minimal
    - prometheus
  optional:
    - grafana
    - jaeger
```

## 7. Timeline

### 7.1 Expected Setup Time
- Kubernetes: 30 minutes
- Istio: 20 minutes
- Monitoring: 15 minutes
- Validation: 30 minutes
**Total**: ~2 hours

### 7.2 Contingency
Add 1 hour for troubleshooting and optimization

## 8. Support Requirements

### 8.1 Team Access
- DevOps team for cluster setup
- Security team for policy review
- SRE team for monitoring setup

### 8.2 Documentation
- Cluster access guide
- Mesh policy documentation
- Monitoring dashboard guide

## 9. Next Steps

1. Request cluster provisioning
2. Prepare validation scripts
3. Schedule setup window
4. Coordinate with security team