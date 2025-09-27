#!/usr/bin/env python3

import datetime
import hashlib
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, asdict
from datetime import UTC
from pathlib import Path
from typing import Dict, List, Optional, Set

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


@dataclass
class ResourceValidation:
    cpu: Optional[float] = None
    memory: Optional[int] = None
    storage: Optional[int] = None
    story_points: Optional[int] = None

    def is_valid(self) -> bool:
        return (
            self.cpu is not None and 0.1 <= self.cpu <= 16 and
            self.memory is not None and 128 <= self.memory <= 32768 and
            self.storage is not None and 10 <= self.storage <= 100000 and
            self.story_points is not None and 1 <= self.story_points <= 20
        )

    def get_validation_errors(self) -> List[str]:
        errors = []
        if self.cpu is None or not 0.1 <= self.cpu <= 16:
            errors.append(f"CPU must be between 0.1 and 16 cores, got {self.cpu}")
        if self.memory is None or not 128 <= self.memory <= 32768:
            errors.append(f"Memory must be between 128 and 32768 MB, got {self.memory}")
        if self.storage is None or not 10 <= self.storage <= 100000:
            errors.append(f"Storage must be between 10 and 100000 MB, got {self.storage}")
        if self.story_points is None or not 1 <= self.story_points <= 20:
            errors.append(f"Story points must be between 1 and 20, got {self.story_points}")
        return errors


@dataclass
class ScenarioValidation:
    name: str
    has_given: bool
    has_when: bool
    has_then: bool
    has_resource_tag: bool
    resources: Optional[ResourceValidation] = None
    resource_errors: Optional[List[str]] = None
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
        self.coverage_report_path = None  # Will be set per run
        self.mode = os.environ.get("VALIDATION_MODE", "compliance").lower()
        logging.info(f"Initializing SpecValidator in {self.mode} mode")

    def validate_all(self) -> bool:
        """
        Validates all feature files in the features directory.
        Returns True if all specs are valid, False otherwise.
        """
        logging.info(f"Starting validation of all feature files in {self.features_dir}")
        all_valid = True
        feature_validations = []

        # Get all .feature files
        feature_files = list(self.features_dir.glob("*.feature"))
        if not feature_files:
            logging.error(f"No feature files found in {self.features_dir}")
            return False

        logging.info(f"Found {len(feature_files)} feature files to validate")

        # Calculate combined SHA
        combined_sha = self._calculate_combined_sha(feature_files)
        logging.info(f"Generated combined SHA: {combined_sha}")

        reports_dir = Path("reports")
        feature_sha_dir = reports_dir / combined_sha
        feature_sha_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created reports directory: {feature_sha_dir}")

        self.coverage_report_path = feature_sha_dir / "spec-coverage.json"

        for feature_file in feature_files:
            validation = self._validate_feature(feature_file)
            feature_validations.append(validation)
            if not validation.is_valid:
                all_valid = False

        # Generate coverage report
        self._generate_coverage_report(feature_validations, combined_sha)

        # Write marker if failed in compliance mode
        if self.mode == "compliance" and not all_valid:
            marker = feature_sha_dir / "spec-validation-failed"
            logging.warning(f"Validation failed in compliance mode. Creating marker: {marker}")
            with open(marker, "w") as f:
                f.write(
                    f"Validation failed at {datetime.datetime.now(UTC).isoformat()}. See spec-coverage.json for details.\n")

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
        pending_resource_tag = None
        pending_resource_errors = None
        for i, line in enumerate(lines, 1):
            line = line.strip()
            # Extract feature name
            if line.startswith("Feature:"):
                feature_name = line[8:].strip()
                continue
            # Check for resource tags (store for next scenario)
            if "@resource:" in line:
                match = re.search(r"@resource:cpu=([0-9.]+),memory=(\d+),storage=(\d+),story_points=(\d+)", line)
                if match:
                    try:
                        pending_resource_tag = ResourceValidation(
                            cpu=float(match.group(1)),
                            memory=int(match.group(2)),
                            storage=int(match.group(3)),
                            story_points=int(match.group(4))
                        )
                        pending_resource_errors = pending_resource_tag.get_validation_errors()
                    except Exception as e:
                        pending_resource_tag = None
                        pending_resource_errors = [f"Parse error: {str(e)}"]
                else:
                    pending_resource_tag = None
                    pending_resource_errors = ["Resource tag format invalid"]
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
                    has_resource_tag=pending_resource_tag is not None,
                    resources=pending_resource_tag,
                    resource_errors=pending_resource_errors,
                    line_number=i
                )
                pending_resource_tag = None
                pending_resource_errors = None
                continue
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
            errors = []
            if not scenario.has_given:
                errors.append("Missing 'Given' step")
            if not scenario.has_when:
                errors.append("Missing 'When' step")
            if not scenario.has_then:
                errors.append("Missing 'Then' step")
            if not scenario.has_resource_tag:
                errors.append("Missing @resource tag")
            if scenario.resource_errors:
                errors.extend(scenario.resource_errors)
            if errors:
                is_valid = False
                error_msg = f"Error in {feature_file.name} - Scenario '{scenario.name}' (line {scenario.line_number}):"
                logging.error(error_msg)
                for err in errors:
                    logging.error(f"  {err}")
                if self.mode == "sandbox":
                    logging.warning("Continuing validation in sandbox mode")
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
            "timestamp": datetime.datetime.now(UTC).isoformat(),
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
