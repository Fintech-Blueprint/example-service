#!/usr/bin/env python3
"""
Spec Validator - Ensures BDD specifications meet quality standards.

Validates:
- All scenarios have Given/When/Then steps
- Resource tags are present (@resource:<units>)
- Feature files are properly formatted
"""

import argparse
import glob
import json
import sys
from pathlib import Path
from behave.parser import parse_file

def validate_scenario(scenario, feature_file):
    """Validate a single scenario for required components."""
    errors = []
    
    # Check for required step types
    step_types = {step.step_type for step in scenario.steps}
    required_types = {'given', 'when', 'then'}
    missing_types = required_types - step_types
    
    if missing_types:
        errors.append({
            'type': 'missing_steps',
            'scenario': scenario.name,
            'feature': feature_file,
            'line': scenario.line,
            'missing': sorted(list(missing_types))
        })
    
    # Check for @resource tag
    has_resource_tag = any(
        tag.startswith('@resource:') 
        for tag in scenario.tags
    )
    if not has_resource_tag:
        errors.append({
            'type': 'missing_resource_tag',
            'scenario': scenario.name,
            'feature': feature_file,
            'line': scenario.line
        })
        
    return errors

def validate_feature_file(feature_file):
    """Validate an entire feature file."""
    try:
        feature = parse_file(feature_file)
    except Exception as e:
        return {
            'errors': [{
                'type': 'parse_error',
                'feature': feature_file,
                'message': str(e)
            }],
            'stats': {
                'total_scenarios': 0,
                'scenarios_with_errors': 0,
                'coverage_percent': 0
            }
        }
    
    errors = []
    total_scenarios = 0
    scenarios_with_errors = 0
    
    # Validate each scenario
    for scenario in feature.scenarios:
        total_scenarios += 1
        scenario_errors = validate_scenario(scenario, feature_file)
        if scenario_errors:
            scenarios_with_errors += 1
            errors.extend(scenario_errors)
            
    coverage_percent = ((total_scenarios - scenarios_with_errors) / total_scenarios * 100) if total_scenarios > 0 else 0
    
    return {
        'errors': errors,
        'stats': {
            'total_scenarios': total_scenarios,
            'scenarios_with_errors': scenarios_with_errors,
            'coverage_percent': round(coverage_percent, 2)
        }
    }

def main():
    parser = argparse.ArgumentParser(description='Validate BDD feature files')
    parser.add_argument('--out', required=True, help='Output JSON file path')
    args = parser.parse_args()
    
    # Find all feature files
    feature_files = glob.glob('features/**/*.feature', recursive=True)
    if not feature_files:
        print("Error: No feature files found", file=sys.stderr)
        sys.exit(1)
    
    # Validate all features
    total_errors = []
    total_scenarios = 0
    total_scenarios_with_errors = 0
    
    for feature_file in feature_files:
        result = validate_feature_file(feature_file)
        total_errors.extend(result['errors'])
        total_scenarios += result['stats']['total_scenarios']
        total_scenarios_with_errors += result['stats']['scenarios_with_errors']
    
    # Calculate overall coverage
    overall_coverage = ((total_scenarios - total_scenarios_with_errors) / total_scenarios * 100) if total_scenarios > 0 else 0
    
    # Prepare output
    output = {
        'total_features': len(feature_files),
        'total_scenarios': total_scenarios,
        'scenarios_with_errors': total_scenarios_with_errors,
        'coverage_percent': round(overall_coverage, 2),
        'errors': total_errors
    }
    
    # Write output
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, 'w') as f:
        json.dump(output, f, indent=2)
    
    # Exit with error if any validation failures
    if total_errors:
        print(f"Found {len(total_errors)} validation errors:", file=sys.stderr)
        for error in total_errors:
            print(f"  - {error['type']} in {error['feature']} line {error.get('line', 'N/A')}", file=sys.stderr)
        sys.exit(2)
    
    print(f"Validation passed! Coverage: {overall_coverage:.2f}%")

if __name__ == '__main__':
    main()