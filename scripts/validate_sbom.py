#!/usr/bin/env python3

import json
import sys
from typing import Dict, List, Union

def validate_sbom_format(sbom_path: str) -> bool:
    """
    Validates a CycloneDX SBOM JSON file for required fields and format.
    
    Args:
        sbom_path: Path to the SBOM JSON file
        
    Returns:
        bool: True if valid, False if invalid
    """
    try:
        with open(sbom_path) as f:
            sbom = json.load(f)
            
        # Required top-level fields
        required_fields = {
            "bomFormat": str,
            "specVersion": str,
            "version": int,
            "components": list,
            "metadata": dict
        }
        
        for field, expected_type in required_fields.items():
            if field not in sbom:
                print(f"Missing required field: {field}")
                return False
            if not isinstance(sbom[field], expected_type):
                print(f"Invalid type for {field}: expected {expected_type}, got {type(sbom[field])}")
                return False
                
        # Validate components
        for component in sbom["components"]:
            if not validate_component(component):
                return False
                
        # Validate metadata
        if not validate_metadata(sbom["metadata"]):
            return False
            
        return True
        
    except Exception as e:
        print(f"Error validating SBOM: {str(e)}")
        return False

def validate_component(component: Dict) -> bool:
    """Validates a single component in the SBOM"""
    required_fields = {
        "type": str,
        "name": str,
        "version": str
    }
    
    for field, expected_type in required_fields.items():
        if field not in component:
            print(f"Component missing required field: {field}")
            return False
        if not isinstance(component[field], expected_type):
            print(f"Invalid type for component.{field}")
            return False
            
    # Validate allowed component types
    allowed_types = {"application", "framework", "library", "container", "operating-system"}
    if component["type"] not in allowed_types:
        print(f"Invalid component type: {component['type']}")
        return False
        
    return True

def validate_metadata(metadata: Dict) -> bool:
    """Validates the metadata section of the SBOM"""
    required_fields = {
        "timestamp": str,
        "tools": list
    }
    
    for field, expected_type in required_fields.items():
        if field not in metadata:
            print(f"Metadata missing required field: {field}")
            return False
        if not isinstance(metadata[field], expected_type):
            print(f"Invalid type for metadata.{field}")
            return False
            
    # Validate at least one tool
    if not metadata["tools"]:
        print("Metadata must include at least one tool")
        return False
        
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: validate_sbom.py <path_to_sbom.json>")
        sys.exit(1)
        
    sbom_path = sys.argv[1]
    if not validate_sbom_format(sbom_path):
        sys.exit(1)