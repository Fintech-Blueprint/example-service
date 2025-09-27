#!/usr/bin/env python3
"""
Chaos Test Scheduler
Schedules and executes chaos tests on a regular basis to validate service resilience.
"""

import os
import subprocess
import time
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys
import schedule

# Configuration
EVIDENCE_DIR = Path("evidence/sprint6/scheduled-chaos")
SERVICES = ['service-a', 'service-b', 'service-c']

def execute_chaos_test(service):
    """Execute chaos test for a specific service"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    print(f"\nExecuting chaos test for {service} at {timestamp}")
    
    try:
        # Run the chaos test script
        result = subprocess.run(
            ['./scripts/execute_chaos_tests.sh', service],
            capture_output=True,
            text=True
        )
        
        test_result = {
            'service': service,
            'timestamp': datetime.utcnow().isoformat(),
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr if result.returncode != 0 else None
        }
        
        # Save evidence
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        result_file = EVIDENCE_DIR / f"chaos_test_{service}_{timestamp}.json"
        
        with open(result_file, 'w') as f:
            json.dump(test_result, f, indent=2)
        
        # Generate hash
        subprocess.run(['sha256sum', str(result_file)],
                      stdout=open(str(result_file) + '.sha256', 'w'))
        
        # Update evidence chain
        with open('EVIDENCE_CHAIN.md', 'a') as f:
            f.write(f"\n## Scheduled Chaos Test {timestamp}\n")
            f.write(f"- Service: {service}\n")
            f.write(f"- Result: {'✅ PASS' if test_result['success'] else '❌ FAIL'}\n")
            f.write(f"- File: {result_file.name}\n")
            f.write(f"- SHA256: {open(str(result_file) + '.sha256').read().strip()}\n")
        
        print(f"Chaos test for {service} completed. Evidence saved to {result_file}")
        return test_result['success']
        
    except Exception as e:
        print(f"Error executing chaos test for {service}: {e}")
        return False

def run_scheduled_tests():
    """Run chaos tests for all services"""
    print("\nRunning scheduled chaos tests...")
    all_success = True
    
    for service in SERVICES:
        success = execute_chaos_test(service)
        all_success &= success
    
    return all_success

def main():
    print("Starting Chaos Test Scheduler")
    
    # Schedule tests
    # Run tests every 4 hours
    schedule.every(4).hours.do(run_scheduled_tests)
    
    # Also run tests immediately on start
    run_scheduled_tests()
    
    # Keep the scheduler running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            print("\nScheduler stopped by user")
            break
        except Exception as e:
            print(f"Error in scheduler: {e}")
            time.sleep(60)
            continue

if __name__ == "__main__":
    sys.exit(main())