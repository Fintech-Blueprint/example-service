import json
from datetime import datetime
import requests
from pathlib import Path

def prepare_promotion_request():
    # Create evidence directory structure
    evidence_base = Path("/workspaces/example-service/audit/services/service-a")
    evidence_base.mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.utcnow().strftime("%Y%m%d")
    evidence_dir = evidence_base / "evidence" / date_str
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect current metrics
    metrics_response = requests.get("http://localhost:8080/metrics")
    metrics_data = metrics_response.text
    
    # Store metrics evidence
    metrics_file = evidence_dir / "metrics" / "baseline.json"
    metrics_file.parent.mkdir(exist_ok=True)
    metrics_file.write_text(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": metrics_data
    }))
    
    # Get evidence chain
    evidence_response = requests.get("http://localhost:8080/api/v1/evidence")
    evidence_chain = evidence_response.json()["chain"]
    
    # Prepare promotion request
    promotion_request = {
        "service": "service-a",
        "target_state": "compliance_ready",
        "evidence_refs": [
            {
                "path": str(metrics_file),
                "type": "metrics",
                "hash": evidence_chain[-1]["hash"] if evidence_chain else None
            }
        ],
        "dependencies": {
            "required": [],
            "optional": []
        }
    }
    
    # Store promotion request
    promotion_dir = evidence_base / "promotions" / f"pr_{date_str}"
    promotion_dir.mkdir(parents=True, exist_ok=True)
    
    request_file = promotion_dir / "request.json"
    request_file.write_text(json.dumps(promotion_request, indent=2))
    
    return str(request_file)

if __name__ == "__main__":
    request_file = prepare_promotion_request()
    print(f"Promotion request prepared: {request_file}")