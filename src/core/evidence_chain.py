import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

class EvidenceHashChain:
    def __init__(self, service: str, base_path: str = "/workspaces/example-service/audit"):
        self.service = service
        self.base_path = Path(base_path)
        self.evidence_path = self.base_path / "services" / service / "evidence"
        self.evidence_path.mkdir(parents=True, exist_ok=True)

    def _calculate_hash(self, data: Dict[str, Any]) -> str:
        """Calculate SHA256 hash of the data"""
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def _get_latest_hash(self) -> Optional[str]:
        """Get the hash of the latest evidence entry"""
        try:
            latest_file = sorted(self.evidence_path.glob("**/*.json"))[-1]
            with open(latest_file) as f:
                data = json.load(f)
                return data.get("hash")
        except (IndexError, FileNotFoundError):
            return None

    def store_evidence(self, evidence_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Store new evidence in the chain"""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        evidence_id = str(uuid.uuid4())
        
        evidence_entry = {
            "id": evidence_id,
            "timestamp": timestamp,
            "service": self.service,
            "type": evidence_type,
            "data": data,
            "metadata": {
                "phase": "poc",
                "sprint": "1",
                "provisional": True
            },
            "previous_hash": self._get_latest_hash(),
        }
        
        # Calculate hash after setting previous_hash
        evidence_entry["hash"] = self._calculate_hash(evidence_entry)
        
        # Store evidence
        evidence_file = self.evidence_path / f"{timestamp}-{evidence_type}-{evidence_id[:8]}.json"
        with open(evidence_file, "w") as f:
            json.dump(evidence_entry, f, indent=2)
        
        # Create checksum file
        checksum_file = evidence_file.with_suffix(".sha256")
        with open(checksum_file, "w") as f:
            f.write(f"{evidence_entry['hash']} *{evidence_file.name}")
        
        return evidence_entry

    def verify_chain(self) -> bool:
        """Verify the integrity of the evidence chain"""
        files = sorted(self.evidence_path.glob("**/*.json"))
        previous_hash = None
        
        for file in files:
            with open(file) as f:
                entry = json.load(f)
                
                if entry.get("previous_hash") != previous_hash:
                    return False
                
                calculated_hash = self._calculate_hash({
                    **entry,
                    "hash": None  # Remove hash before calculating
                })
                
                if calculated_hash != entry.get("hash"):
                    return False
                
                previous_hash = entry.get("hash")
        
        return True