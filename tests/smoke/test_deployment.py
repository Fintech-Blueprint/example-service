#!/usr/bin/env python3
"""
Smoke test for example-service deployment
Per CTO requirements: Verifies basic service health and reports metrics
"""

import os
import sys
import time
import requests
from datetime import datetime

def log(message):
    """Log a message with timestamp."""
    timestamp = datetime.utcnow().isoformat() + "Z"
    print(f"{timestamp} | {message}")

def check_health(url, max_retries=2, retry_interval=120):
    """Check service health with retry logic."""
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(f"{url}/healthz")
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") != "healthy":
                raise ValueError(f"Unhealthy status: {data.get('status')}")
            
            return True
        except Exception as e:
            log(f"Health check attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries:
                log(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
    
    return False

def main():
    service_url = os.getenv("SERVICE_URL", "http://localhost:8000")
    log(f"Starting smoke test against {service_url}")
    
    success = check_health(service_url)
    
    # Update status file
    os.makedirs("reports", exist_ok=True)
    with open("reports/status.txt", "w") as f:
        f.write(f"smoke:{'PASS' if success else 'FAIL'} health_up:{1 if success else 0}")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()