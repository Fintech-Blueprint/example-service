#!/bin/bash

# Script for executing chaos tests on services
# Usage: ./execute_chaos_tests.sh [service-name]

set -euo pipefail

NAMESPACE=${NAMESPACE:-"default"}
SERVICE=${1:-"all"}

# Inject latency
inject_latency() {
  local svc=$1
  local latency=$2
  echo "Injecting ${latency}ms latency to $svc..."
  kubectl apply -f - << EOF
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: ${svc}-latency
spec:
  hosts:
  - ${svc}
  http:
  - fault:
      delay:
        fixedDelay: ${latency}ms
        percentage:
          value: 100
    route:
    - destination:
        host: ${svc}
EOF
}

# Kill pods
kill_pods() {
  local svc=$1
  echo "Executing pod termination for $svc..."
  kubectl get pods -n ${NAMESPACE} -l app=${svc} -o name | \
    shuf -n 1 | \
    xargs kubectl delete -n ${NAMESPACE}
}

# Log results
log_results() {
  local svc=$1
  local test=$2
  local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  mkdir -p evidence/sprint6/chaos
  echo "[${timestamp}] Executed ${test} test on ${svc}" >> evidence/sprint6/chaos/chaos_test_log.txt
}

# Execute tests based on service
if [[ "$SERVICE" == "all" || "$SERVICE" == "service-a" ]]; then
  inject_latency "service-a" 100
  log_results "service-a" "latency"
  kill_pods "service-a"
  log_results "service-a" "pod-kill"
fi

if [[ "$SERVICE" == "all" || "$SERVICE" == "service-b" ]]; then
  inject_latency "service-b" 200
  log_results "service-b" "latency"
  kill_pods "service-b"
  log_results "service-b" "pod-kill"
fi

if [[ "$SERVICE" == "all" || "$SERVICE" == "service-c" ]]; then
  inject_latency "service-c" 150
  log_results "service-c" "latency"
  kill_pods "service-c"
  log_results "service-c" "pod-kill"
fi

# Hash the evidence
if [[ -f "evidence/sprint6/chaos/chaos_test_log.txt" ]]; then
  sha256sum evidence/sprint6/chaos/chaos_test_log.txt > evidence/sprint6/chaos/chaos_test_log.txt.sha256
fi

echo "Chaos tests completed. Results logged to evidence/sprint6/chaos/chaos_test_log.txt"