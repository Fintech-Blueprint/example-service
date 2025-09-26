#!/bin/bash
set -euo pipefail

NAMESPACE=monitoring
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
METRICS_DIR=evidence/sprint5/metrics

mkdir -p $METRICS_DIR

# Collect key metrics
METRICS=(
  'rate(istio_requests_total{reporter="source"}[5m])'
  'histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket[5m])) by (le, destination_service))'
  'sum(envoy_cluster_upstream_rq_retry{}) by (cluster_name)'
  'sum(envoy_cluster_circuit_breakers_default_open{}) by (cluster_name)'
  'sum(rate(istio_requests_total{destination_service="service-b",destination_version="v2"}[5m])) / sum(rate(istio_requests_total{destination_service="service-b"}[5m]))'
)

echo "{" > $METRICS_DIR/prometheus_snapshot_$TIMESTAMP.json
echo "  \"timestamp\": \"$TIMESTAMP\"," >> $METRICS_DIR/prometheus_snapshot_$TIMESTAMP.json
echo "  \"metrics\": {" >> $METRICS_DIR/prometheus_snapshot_$TIMESTAMP.json

for metric in "${METRICS[@]}"; do
  echo "    \"$(echo $metric | tr -d '\n')\": " >> $METRICS_DIR/prometheus_snapshot_$TIMESTAMP.json
  kubectl -n $NAMESPACE exec deploy/prometheus-server -c prometheus-server -- wget -qO- --post-data="query=$metric" http://localhost:9090/api/v1/query >> $METRICS_DIR/prometheus_snapshot_$TIMESTAMP.json
  echo "," >> $METRICS_DIR/prometheus_snapshot_$TIMESTAMP.json
done

# Remove last comma
sed -i '$ d' $METRICS_DIR/prometheus_snapshot_$TIMESTAMP.json
echo "  }" >> $METRICS_DIR/prometheus_snapshot_$TIMESTAMP.json
echo "}" >> $METRICS_DIR/prometheus_snapshot_$TIMESTAMP.json

./scripts/hash-evidence.sh $METRICS_DIR/prometheus_snapshot_$TIMESTAMP.json "Prometheus metrics snapshot" sprint5