#!/bin/bash
set -euo pipefail

# Create namespace and install monitoring
echo "Installing Prometheus and Grafana..."
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Create dashboard ConfigMap
kubectl -n monitoring create configmap grafana-dashboards \
  --from-file=/workspaces/example-service/charts/monitoring/dashboards/service-b.json \
  --dry-run=client -o yaml | kubectl apply -f -

# Add Helm repos
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Prometheus
helm upgrade --install prometheus prometheus-community/prometheus \
  -n monitoring \
  -f charts/monitoring/values-prometheus.yaml --wait

# Install Grafana
helm upgrade --install grafana grafana/grafana \
  -n monitoring \
  -f charts/monitoring/values-grafana.yaml --wait

# Deploy Service B v2 and traffic rules
echo "Deploying Service B v2 and traffic management..."

# Apply DestinationRule first
kubectl apply -f charts/service-b/templates/istio/destination-rule.yaml

# Deploy Service B v2
kubectl apply -f charts/service-b/templates/deployment-v2.yaml

# Apply VirtualService
kubectl apply -f charts/service-b/templates/istio/virtual-service.yaml

# Create evidence directory
mkdir -p evidence/sprint4

# Collect Prometheus targets
echo "Collecting Prometheus targets..."
kubectl -n monitoring exec deploy/prometheus-server -- \
  curl -sS http://localhost:9090/api/v1/targets | jq '.' \
  > evidence/sprint4/$(date -u +%Y%m%dT%H%M%SZ)-prometheus-targets.log

./scripts/hash-evidence.sh evidence/sprint4/$(date -u +%Y%m%dT%H%M%SZ)-prometheus-targets.log "Prometheus targets" sprint4

# Create and run tester pod
echo "Running canary distribution test..."
kubectl run -n default tester --image=curlimages/curl:7.86.0 --restart=Never --command -- sleep 3600

# Wait for pod
kubectl wait --for=condition=ready pod/tester --timeout=60s

# Run test
kubectl exec -n default pod/tester -- sh -c 'for i in $(seq 1 200); do curl -s http://service-b:8080/which-version; done' | sort | uniq -c \
  > evidence/sprint4/$(date -u +%Y%m%dT%H%M%SZ)-canary-distribution.log

./scripts/hash-evidence.sh evidence/sprint4/$(date -u +%Y%m%dT%H%M%SZ)-canary-distribution.log "Canary distribution sample" sprint4

# Query Prometheus for canary ratio
echo "Collecting Prometheus metrics..."
kubectl -n monitoring exec deploy/prometheus-server -- \
  curl -sG 'http://localhost:9090/api/v1/query' --data-urlencode 'query=sum(rate(istio_requests_total{destination_workload="service-b",destination_version="v2"}[1m]))' \
  > evidence/sprint4/$(date -u +%Y%m%dT%H%M%SZ)-prometheus-canary-v2.log

./scripts/hash-evidence.sh evidence/sprint4/$(date -u +%Y%m%dT%H%M%SZ)-prometheus-canary-v2.log "Prometheus canary v2 rate" sprint4

# Save Grafana dashboard for evidence
kubectl -n monitoring get configmap grafana-dashboards -o jsonpath='{.data.service-b\.json}' \
  > evidence/sprint4/$(date -u +%Y%m%dT%H%M%SZ)-grafana-dashboard-service-b.json

./scripts/hash-evidence.sh evidence/sprint4/$(date -u +%Y%m%dT%H%M%SZ)-grafana-dashboard-service-b.json "Grafana dashboard config" sprint4

# Cleanup
kubectl delete pod/tester --ignore-not-found

echo "Done! Check evidence/sprint4/ for results."