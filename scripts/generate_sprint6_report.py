#!/usr/bin/env python3
"""
Sprint 6 Bi-Daily Report Generator
Generates comprehensive reports on service performance, traffic validation, and chaos test outcomes.
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

def get_service_metrics(service):
    """Get service metrics from Prometheus"""
    metrics = {
        'latency_p95': subprocess.getoutput(
            'curl -s "http://prometheus:9090/api/v1/query" '
            f'-d "query=histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket{{destination_service=~\'{service}.*\'}}[5m])) by (le))"'
        ),
        'error_rate': subprocess.getoutput(
            'curl -s "http://prometheus:9090/api/v1/query" '
            f'-d "query=sum(rate(istio_requests_total{{destination_service=~\'{service}.*\',response_code=~\'5.*\'}}[5m])) / sum(rate(istio_requests_total{{destination_service=~\'{service}.*\'}}[5m])) * 100"'
        ),
        'throughput': subprocess.getoutput(
            'curl -s "http://prometheus:9090/api/v1/query" '
            f'-d "query=sum(rate(istio_requests_total{{destination_service=~\'{service}.*\'}}[5m]))"'
        )
    }
    return metrics

def get_traffic_distribution():
    """Get traffic distribution for Service-B canary"""
    return subprocess.getoutput(
        'curl -s "http://prometheus:9090/api/v1/query" '
        '-d "query=sum(rate(istio_requests_total{destination_service=~\'service-b.*\'}[5m])) by (version)"'
    )

def get_chaos_test_results():
    """Read and parse chaos test logs"""
    log_file = Path("evidence/sprint6/chaos/chaos_test_log.txt")
    if not log_file.exists():
        return "No chaos test results found"
    
    return log_file.read_text()

def generate_report():
    """Generate the bi-daily report"""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
    report_dir = Path("evidence/sprint6/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "service-a": get_service_metrics("service-a"),
            "service-b": get_service_metrics("service-b"),
            "service-c": get_service_metrics("service-c")
        },
        "traffic_distribution": get_traffic_distribution(),
        "chaos_test_results": get_chaos_test_results()
    }
    
    # Write JSON report
    report_file = report_dir / f"sprint6_report_{timestamp}.json"
    report_file.write_text(json.dumps(report, indent=2))
    
    # Generate SHA256 hash
    subprocess.run(["sha256sum", str(report_file)], 
                  stdout=open(str(report_file) + ".sha256", "w"))
    
    # Update evidence chain
    evidence_chain = Path("EVIDENCE_CHAIN.md")
    if not evidence_chain.exists():
        evidence_chain.write_text("# Sprint 6 Evidence Chain\n\n")
    
    with open(evidence_chain, "a") as f:
        f.write(f"\n## Report {timestamp}\n")
        f.write(f"- Timestamp: {report['timestamp']}\n")
        f.write(f"- File: {report_file.name}\n")
        f.write(f"- SHA256: {open(str(report_file) + '.sha256').read().strip()}\n")

if __name__ == "__main__":
    generate_report()