from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime
import json


class PromotionState:
    SANDBOX = "sandbox"
    COMPLIANCE_READY = "compliance_ready"
    COMPLIANT = "compliant"


class EvidenceRef(BaseModel):
    path: str
    type: str
    hash: str


class Dependencies(BaseModel):
    required: List[str]
    optional: List[str] = []


class PromotionRequest(BaseModel):
    service: str
    target_state: str
    evidence_refs: List[EvidenceRef]
    dependencies: Dependencies


class ValidationResult(BaseModel):
    valid: bool
    message: str
    details: Optional[Dict] = None


class PromotionManager:
    def __init__(self):
        self.current_state = PromotionState.SANDBOX
        self.evidence_chain = []

    def validate_transition(self, target_state: str) -> ValidationResult:
        """Validate if the requested state transition is allowed"""
        allowed_transitions = {
            PromotionState.SANDBOX: [PromotionState.COMPLIANCE_READY],
            PromotionState.COMPLIANCE_READY: [PromotionState.COMPLIANT],
            PromotionState.COMPLIANT: [PromotionState.SANDBOX]  # For rollbacks
        }

        if target_state not in allowed_transitions.get(self.current_state, []):
            return ValidationResult(
                valid=False,
                message=f"Invalid transition from {self.current_state} to {target_state}",
                details={"allowed_transitions": allowed_transitions[self.current_state]}
            )

        return ValidationResult(valid=True, message="Transition allowed")

    def validate_evidence(self, evidence_refs: List[EvidenceRef]) -> ValidationResult:
        """Validate evidence requirements for promotion"""
        required_evidence = {
            PromotionState.COMPLIANCE_READY: ["sast", "tests", "metrics"],
            PromotionState.COMPLIANT: ["dependency_check", "compliance_scan", "performance_test"]
        }

        evidence_types = set(ref.type for ref in evidence_refs)
        needed_evidence = set(required_evidence.get(self.current_state, []))

        if not needed_evidence.issubset(evidence_types):
            missing = needed_evidence - evidence_types
            return ValidationResult(
                valid=False,
                message="Missing required evidence",
                details={"missing": list(missing)}
            )

        return ValidationResult(valid=True, message="Evidence requirements met")

    def request_promotion(self, request: PromotionRequest) -> Dict:
        """Process a promotion request"""
        # Validate state transition
        transition_result = self.validate_transition(request.target_state)
        if not transition_result.valid:
            return {"status": "error", "details": transition_result.dict()}

        # Validate evidence
        evidence_result = self.validate_evidence(request.evidence_refs)
        if not evidence_result.valid:
            return {"status": "error", "details": evidence_result.dict()}

        # Record promotion attempt in evidence chain
        promotion_evidence = {
            "timestamp": datetime.utcnow().isoformat(),
            "request": request.dict(),
            "validation_results": {
                "transition": transition_result.dict(),
                "evidence": evidence_result.dict()
            }
        }

        self.evidence_chain.append(promotion_evidence)

        # Update state if all validations pass
        self.current_state = request.target_state

        return {
            "status": "success",
            "new_state": self.current_state,
            "timestamp": promotion_evidence["timestamp"]
        }
