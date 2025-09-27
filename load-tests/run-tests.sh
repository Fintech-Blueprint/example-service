#!/bin/bash
set -euo pipefail

# Run load tests and validate against thresholds
SERVICE_URL=${1:-"http://localhost:8000"}
SCENARIO=${2:-"standard"}

echo "Running load tests against $SERVICE_URL with scenario $SCENARIO"

# Configure k6 with environment variables
export K6_PROMETHEUS_RW_SERVER_URL=http://prometheus:9090/api/v1/write
export K6_PROMETHEUS_RW_TREND_STATS="p(95),p(99),avg,med,min,max"

# Run load test
k6 run \
    --tag scenario=$SCENARIO \
    --out prometheus-remote-write \
    k6-script.js

# Store results in audit trail
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
RESULTS_FILE="results_${TIMESTAMP}.json"

k6 run --summary-export=$RESULTS_FILE k6-script.js

# Store in audit trail
../audit/store-evidence.sh "load-test" "$RESULTS_FILE"

# Clean up
rm "$RESULTS_FILE"