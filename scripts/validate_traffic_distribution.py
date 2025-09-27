#!/usr/bin/env python3
"""
Synthetic Traffic Generator and Validator for Service-B Canary Deployment
Validates the 90/10 traffic split and collects evidence.
"""

import json
import time
import requests
import subprocess
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import sys

# Configuration
TOTAL_REQUESTS = 1000
CONCURRENT_REQUESTS = 10
SERVICE_B_ENDPOINT = "http://service-b/v1"
EVIDENCE_DIR = Path("evidence/sprint6/traffic")

def send_request():
    """Send a single request and return the version from response"""
    try:
        response = requests.get(f"{SERVICE_B_ENDPOINT}/version")
        return response.headers.get('X-Version', 'unknown')
    except Exception as e:
        print(f"Request failed: {e}")
        return 'error'

def validate_distribution(results):
    """Validate if the traffic distribution matches 90/10 split"""
    total = len([r for r in results if r != 'error'])
    if total == 0:
        return False, "All requests failed"
    
    counts = Counter(results)
    v2_percentage = (counts.get('v2', 0) / total) * 100
    v1_percentage = (counts.get('v1', 0) / total) * 100
    
    # Allow for some variance (±5%)
    is_valid = (85 <= v2_percentage <= 95) and (5 <= v1_percentage <= 15)
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_requests": total,
        "distribution": {
            "v1": v1_percentage,
            "v2": v2_percentage
        },
        "raw_counts": dict(counts),
        "is_valid": is_valid
    }
    
    return is_valid, report

def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    print(f"Sending {TOTAL_REQUESTS} requests to validate traffic distribution...")
    
    with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        results = list(executor.map(lambda _: send_request(), range(TOTAL_REQUESTS)))
    
    is_valid, report = validate_distribution(results)
    
    # Save evidence
    report_file = EVIDENCE_DIR / f"traffic_validation_{timestamp}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Generate hash
    subprocess.run(['sha256sum', str(report_file)], 
                  stdout=open(str(report_file) + '.sha256', 'w'))
    
    # Update evidence chain
    with open('EVIDENCE_CHAIN.md', 'a') as f:
        f.write(f"\n## Traffic Validation {timestamp}\n")
        f.write(f"- Result: {'✅ PASS' if is_valid else '❌ FAIL'}\n")
        f.write(f"- File: {report_file.name}\n")
        f.write(f"- SHA256: {open(str(report_file) + '.sha256').read().strip()}\n")
    
    print(f"Traffic Distribution Report:")
    print(json.dumps(report, indent=2))
    
    return 0 if is_valid else 1

if __name__ == "__main__":
    sys.exit(main())