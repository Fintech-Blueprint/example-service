# Grafana Dashboard Configuration

## Overview
This directory contains versioned Grafana dashboards that are:
1. Tied to Golden Goose releases
2. Reference thresholds from alerts.yaml
3. Included in rollbacks

## Structure
```
grafana-dashboards/
├── service-dashboard.json     # Main service dashboard
├── alerts-dashboard.json     # Alert overview dashboard
├── load-test-dashboard.json  # Load test results dashboard
└── config.yaml              # Dashboard configuration
```

## Features
- Automatic threshold updates from alerts.yaml
- Version control with releases
- Rollback support
- Prometheus data source integration

## Integration
- Dashboards are packaged with Golden Goose releases
- Alert thresholds are sourced from alerts.yaml
- Changes trigger dashboard updates
- Rollbacks restore dashboard state