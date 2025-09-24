#!/usr/bin/env python3
"""
Smoke test script for example-service
Per CTO requirements: Check /healthz endpoint and report health_up metric
"""

import os
import sys
import time
import requests
from datetime import datetime

def log(message):
    timestamp = datetime.utcnow().isoformat() + "Z"
    print(f"{timestamp} | {message}")

def main():
    # Get service URL from environment or use default
    service_url = os.getenv("SERVICE_URL", "http://localhost:8000")
    max_retries = 2
    retry_interval = 120  # seconds

    log(f"Starting smoke test against {service_url}")
    
    for attempt in range(max_retries + 1):
        try:
            # Check health endpoint
            response = requests.get(f"{service_url}/healthz")
            response.raise_for_status()
            
            # Verify response format
            data = response.json()
            if data.get("status") != "healthy":
                raise ValueError("Unexpected health status")
                
            log("Health check passed - service is healthy")
            # Write status for the one-line report
            with open("reports/status.txt", "w") as f:
                f.write("smoke:PASS health_up:1")
            sys.exit(0)
            
        except Exception as e:
            log(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries:
                log(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                log("All retry attempts failed")
                # Write failure status
                with open("reports/status.txt", "w") as f:
                    f.write("smoke:FAIL health_up:0")
                sys.exit(1)

if __name__ == "__main__":
    main()