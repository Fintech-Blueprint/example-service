#!/bin/bash
set -euo pipefail

EVIDENCE_DIR=${EVIDENCE_DIR:-evidence/sprint5}
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

# Function to log and hash evidence
log_and_hash() {
    local file="$1"
    local desc="$2"
    ./scripts/hash-evidence.sh "$file" "$desc" sprint5
}

# 1. Pod Kill Test
echo "Starting pod kill test for service-a..."
POD_NAME=$(kubectl get pods -l app=service-a -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod "$POD_NAME" --grace-period=0 --force 2>&1 | tee "$EVIDENCE_DIR/chaos-pod-kill-$TIMESTAMP.log"
log_and_hash "$EVIDENCE_DIR/chaos-pod-kill-$TIMESTAMP.log" "service-a pod kill test"

# Wait for new pod
kubectl wait --for=condition=ready pod -l app=service-a --timeout=60s

# 2. Network Delay Test (using debug pod with tc)
echo "Starting network delay test..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: network-delay-test
  labels:
    app: network-delay-test
spec:
  containers:
  - name: network-tools
    image: nicolaka/netshoot
    command: ["sleep", "3600"]
    securityContext:
      privileged: true
EOF

kubectl wait --for=condition=ready pod/network-delay-test --timeout=60s

# Apply network delay
kubectl exec network-delay-test -- tc qdisc add dev eth0 root netem delay 100ms 2>&1 | tee "$EVIDENCE_DIR/chaos-network-delay-$TIMESTAMP.log"
log_and_hash "$EVIDENCE_DIR/chaos-network-delay-$TIMESTAMP.log" "network delay test"

# 3. Generate traffic during chaos
echo "Generating traffic..."
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

# Wait for load test to complete
kubectl wait --for=condition=completed job/load-test --timeout=360s

# Collect load test logs
kubectl logs load-test > "$EVIDENCE_DIR/chaos-load-test-$TIMESTAMP.log"
log_and_hash "$EVIDENCE_DIR/chaos-load-test-$TIMESTAMP.log" "chaos load test results"

# Cleanup
kubectl delete pod network-delay-test --grace-period=0 --force
kubectl delete pod load-test --ignore-not-found