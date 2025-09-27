#!/usr/bin/env bash
set -euo pipefail

# ==============================
# CONFIGURATION (overridable via env)
# ==============================
# Set SPRINT (sprint2 or sprint3) to pick evidence dir; default to sprint2
SPRINT="${SPRINT:-sprint2}"
# Cluster name can be overridden via CLUSTER_NAME env; default follows sprint
CLUSTER_NAME="${CLUSTER_NAME:-${SPRINT}-cluster}"
K8S_VERSION="${K8S_VERSION:-v1.28.0}"
ISTIO_VERSION="${ISTIO_VERSION:-1.20.0}"
NAMESPACE="${NAMESPACE:-default}"
# Evidence dir defaults to evidence/<sprint>
EVIDENCE_DIR="${EVIDENCE_DIR:-evidence/${SPRINT}}"
CONFIG_DIR="${CONFIG_DIR:-config/local}"

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
# Use sprint-specific kind config if present
KIND_CONFIG="${CONFIG_DIR}/kind-config-${SPRINT}.yaml"
if [ -f "$KIND_CONFIG" ]; then
    log_info "Using kind config: $KIND_CONFIG"
    kind create cluster --name "${CLUSTER_NAME}" --config="$KIND_CONFIG"
else
    kind create cluster --name "${CLUSTER_NAME}" --config="${CONFIG_DIR}/kind-config.yaml"
fi

log_info "Waiting for cluster to be ready..."
kubectl cluster-info --context "kind-${CLUSTER_NAME}"
kubectl wait --for=condition=ready nodes --all --timeout=120s

# ==============================
# ISTIO INSTALLATION
# ==============================

log_info "Installing Istio ${ISTIO_VERSION} via Helm (golden path)..."

# Add Istio helm repo
log_info "Adding Istio Helm repository..."
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update

# Create istio-system namespace
kubectl create namespace istio-system 2>/dev/null || true

log_info "Installing Istio base chart..."
helm install istio-base istio/base \
  --namespace istio-system \
  --version "${ISTIO_VERSION}" \
  --wait \
  --timeout 5m || true

sleep 10

log_info "Installing Istiod..."
helm install istiod istio/istiod \
  --namespace istio-system \
  --version "${ISTIO_VERSION}" \
  --wait \
  --timeout 5m || true

# Wait for istiod to be ready
kubectl wait --for=condition=available deployment/istiod -n istio-system --timeout=300s || true

log_info "Installing Istio gateway..."
helm install istio-ingressgateway istio/gateway \
  --namespace istio-system \
  --version "${ISTIO_VERSION}" \
  --wait \
  --timeout 5m || true

# Wait for gateway to be ready
kubectl wait --for=condition=available deployment/istio-ingressgateway -n istio-system --timeout=300s || true

log_info "Collecting final evidence..."

# Save Istio status
TS=$(date +%Y%m%d-%H%M%S)
kubectl get pods -n istio-system -o wide > "${EVIDENCE_DIR}/istio-pods-${TS}.log"
kubectl get events -n istio-system --sort-by=.lastTimestamp | tail -n 50 > "${EVIDENCE_DIR}/istio-events-${TS}.log"

# Save service status and mesh validation
kubectl get pods -n "${NAMESPACE}" -o wide > "${EVIDENCE_DIR}/service-pods-${TS}.log"
kubectl get events -n "${NAMESPACE}" --sort-by=.lastTimestamp | tail -n 50 > "${EVIDENCE_DIR}/service-events-${TS}.log"

# Hash the evidence files
for logfile in "${EVIDENCE_DIR}"/*-"${TS}".log; do
    if [ -f "$logfile" ]; then
        ./scripts/hash-evidence.sh "$logfile" "$(basename "$logfile")" "${SPRINT}"
    fi
done

log_info "Bootstrap complete! Check ${EVIDENCE_DIR} for logs and evidence."# Enable injection for default namespace (best-effort)
if kubectl label namespace default istio-injection=enabled --overwrite >>"$ISTIO_LOG" 2>&1; then
    log_info "Enabled istio-injection on namespace 'default'"
else
    log_warn "Failed to label namespace 'default' for istio-injection (see $ISTIO_LOG)"
fi

# ==============================
# DEPLOY SERVICES
# ==============================
log_info "Deploying services (A, B, C)..."

# Deploy Service-A
log_info "Deploying Service-A..."
helm upgrade --install service-a "${CONFIG_DIR}/services/service-a" \
    --namespace "${NAMESPACE}" \
    --create-namespace \
    --wait \
    --timeout 5m || log_warn "Service-A helm install failed"

# Deploy Service-B
log_info "Deploying Service-B..."
helm upgrade --install service-b "${CONFIG_DIR}/services/service-b" \
    --namespace "${NAMESPACE}" \
    --create-namespace \
    --wait \
    --timeout 5m || log_warn "Service-B helm install failed"

# Deploy Service-C
log_info "Deploying Service-C..."
helm upgrade --install service-c charts/service-c \
    --namespace "${NAMESPACE}" \
    --create-namespace \
    --wait \
    --timeout 5m || log_warn "Service-C helm install failed"

log_info "Waiting for services to be ready..."
for svc in service-a service-b service-c; do
    if kubectl wait --for=condition=available "deployment/${svc}" -n "${NAMESPACE}" --timeout=120s; then
        log_info "${svc} is available"
    else
        log_warn "${svc} did not become available in time"
        kubectl get pods -l "app.kubernetes.io/name=${svc}" -n "${NAMESPACE}" -o wide || true
    fi
done

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

# Ensure evidence dir exists
mkdir -p "${EVIDENCE_DIR}"

# Collect cluster info
# Capture cluster info
kubectl cluster-info dump > "${EVIDENCE_DIR}/cluster-info-$(date +%Y%m%d-%H%M%S).log" 2>&1 || log_warn "cluster-info dump failed"

# Collect Istio status
# istio analysis
istioctl analyze -A > "${EVIDENCE_DIR}/istio-analysis-$(date +%Y%m%d-%H%M%S).log" 2>&1 || log_warn "istioctl analyze failed"

# Collect pod status
# pod status
kubectl get pods -A -o wide > "${EVIDENCE_DIR}/pods-status-$(date +%Y%m%d-%H%M%S).log" 2>&1 || log_warn "kubectl get pods failed"

# Hash the evidence files
if [[ -x scripts/hash-evidence.sh ]]; then
    log_info "Hashing evidence files..."
    for file in "${EVIDENCE_DIR}"/*.log; do
        ./scripts/hash-evidence.sh "$file" "Local mesh setup evidence" "$SPRINT"
    done
fi

# ==============================
# FINAL STATUS
# ==============================
log_info "Local mesh setup complete!"
log_info "Cluster: ${CLUSTER_NAME}"
log_info "Sprint: ${SPRINT}"
log_info "Evidence location: ${EVIDENCE_DIR}/"
log_info "To use the cluster:"
echo "  export KUBECONFIG=$(kind get kubeconfig --name ${CLUSTER_NAME})"
echo "  kubectl get pods -A  # to verify"