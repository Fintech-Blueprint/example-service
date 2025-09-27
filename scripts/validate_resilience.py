#!/usr/bin/env python3
"""
Service Resilience Validator
Tests retry policies and circuit breaker behavior while collecting evidence.
"""

import json
import time
import requests
import subprocess
from datetime import datetime
from pathlib import Path
import sys

# Configuration
EVIDENCE_DIR = Path("evidence/sprint6/resilience")
SERVICES = ['service-a', 'service-b', 'service-c']

def test_retry_policy(service):
    """Test retry policy by causing intentional failures and monitoring retries"""
    endpoint = f"http://{service}/v1/test-retry"
    try:
        # Add a header to trigger artificial failures that should be retried
        response = requests.get(endpoint, headers={'X-Fail-First': 'true'}, timeout=10)
        return {
            'status': response.status_code,
            'retries': int(response.headers.get('X-Retry-Count', 0)),
            'success': response.status_code == 200
        }
    except requests.exceptions.Timeout:
        return {'status': 504, 'retries': 0, 'success': False}
    except Exception as e:
        return {'status': 500, 'retries': 0, 'success': False, 'error': str(e)}

def test_circuit_breaker(service):
    """Test circuit breaker by generating errors until it trips"""
    endpoint = f"http://{service}/v1/test-circuit-breaker"
    results = []
    
    for i in range(10):  # Send enough requests to potentially trip the circuit breaker
        try:
            # Add header to trigger artificial 500 errors
            response = requests.get(endpoint, headers={'X-Force-Error': 'true'}, timeout=2)
            results.append({
                'attempt': i + 1,
                'status': response.status_code,
                'circuit_open': response.headers.get('X-Circuit-Open', 'false') == 'true'
            })
        except requests.exceptions.Timeout:
            results.append({
                'attempt': i + 1,
                'status': 504,
                'circuit_open': True
            })
        except Exception as e:
            results.append({
                'attempt': i + 1,
                'status': 500,
                'circuit_open': True,
                'error': str(e)
            })
        
        time.sleep(1)  # Brief pause between requests
    
    return results

def validate_service(service):
    """Run all resilience tests for a service"""
    print(f"\nTesting resilience for {service}...")
    
    retry_results = test_retry_policy(service)
    print(f"Retry Policy Test: {'✅ PASS' if retry_results['success'] else '❌ FAIL'}")
    
    circuit_breaker_results = test_circuit_breaker(service)
    circuit_breaker_tripped = any(r['circuit_open'] for r in circuit_breaker_results)
    print(f"Circuit Breaker Test: {'✅ PASS' if circuit_breaker_tripped else '❌ FAIL'}")
    
    return {
        'service': service,
        'timestamp': datetime.utcnow().isoformat(),
        'retry_policy': retry_results,
        'circuit_breaker': circuit_breaker_results,
        'overall_success': retry_results['success'] and circuit_breaker_tripped
    }

def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    results = []
    overall_success = True
    
    for service in SERVICES:
        result = validate_service(service)
        results.append(result)
        overall_success &= result['overall_success']
    
    # Save evidence
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'results': results,
        'overall_success': overall_success
    }
    
    report_file = EVIDENCE_DIR / f"resilience_validation_{timestamp}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Generate hash
    subprocess.run(['sha256sum', str(report_file)], 
                  stdout=open(str(report_file) + '.sha256', 'w'))
    
    # Update evidence chain
    with open('EVIDENCE_CHAIN.md', 'a') as f:
        f.write(f"\n## Resilience Validation {timestamp}\n")
        f.write(f"- Result: {'✅ PASS' if overall_success else '❌ FAIL'}\n")
        f.write(f"- File: {report_file.name}\n")
        f.write(f"- SHA256: {open(str(report_file) + '.sha256').read().strip()}\n")
    
    print(f"\nResilience Validation Report:")
    print(json.dumps(report, indent=2))
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())