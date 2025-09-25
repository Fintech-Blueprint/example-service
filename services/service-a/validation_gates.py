from typing import List, Dict, Optional
import json
import hashlib
from datetime import datetime
from pydantic import BaseModel

class ValidationGate:
    def __init__(self, name: str, gate_type: str):
        self.name = name
        self.type = gate_type  # blocking or advisory
        self.validations = []
    
    def validate(self, context: Dict) -> Dict:
        raise NotImplementedError

class DependencyGate(ValidationGate):
    def __init__(self):
        super().__init__("dependency_check", "blocking")
    
    def validate(self, context: Dict) -> Dict:
        dependencies = context.get("dependencies", {})
        required = dependencies.get("required", [])
        optional = dependencies.get("optional", [])
        
        # In POC phase, we'll just check if dependencies are declared
        return {
            "valid": True if required or optional else False,
            "message": "Dependencies declared" if required or optional else "No dependencies specified",
            "details": {
                "required": required,
                "optional": optional
            }
        }

class EvidenceChainGate(ValidationGate):
    def __init__(self):
        super().__init__("evidence_chain", "blocking")
    
    def validate(self, context: Dict) -> Dict:
        evidence_chain = context.get("evidence_chain", [])
        if not evidence_chain:
            return {
                "valid": False,
                "message": "Empty evidence chain",
                "details": None
            }
        
        # Verify hash chain integrity
        previous_hash = "0" * 64
        for evidence in evidence_chain:
            # Remove hash field for hash calculation
            evidence_copy = evidence.copy()
            current_hash = evidence_copy.pop("hash", None)
            
            if evidence_copy.get("previous_hash") != previous_hash:
                return {
                    "valid": False,
                    "message": "Evidence chain broken",
                    "details": {
                        "expected_hash": previous_hash,
                        "found_hash": evidence_copy.get("previous_hash")
                    }
                }
            
            # Calculate hash
            evidence_str = json.dumps(evidence_copy, sort_keys=True)
            calculated_hash = hashlib.sha256(evidence_str.encode()).hexdigest()
            
            if calculated_hash != current_hash:
                return {
                    "valid": False,
                    "message": "Evidence hash mismatch",
                    "details": {
                        "expected_hash": current_hash,
                        "calculated_hash": calculated_hash
                    }
                }
            
            previous_hash = current_hash
        
        return {
            "valid": True,
            "message": "Evidence chain verified",
            "details": {
                "chain_length": len(evidence_chain),
                "last_hash": previous_hash
            }
        }

class ValidationGatekeeper:
    def __init__(self):
        self.gates = [
            DependencyGate(),
            EvidenceChainGate()
        ]
    
    def validate_all(self, context: Dict) -> List[Dict]:
        results = []
        for gate in self.gates:
            try:
                result = gate.validate(context)
                results.append({
                    "gate": gate.name,
                    "type": gate.type,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "gate": gate.name,
                    "type": gate.type,
                    "result": {
                        "valid": False,
                        "message": f"Gate validation error: {str(e)}",
                        "details": None
                    }
                })
        return results