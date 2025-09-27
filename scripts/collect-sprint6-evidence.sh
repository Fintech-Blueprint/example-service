#!/bin/bash
# Automated evidence collection for Sprint 6

# Set up variables
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EVIDENCE_DIR="/workspaces/example-service/evidence/sprint6/${TIMESTAMP}"
PROMETHEUS_URL="http://prometheus:9090"

# Create evidence directory
mkdir -p "${EVIDENCE_DIR}/metrics"
mkdir -p "${EVIDENCE_DIR}/chaos"
mkdir -p "${EVIDENCE_DIR}/traffic"

# Collect Prometheus metrics
echo "Collecting metrics snapshots..."
curl -s "${PROMETHEUS_URL}/api/v1/query?query=histogram_quantile(0.95,sum(rate(istio_request_duration_milliseconds_bucket{}[5m]))by(le,destination_service))" > "${EVIDENCE_DIR}/metrics/latency.json"
curl -s "${PROMETHEUS_URL}/api/v1/query?query=sum(rate(istio_requests_total{}[5m]))by(destination_service,response_code)" > "${EVIDENCE_DIR}/metrics/requests.json"

# Collect traffic split status
echo "Collecting traffic distribution..."
kubectl get virtualservice -o yaml > "${EVIDENCE_DIR}/traffic/virtualservice-state.yaml"
kubectl get destinationrule -o yaml > "${EVIDENCE_DIR}/traffic/destinationrule-state.yaml"

# Collect chaos test results
echo "Collecting chaos test results..."
kubectl get events --field-selector reason=ChaosInjected -o yaml > "${EVIDENCE_DIR}/chaos/chaos-events.yaml"

# Hash the evidence
cd "${EVIDENCE_DIR}" && find . -type f -exec sha256sum {} \; > checksums.txt

# Update evidence chain
echo "Updating evidence chain..."
{
  echo "## Sprint 6 Evidence - ${TIMESTAMP}"
  echo "### Metrics Collection"
  echo "- Location: evidence/sprint6/${TIMESTAMP}/metrics/"
  echo "- Files: latency.json, requests.json"
  echo "### Traffic Management"
  echo "- Location: evidence/sprint6/${TIMESTAMP}/traffic/"
  echo "- Files: virtualservice-state.yaml, destinationrule-state.yaml"
  echo "### Chaos Testing"
  echo "- Location: evidence/sprint6/${TIMESTAMP}/chaos/"
  echo "- Files: chaos-events.yaml"
  echo "### Evidence Hash"
  echo "\`\`\`"
  cat checksums.txt
  echo "\`\`\`"
  echo
} >> /workspaces/example-service/EVIDENCE_CHAIN.md

echo "Evidence collection complete at ${TIMESTAMP}"