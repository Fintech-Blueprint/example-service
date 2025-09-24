"""
Service mode transition management and validation.
"""
import os
import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from .dependency_manager import DependencyManager

class ModeTransitionManager:
    def __init__(self, service_name: str):
        self.service_name = service_name
        with open('org-config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.dep_manager = DependencyManager(service_name)
        self.current_mode = os.getenv('SERVICE_MODE', 'sandbox').lower()
        
    def validate_compliance_readiness(self) -> Dict[str, bool]:
        """
        Validate if service is ready for compliance mode.
        Returns dict of check results.
        """
        results = {
            'dependencies_compliant': True,
            'tests_passing': True,
            'sast_passing': True,
            'signatures_valid': True,
            'resource_limits_ok': True
        }
        
        # Check dependencies
        dep_error = self.dep_manager.validate_compliance_prerequisites()
        results['dependencies_compliant'] = dep_error is None
        
        # Check test coverage
        coverage_file = Path(f'services/{self.service_name}/reports/latest/coverage.json')
        if coverage_file.exists():
            with open(coverage_file, 'r') as f:
                coverage = json.load(f)
                results['tests_passing'] = coverage.get('total_coverage', 0) >= 70
        else:
            results['tests_passing'] = False
        
        # Check SAST results
        sast_file = Path(f'services/{self.service_name}/reports/latest/sast-report.json')
        if sast_file.exists():
            with open(sast_file, 'r') as f:
                sast = json.load(f)
                results['sast_passing'] = sast.get('high_severity_issues', 1) == 0
        else:
            results['sast_passing'] = False
        
        # Check signatures
        sig_dir = Path(f'services/{self.service_name}/reports/latest')
        results['signatures_valid'] = any(sig_dir.glob('*.sig'))
        
        # Check resource compliance
        resource_file = Path(f'services/{self.service_name}/reports/latest/resource-usage.json')
        if resource_file.exists():
            with open(resource_file, 'r') as f:
                resources = json.load(f)
                cpu_limit = float(self.config['org']['resource_limits']['compliance']['cpu'].split('-')[1])
                mem_limit = float(self.config['org']['resource_limits']['compliance']['memory'].split('-')[1].replace('Mi', ''))
                
                results['resource_limits_ok'] = (
                    resources.get('cpu_usage', 0) <= cpu_limit and
                    resources.get('memory_usage', 0) <= mem_limit
                )
        else:
            results['resource_limits_ok'] = False
        
        return results
    
    def request_compliance_mode(self) -> Optional[str]:
        """
        Request transition to compliance mode.
        Returns None if successful, error message if not.
        """
        if self.current_mode == 'compliance':
            return "Already in compliance mode"
        
        # Validate readiness
        checks = self.validate_compliance_readiness()
        if not all(checks.values()):
            failed = [k for k, v in checks.items() if not v]
            return f"Failed compliance checks: {', '.join(failed)}"
        
        # Record transition request
        transition_dir = Path(f'services/{self.service_name}/mode-transitions')
        transition_dir.mkdir(exist_ok=True)
        
        transition_file = transition_dir / f'request_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.json'
        transition_data = {
            'requested_at': datetime.utcnow().isoformat(),
            'from_mode': self.current_mode,
            'to_mode': 'compliance',
            'checks': checks,
            'status': 'pending_approval'
        }
        
        with open(transition_file, 'w') as f:
            json.dump(transition_data, f, indent=2)
        
        return None  # Success