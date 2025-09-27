#!/bin/bash
set -euo pipefail

NAMESPACE=monitoring
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
METRICS_DIR=evidence/sprint5/metrics

mkdir -p $METRICS_DIR

# Get Grafana admin password
GRAFANA_PASSWORD=$(kubectl -n $NAMESPACE get secret grafana -o jsonpath="{.data.admin-password}" | base64 --decode)

# Port forward Grafana (in background)
kubectl -n $NAMESPACE port-forward svc/grafana 3000:80 &
PF_PID=$!
sleep 5

# Get all dashboards
DASHBOARDS=$(curl -s -u "admin:$GRAFANA_PASSWORD" http://localhost:3000/api/search?type=dash-db)

echo "{" > $METRICS_DIR/grafana_dashboards_$TIMESTAMP.json
echo "  \"timestamp\": \"$TIMESTAMP\"," >> $METRICS_DIR/grafana_dashboards_$TIMESTAMP.json
echo "  \"dashboards\": [" >> $METRICS_DIR/grafana_dashboards_$TIMESTAMP.json

# For each dashboard, get its full JSON
echo "$DASHBOARDS" | jq -r '.[] | .uid' | while read -r uid; do
  if [ ! -z "$uid" ]; then
    curl -s -u "admin:$GRAFANA_PASSWORD" "http://localhost:3000/api/dashboards/uid/$uid" >> $METRICS_DIR/grafana_dashboards_$TIMESTAMP.json
    echo "," >> $METRICS_DIR/grafana_dashboards_$TIMESTAMP.json
  fi
done

# Remove last comma and close JSON
sed -i '$ d' $METRICS_DIR/grafana_dashboards_$TIMESTAMP.json
echo "  ]" >> $METRICS_DIR/grafana_dashboards_$TIMESTAMP.json
echo "}" >> $METRICS_DIR/grafana_dashboards_$TIMESTAMP.json

# Kill port-forward
kill $PF_PID

./scripts/hash-evidence.sh $METRICS_DIR/grafana_dashboards_$TIMESTAMP.json "Grafana dashboards export" sprint5