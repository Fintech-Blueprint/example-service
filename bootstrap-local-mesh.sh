#!/usr/bin/env bash
set -euo pipefail

# ==============================
# CONFIGURATION
# ==============================
CLUSTER_NAME="sprint2-mesh"
K8S_VERSION="v1.28.0"
ISTIO_VERSION="1.20.0"
NAMESPACE="default"
EVIDENCE_DIR="evidence/mesh"
CONFIG_DIR="config/local"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ==============================
# HELPER FUNCTIONS
# ==============================
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    command -v "$1" >/dev/null 2>&1 || { 
        log_error "$1 not installed. Please install $1 first."; 
        exit 1; 
    }
}

# ==============================
# PRE-CHECKS
# ==============================
log_info "Checking prerequisites..."
check_command kind
check_command kubectl
check_command helm
check_command istioctl

# Create necessary directories
mkdir -p "${EVIDENCE_DIR}"
mkdir -p "${CONFIG_DIR}/services"

# ==============================
# KIND CLUSTER SETUP
# ==============================
if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
    log_warn "Cluster ${CLUSTER_NAME} already exists. Deleting..."
    kind delete cluster --name "${CLUSTER_NAME}"
fi

log_info "Creating Kind cluster ${CLUSTER_NAME}..."
kind create cluster --name "${CLUSTER_NAME}" --config="${CONFIG_DIR}/kind-config.yaml"

log_info "Waiting for cluster to be ready..."
kubectl cluster-info --context "kind-${CLUSTER_NAME}"
kubectl wait --for=condition=ready nodes --all --timeout=120s

# ==============================
# ISTIO INSTALLATION
# ==============================
log_info "Installing Istio ${ISTIO_VERSION}..."

# Add Istio helm repo
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update

# Install Istio base
log_info "Installing Istio base..."
helm install istio-base istio/base \
    --namespace istio-system \
    --create-namespace \
    --version "${ISTIO_VERSION}" \
    --wait

# Install Istiod
log_info "Installing Istiod..."
helm install istiod istio/istiod \
    --namespace istio-system \
    --version "${ISTIO_VERSION}" \
    --wait

# Install Istio Ingress Gateway
log_info "Installing Istio Ingress Gateway..."
helm install istio-ingress istio/gateway \
    --namespace istio-system \
    --version "${ISTIO_VERSION}" \
    --wait

# Enable injection for default namespace
kubectl label namespace default istio-injection=enabled --overwrite

# ==============================
# DEPLOY SERVICES
# ==============================
log_info "Deploying Service-A and Service-B..."

# Deploy Service-A
log_info "Deploying Service-A..."
helm upgrade --install service-a "${CONFIG_DIR}/services/service-a" \
    --namespace "${NAMESPACE}" \
    --create-namespace \
    --wait

# Deploy Service-B
log_info "Deploying Service-B..."
helm upgrade --install service-b "${CONFIG_DIR}/services/service-b" \
    --namespace "${NAMESPACE}" \
    --create-namespace \
    --wait

log_info "Waiting for services to be ready..."
kubectl wait --for=condition=available deployment/service-a-deployment --timeout=120s
kubectl wait --for=condition=available deployment/service-b-deployment --timeout=120s

# ==============================
# VALIDATION
# ==============================
log_info "Running validation scripts..."

# Run mTLS validation
if [[ -x tests/mesh/check-mtls.sh ]]; then
    log_info "Running mTLS validation..."
    ./tests/mesh/check-mtls.sh | tee "${EVIDENCE_DIR}/mtls-$(date +%Y%m%d-%H%M%S).log"
else
    log_warn "mTLS validation script not found or not executable"
fi

# Run RBAC validation
if [[ -x tests/mesh/check-rbac.sh ]]; then
    log_info "Running RBAC validation..."
    ./tests/mesh/check-rbac.sh | tee "${EVIDENCE_DIR}/rbac-$(date +%Y%m%d-%H%M%S).log"
else
    log_warn "RBAC validation script not found or not executable"
fi

# ==============================
# EVIDENCE COLLECTION
# ==============================
log_info "Collecting evidence..."

# Collect cluster info
kubectl cluster-info dump > "${EVIDENCE_DIR}/cluster-info-$(date +%Y%m%d-%H%M%S).log"

# Collect Istio status
istioctl analyze -A > "${EVIDENCE_DIR}/istio-analysis-$(date +%Y%m%d-%H%M%S).log"

# Collect pod status
kubectl get pods -A -o wide > "${EVIDENCE_DIR}/pods-status-$(date +%Y%m%d-%H%M%S).log"

# Hash the evidence files
if [[ -x scripts/hash-evidence.sh ]]; then
    log_info "Hashing evidence files..."
    for file in "${EVIDENCE_DIR}"/*.log; do
        ./scripts/hash-evidence.sh "$file" "Local mesh setup evidence"
    done
fi

# ==============================
# FINAL STATUS
# ==============================
log_info "Local mesh setup complete!"
log_info "Cluster: ${CLUSTER_NAME}"
log_info "Evidence location: ${EVIDENCE_DIR}/"
log_info "To use the cluster:"
echo "  export KUBECONFIG=$(kind get kubeconfig --name ${CLUSTER_NAME})"
echo "  kubectl get pods -A  # to verify"