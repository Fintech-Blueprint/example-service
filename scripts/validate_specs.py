#!/usr/bin/env python3

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set

@dataclass
class ScenarioValidation:
    name: str
    has_given: bool
    has_when: bool
    has_then: bool
    has_resource_tag: bool
    resource_units: Optional[int] = None
    line_number: Optional[int] = None

@dataclass
class FeatureValidation:
    file_path: str
    feature_name: str
    scenarios: List[ScenarioValidation]
    is_valid: bool
    sha: str

class SpecValidator:
    def __init__(self, features_dir: str = "features"):
        self.features_dir = Path(features_dir)
        self.coverage_report_path = Path("reports/spec-coverage.json")
        
    def validate_all(self) -> bool:
        """
        Validates all feature files in the features directory.
        Returns True if all specs are valid, False otherwise.
        """
        all_valid = True
        feature_validations = []
        
        # Get all .feature files
        feature_files = list(self.features_dir.glob("*.feature"))
        if not feature_files:
            print(f"No feature files found in {self.features_dir}")
            return False
            
        # Calculate combined SHA
        combined_sha = self._calculate_combined_sha(feature_files)
        
        for feature_file in feature_files:
            validation = self._validate_feature(feature_file)
            feature_validations.append(validation)
            if not validation.is_valid:
                all_valid = False
                
        # Generate coverage report
        self._generate_coverage_report(feature_validations, combined_sha)
        
        return all_valid
        
    def _calculate_combined_sha(self, feature_files: List[Path]) -> str:
        """
        Calculate combined SHA of all feature files.
        Files are processed in sorted order for deterministic output.
        """
        sha = hashlib.sha256()
        
        for file in sorted(feature_files):
            content = file.read_bytes()
            sha.update(content)
            
        return sha.hexdigest()[:8]
        
    def _validate_feature(self, feature_file: Path) -> FeatureValidation:
        """Validates a single feature file"""
        scenarios = []
        feature_name = ""
        is_valid = True
        
        with open(feature_file) as f:
            lines = f.readlines()
            
        current_scenario = None
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Extract feature name
            if line.startswith("Feature:"):
                feature_name = line[8:].strip()
                continue
                
            # Start new scenario
            if line.startswith("Scenario:"):
                if current_scenario:
                    scenarios.append(current_scenario)
                current_scenario = ScenarioValidation(
                    name=line[9:].strip(),
                    has_given=False,
                    has_when=False,
                    has_then=False,
                    has_resource_tag=False,
                    line_number=i
                )
                continue
                
            # Check for resource tags
            if "@resource:" in line and current_scenario:
                match = re.search(r"@resource:(\d+)", line)
                if match:
                    current_scenario.has_resource_tag = True
                    current_scenario.resource_units = int(match.group(1))
                    
            # Check for Given/When/Then
            if current_scenario:
                if line.startswith("Given "):
                    current_scenario.has_given = True
                elif line.startswith("When "):
                    current_scenario.has_when = True
                elif line.startswith("Then "):
                    current_scenario.has_then = True
                    
        # Add final scenario
        if current_scenario:
            scenarios.append(current_scenario)
            
        # Validate scenarios
        for scenario in scenarios:
            if not all([scenario.has_given, scenario.has_when, scenario.has_then, scenario.has_resource_tag]):
                is_valid = False
                print(f"\nError in {feature_file.name} - Scenario '{scenario.name}' (line {scenario.line_number}):")
                if not scenario.has_given:
                    print("  Missing 'Given' step")
                if not scenario.has_when:
                    print("  Missing 'When' step")
                if not scenario.has_then:
                    print("  Missing 'Then' step")
                if not scenario.has_resource_tag:
                    print("  Missing @resource:<units> tag")
                    
        return FeatureValidation(
            file_path=str(feature_file),
            feature_name=feature_name,
            scenarios=scenarios,
            is_valid=is_valid,
            sha=hashlib.sha256(feature_file.read_bytes()).hexdigest()[:8]
        )
        
    def _generate_coverage_report(self, validations: List[FeatureValidation], combined_sha: str):
        """Generates the coverage report JSON file"""
        report = {
            "timestamp": "",  # Will be set by CI
            "combined_sha": combined_sha,
            "features": []
        }
        
        for validation in validations:
            feature_report = {
                "file": validation.file_path,
                "name": validation.feature_name,
                "sha": validation.sha,
                "is_valid": validation.is_valid,
                "scenarios": []
            }
            
            for scenario in validation.scenarios:
                scenario_report = asdict(scenario)
                feature_report["scenarios"].append(scenario_report)
                
            report["features"].append(feature_report)
            
        # Create reports directory if it doesn't exist
        self.coverage_report_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write report
        with open(self.coverage_report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
if __name__ == "__main__":
    validator = SpecValidator()
    if not validator.validate_all():
        sys.exit(1)