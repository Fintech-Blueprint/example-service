#!/usr/bin/env python3
"""
Golden Goose v1 - Package Generator
Generates a consolidated package of service reports and artifacts.
"""

import os
import yaml
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List

class GoldenGoosePackager:
    def __init__(self):
        with open('org-config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        self.version = 'v1'
        
    def _get_latest_successful_run(self, service_path: str) -> Dict:
        """Get the latest successful run for a service."""
        reports_path = Path(service_path) / 'reports'
        latest_run = None
        latest_timestamp = None
        
        for sha_dir in reports_path.glob('*'):
            if not sha_dir.is_dir() or sha_dir.name == 'archive':
                continue
                
            for run_dir in sha_dir.glob('*'):
                if not run_dir.is_dir():
                    continue
                    
                manifest_file = run_dir / 'manifest.json'
                if not manifest_file.exists():
                    continue
                    
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                    
                if manifest.get('status') == 'success':
                    timestamp = datetime.strptime(manifest.get('timestamp'), '%Y-%m-%dT%H:%M:%SZ')
                    if not latest_timestamp or timestamp > latest_timestamp:
                        latest_timestamp = timestamp
                        latest_run = run_dir
        
        return latest_run
    
    def _collect_service_artifacts(self, service_dir: Path) -> Dict:
        """Collect artifacts from a service's latest successful run."""
        latest_run = self._get_latest_successful_run(service_dir)
        if not latest_run:
            return None
            
        artifacts = {
            'reports': {},
            'sbom': None,
            'manifest': None,
            'signatures': []
        }
        
        # Collect reports
        for report in latest_run.glob('*.json'):
            if report.name != 'manifest.json':
                with open(report, 'r') as f:
                    artifacts['reports'][report.name] = json.load(f)
        
        # Get SBOM
        sbom_file = latest_run / 'sbom.cyclonedx.json'
        if sbom_file.exists():
            with open(sbom_file, 'r') as f:
                artifacts['sbom'] = json.load(f)
        
        # Get manifest
        manifest_file = latest_run / 'manifest.json'
        if manifest_file.exists():
            with open(manifest_file, 'r') as f:
                artifacts['manifest'] = json.load(f)
        
        # Collect signatures
        for sig in latest_run.glob('*.sig'):
            with open(sig, 'rb') as f:
                artifacts['signatures'].append({
                    'name': sig.name,
                    'content': f.read()
                })
        
        return artifacts
    
    def generate_package(self) -> str:
        """Generate a Golden Goose package with artifacts from all services."""
        services_dir = Path('services')
        if not services_dir.exists():
            raise FileNotFoundError("Services directory not found")
        
        # Create package directory
        package_dir = Path('golden-goose/releases') / self.version / self.timestamp
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Collect artifacts from all services
        services_data = {}
        for service_dir in services_dir.glob('*'):
            if not service_dir.is_dir():
                continue
                
            artifacts = self._collect_service_artifacts(service_dir)
            if artifacts:
                services_data[service_dir.name] = artifacts
        
        # Generate summary
        summary = []
        for service, data in services_data.items():
            manifest = data.get('manifest', {})
            summary.append(f"{service}|{manifest.get('status', 'unknown')}|{manifest.get('timestamp', 'unknown')}")
        
        # Write summary
        with open(package_dir / 'summary.txt', 'w') as f:
            f.write('\n'.join(summary))
        
        # Write detailed reports
        reports_dir = package_dir / 'reports'
        reports_dir.mkdir(exist_ok=True)
        
        for service, data in services_data.items():
            service_dir = reports_dir / service
            service_dir.mkdir(exist_ok=True)
            
            # Write reports
            for report_name, content in data['reports'].items():
                with open(service_dir / report_name, 'w') as f:
                    json.dump(content, f, indent=2)
            
            # Write SBOM
            if data['sbom']:
                with open(service_dir / 'sbom.cyclonedx.json', 'w') as f:
                    json.dump(data['sbom'], f, indent=2)
            
            # Write manifest
            if data['manifest']:
                with open(service_dir / 'manifest.json', 'w') as f:
                    json.dump(data['manifest'], f, indent=2)
            
            # Write signatures
            for sig in data['signatures']:
                with open(service_dir / sig['name'], 'wb') as f:
                    f.write(sig['content'])
        
        # Update latest symlink
        latest_link = Path('golden-goose/releases') / self.version / 'latest'
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(package_dir.relative_to(latest_link.parent))
        
        return package_dir

if __name__ == '__main__':
    try:
        packager = GoldenGoosePackager()
        package_dir = packager.generate_package()
        print(f"Golden Goose package generated successfully at: {package_dir}")
    except Exception as e:
        print(f"Error generating package: {e}")
        exit(1)