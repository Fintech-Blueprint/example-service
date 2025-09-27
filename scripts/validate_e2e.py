#!/usr/bin/env python3
"""
End-to-End Validation Script for Sprint 6
Validates all components and generates comprehensive report
"""

import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
import sys
import asyncio
import aiohttp

EVIDENCE_DIR = Path("evidence/sprint6/validation")
COMPONENTS = [
    "monitoring",
    "traffic",
    "resilience",
    "chaos"
]

async def check_prometheus_metrics():
    """Verify Prometheus metrics are being collected"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://prometheus:9090/api/v1/targets") as response:
                data = await response.json()
                active_targets = [t for t in data.get('data', {}).get('activeTargets', [])
                                if t.get('health') == 'up']
                return len(active_targets) > 0
    except Exception as e:
        print(f"Error checking Prometheus metrics: {e}")
        return False

async def verify_grafana_dashboard():
    """Verify Grafana dashboard is accessible"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://grafana:3000/api/dashboards/uid/service-c") as response:
                return response.status == 200
    except Exception as e:
        print(f"Error verifying Grafana dashboard: {e}")
        return False

async def validate_monitoring():
    """Validate monitoring stack"""
    prometheus_ok = await check_prometheus_metrics()
    grafana_ok = await verify_grafana_dashboard()
    
    return {
        "component": "monitoring",
        "prometheus_metrics": prometheus_ok,
        "grafana_dashboard": grafana_ok,
        "success": prometheus_ok and grafana_ok
    }

def validate_traffic():
    """Run traffic validation"""
    try:
        result = subprocess.run(
            ['./scripts/validate_traffic_distribution.py'],
            capture_output=True,
            text=True
        )
        return {
            "component": "traffic",
            "returncode": result.returncode,
            "output": result.stdout,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {
            "component": "traffic",
            "error": str(e),
            "success": False
        }

def validate_resilience():
    """Run resilience validation"""
    try:
        result = subprocess.run(
            ['./scripts/validate_resilience.py'],
            capture_output=True,
            text=True
        )
        return {
            "component": "resilience",
            "returncode": result.returncode,
            "output": result.stdout,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {
            "component": "resilience",
            "error": str(e),
            "success": False
        }

def validate_chaos():
    """Run a single chaos test cycle"""
    try:
        result = subprocess.run(
            ['./scripts/execute_chaos_tests.sh', 'all'],
            capture_output=True,
            text=True
        )
        return {
            "component": "chaos",
            "returncode": result.returncode,
            "output": result.stdout,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {
            "component": "chaos",
            "error": str(e),
            "success": False
        }

async def run_validation():
    """Run all validations"""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    print("Starting end-to-end validation...")
    
    # Run monitoring validation asynchronously
    monitoring_result = await validate_monitoring()
    
    # Run other validations
    traffic_result = validate_traffic()
    resilience_result = validate_resilience()
    chaos_result = validate_chaos()
    
    # Combine results
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "monitoring": monitoring_result,
            "traffic": traffic_result,
            "resilience": resilience_result,
            "chaos": chaos_result
        }
    }
    
    # Calculate overall success
    results["success"] = all(c["success"] for c in results["components"].values())
    
    # Save evidence
    report_file = EVIDENCE_DIR / f"e2e_validation_{timestamp}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate hash
    subprocess.run(['sha256sum', str(report_file)],
                  stdout=open(str(report_file) + '.sha256', 'w'))
    
    # Update evidence chain
    with open('EVIDENCE_CHAIN.md', 'a') as f:
        f.write(f"\n## End-to-End Validation {timestamp}\n")
        f.write(f"- Result: {'✅ PASS' if results['success'] else '❌ FAIL'}\n")
        f.write(f"- File: {report_file.name}\n")
        f.write(f"- SHA256: {open(str(report_file) + '.sha256').read().strip()}\n")
        
        # Add component results
        f.write("\nComponent Status:\n")
        for component, result in results["components"].items():
            f.write(f"- {component}: {'✅' if result['success'] else '❌'}\n")
    
    print("\nValidation Results:")
    print(json.dumps(results, indent=2))
    
    return 0 if results["success"] else 1

def main():
    """Main entry point"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    return asyncio.run(run_validation())

if __name__ == "__main__":
    sys.exit(main())