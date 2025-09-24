"""
Service dependency management and health validation module.
"""
import os
import yaml
import requests
from typing import Dict, List, Optional
from prometheus_client import Gauge

# Load org-level configuration
with open('org-config.yaml', 'r') as f:
    org_config = yaml.safe_load(f)

# Dependency health metrics
dependency_health = Gauge('service_dependency_health', 'Health status of service dependencies', ['service', 'dependency'])
dependency_mode = Gauge('service_dependency_mode', 'Mode of service dependencies', ['service', 'dependency'])

class DependencyManager:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.mode = os.getenv('SERVICE_MODE', 'sandbox').lower()
        
    def get_dependencies(self) -> List[str]:
        """Get list of dependencies for this service."""
        services_dir = os.path.join('services')
        deps_file = os.path.join(services_dir, self.service_name, 'dependencies.yaml')
        
        if not os.path.exists(deps_file):
            return []
            
        with open(deps_file, 'r') as f:
            deps = yaml.safe_load(f)
            return deps.get('dependencies', [])
    
    def check_dependency_health(self) -> Dict[str, bool]:
        """Check health status of all dependencies."""
        results = {}
        deps = self.get_dependencies()
        
        for dep in deps:
            try:
                # Check dependency health endpoint
                resp = requests.get(f'http://{dep}:8000/healthz', timeout=5)
                health_status = resp.status_code == 200
                dep_mode = resp.headers.get('X-Service-Mode', 'unknown')
                
                # Update Prometheus metrics
                dependency_health.labels(service=self.service_name, dependency=dep).set(1 if health_status else 0)
                dependency_mode.labels(service=self.service_name, dependency=dep).set(1 if dep_mode == 'compliance' else 0)
                
                results[dep] = health_status
                
            except Exception:
                dependency_health.labels(service=self.service_name, dependency=dep).set(0)
                results[dep] = False
        
        return results
    
    def validate_compliance_prerequisites(self) -> Optional[str]:
        """
        Validate if service can switch to compliance mode.
        Returns None if valid, error message if not.
        """
        if self.mode == 'compliance':
            return None
            
        # Check dependency modes
        deps = self.get_dependencies()
        for dep in deps:
            try:
                resp = requests.get(f'http://{dep}:8000/healthz', timeout=5)
                if resp.headers.get('X-Service-Mode') != 'compliance':
                    return f"Dependency {dep} must be in compliance mode"
            except Exception:
                return f"Cannot verify dependency {dep}"
        
        return None