#!/bin/bash
set -euo pipefail

SPRINT=${SPRINT:-sprint5}
EVIDENCE_DIR=${EVIDENCE_DIR:-evidence/$SPRINT}
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

# Function to log and hash evidence
log_and_hash() {
    local file="$1"
    local desc="$2"
    ./scripts/hash-evidence.sh "$file" "$desc" "$SPRINT"
}

# Function to check error rate
check_error_rate() {
    local error_rate=$(kubectl -n monitoring exec -c prometheus-server deploy/prometheus-server -- wget -qO- --post-data='query=sum(rate(istio_requests_total{destination_service="service-b",response_code=~"5.*"}[5m]))/sum(rate(istio_requests_total{destination_service="service-b"}[5m]))' http://localhost:9090/api/v1/query | jq -r '.data.result[0].value[1]')
    
    if (( $(echo "$error_rate > 0.01" | bc -l) )); then
        echo "Error rate $error_rate exceeds threshold 0.01"
        return 1
    fi
    return 0
}

# Function to check latency
check_latency() {
    local current_p95=$(kubectl -n monitoring exec -c prometheus-server deploy/prometheus-server -- wget -qO- --post-data='query=histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket{destination_service="service-b"}[5m])) by (le))' http://localhost:9090/api/v1/query | jq -r '.data.result[0].value[1]')
    
    local baseline_p95=$(kubectl -n monitoring exec -c prometheus-server deploy/prometheus-server -- wget -qO- --post-data='query=histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket{destination_service="service-b"}[1h] offset 1h)) by (le))' http://localhost:9090/api/v1/query | jq -r '.data.result[0].value[1]')
    
    if (( $(echo "$current_p95 > $baseline_p95 * 1.2" | bc -l) )); then
        echo "P95 latency $current_p95 exceeds baseline $baseline_p95 by more than 20%"
        return 1
    fi
    return 0
}

echo "Starting Sprint 5 implementation..."

# 1. Enable Prometheus PVC
echo "Upgrading Prometheus with PVC..."
helm upgrade --install prometheus prometheus-community/prometheus \
    -f sprint5/05-monitoring/prometheus-values-pvc.yaml \
    --namespace monitoring --create-namespace \
    --wait 2>&1 | tee "$EVIDENCE_DIR/prometheus-pvc-upgrade-$TIMESTAMP.log"
log_and_hash "$EVIDENCE_DIR/prometheus-pvc-upgrade-$TIMESTAMP.log" "prometheus pvc upgrade"

# 2. Apply Prometheus alert rules
echo "Applying alert rules..."
kubectl apply -f sprint5/04-alerts/prometheus-rules.yaml 2>&1 | tee "$EVIDENCE_DIR/prometheus-rules-$TIMESTAMP.log"
log_and_hash "$EVIDENCE_DIR/prometheus-rules-$TIMESTAMP.log" "prometheus alert rules"

# 3. Create Grafana dashboard
echo "Creating Grafana dashboard..."
kubectl -n monitoring create configmap grafana-dashboards \
    --from-file=golden-signals.json=sprint5/06-grafana/dashboards/golden-signals.json \
    --dry-run=client -o yaml | kubectl apply -f - 2>&1 | tee "$EVIDENCE_DIR/grafana-dashboard-$TIMESTAMP.log"
log_and_hash "$EVIDENCE_DIR/grafana-dashboard-$TIMESTAMP.log" "grafana dashboard"

# 4. Collect baseline metrics
echo "Collecting baseline metrics..."
kubectl -n monitoring exec -c prometheus-server deploy/prometheus-server -- wget -qO- http://localhost:9090/api/v1/query?query=histogram_quantile\(0.95,\ sum\(rate\(istio_request_duration_milliseconds_bucket\{destination_service=\"service-b\"\}\[1h\]\)\)\ by\ \(le\)\) > "$EVIDENCE_DIR/baseline-latency-$TIMESTAMP.json"
log_and_hash "$EVIDENCE_DIR/baseline-latency-$TIMESTAMP.json" "baseline latency metrics"

# 5. Deploy initial canary (90/10)
echo "Deploying canary 90/10 split..."
kubectl apply -f sprint5/03-canary/canary-rollout.yaml 2>&1 | tee "$EVIDENCE_DIR/canary-initial-$TIMESTAMP.log"
log_and_hash "$EVIDENCE_DIR/canary-initial-$TIMESTAMP.log" "initial canary deployment"

# 6. Run synthetic traffic
echo "Running synthetic traffic tests..."
kubectl run -n default load-test --image=grafana/k6 --restart=Never --command -- k6 run - <<EOF
import http from 'k6/http';
import { check, sleep } from 'k6';

export default function () {
    let res = http.get('http://service-b:8080/api/test');
    check(res, { 'status was 200': (r) => r.status == 200 });
    sleep(0.1);
}

export let options = {
    vus: 20,
    duration: '5m'
};
EOF

# Wait for load test to complete and collect results
kubectl wait --for=condition=completed pod/load-test --timeout=360s
kubectl logs load-test > "$EVIDENCE_DIR/load-test-initial-$TIMESTAMP.log"
log_and_hash "$EVIDENCE_DIR/load-test-initial-$TIMESTAMP.log" "initial load test"

# 7. Apply fault injection
echo "Applying fault injection..."
kubectl apply -f sprint5/01-fault-injection/istio-fault-injection.yaml 2>&1 | tee "$EVIDENCE_DIR/fault-injection-$TIMESTAMP.log"
log_and_hash "$EVIDENCE_DIR/fault-injection-$TIMESTAMP.log" "fault injection applied"

# 8. Run chaos tests
echo "Running chaos tests..."
bash sprint5/02-chaos/chaos-scripts.sh

# 9. Progressive canary promotion
echo "Starting progressive canary promotion..."

# Update to 50/50
sed -i 's/weight: 90/weight: 50/g; s/weight: 10/weight: 50/g' sprint5/03-canary/canary-rollout.yaml
kubectl apply -f sprint5/03-canary/canary-rollout.yaml

echo "Waiting 3 minutes for 50/50 validation..."
sleep 180

if check_error_rate && check_latency; then
    echo "50/50 validation passed, promoting to 100% v2..."
    
    # Update to 100/0
    sed -i 's/weight: 50/weight: 0/g; s/weight: 50/weight: 100/g' sprint5/03-canary/canary-rollout.yaml
    kubectl apply -f sprint5/03-canary/canary-rollout.yaml
    
    echo "Waiting 3 minutes for final validation..."
    sleep 180
    
    if check_error_rate && check_latency; then
        echo "Full promotion successful!" | tee "$EVIDENCE_DIR/canary-promotion-success-$TIMESTAMP.log"
        log_and_hash "$EVIDENCE_DIR/canary-promotion-success-$TIMESTAMP.log" "canary promotion success"
    else
        echo "Final validation failed, rolling back..." | tee "$EVIDENCE_DIR/canary-rollback-$TIMESTAMP.log"
        kubectl apply -f sprint5/03-canary/canary-rollout.yaml
        log_and_hash "$EVIDENCE_DIR/canary-rollback-$TIMESTAMP.log" "canary rollback to 50/50"
    fi
else
    echo "50/50 validation failed, rolling back..." | tee "$EVIDENCE_DIR/canary-rollback-$TIMESTAMP.log"
    # Restore 90/10
    sed -i 's/weight: 50/weight: 90/g; s/weight: 50/weight: 10/g' sprint5/03-canary/canary-rollout.yaml
    kubectl apply -f sprint5/03-canary/canary-rollout.yaml
    log_and_hash "$EVIDENCE_DIR/canary-rollback-$TIMESTAMP.log" "canary rollback to 90/10"
fi

# 10. Export final dashboard and metrics
echo "Collecting final evidence..."

# Export Grafana dashboard
kubectl -n monitoring get configmap grafana-dashboards -o json | jq '.data."golden-signals.json"' > "$EVIDENCE_DIR/final-dashboard-$TIMESTAMP.json"
log_and_hash "$EVIDENCE_DIR/final-dashboard-$TIMESTAMP.json" "final grafana dashboard"

# Export Prometheus config and rules
kubectl -n monitoring get configmap prometheus-server -o yaml > "$EVIDENCE_DIR/final-prometheus-config-$TIMESTAMP.yaml"
log_and_hash "$EVIDENCE_DIR/final-prometheus-config-$TIMESTAMP.yaml" "final prometheus config"

echo "Sprint 5 implementation complete. Check $EVIDENCE_DIR for all evidence files."