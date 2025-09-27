#!/bin/bash
set -euo pipefail

# Setup script for monitoring stack deployment
NAMESPACE=${1:-"monitoring"}

echo "Setting up monitoring stack in namespace: $NAMESPACE"

# Create namespace if it doesn't exist
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Add Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Prometheus Operator
echo "Installing Prometheus Operator..."
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace "$NAMESPACE" \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false

# Wait for Prometheus to be ready
kubectl wait --for=condition=available --timeout=300s deployment/prometheus-kube-prometheus-operator -n "$NAMESPACE"
kubectl wait --for=condition=available --timeout=300s deployment/prometheus-grafana -n "$NAMESPACE"

# Apply our custom Prometheus rules
echo "Applying custom Prometheus rules..."
kubectl apply -f monitoring/prometheus/rules/ -n "$NAMESPACE"

# Deploy Grafana dashboards
echo "Deploying Grafana dashboards..."
for dashboard in monitoring/grafana/dashboards/*.json; do
  name=$(basename "$dashboard" .json)
  kubectl create configmap "grafana-dashboard-${name}" \
    --from-file="$dashboard" \
    --dry-run=client -o yaml | \
    kubectl apply -f - -n "$NAMESPACE"
done

# Label the namespace for Istio injection
kubectl label namespace "$NAMESPACE" istio-injection=enabled --overwrite

echo "Monitoring stack setup complete!"
echo "Access Grafana:"
echo "kubectl port-forward svc/prometheus-grafana 3000:80 -n $NAMESPACE"
echo "Default credentials:"
echo "Username: admin"
echo "Password: prom-operator"

# Create evidence directory
mkdir -p evidence/sprint6/monitoring
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Save setup evidence
cat << EOF > "evidence/sprint6/monitoring/setup_${timestamp}.json"
{
  "timestamp": "${timestamp}",
  "namespace": "${NAMESPACE}",
  "components": {
    "prometheus": "installed",
    "grafana": "installed",
    "customRules": "applied",
    "dashboards": "configured"
  },
  "status": "completed"
}
EOF

# Generate hash
sha256sum "evidence/sprint6/monitoring/setup_${timestamp}.json" > "evidence/sprint6/monitoring/setup_${timestamp}.json.sha256"

# Update evidence chain
cat << EOF >> EVIDENCE_CHAIN.md

## Monitoring Stack Setup ${timestamp}
- Namespace: ${NAMESPACE}
- Status: ✅ Completed
- File: setup_${timestamp}.json
- SHA256: $(cat "evidence/sprint6/monitoring/setup_${timestamp}.json.sha256")
EOF