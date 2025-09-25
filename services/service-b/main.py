from fastapi import FastAPI, Response, HTTPException
from prometheus_client import generate_latest
import json
import time
import uuid
from datetime import datetime
import hashlib
import httpx
from typing import Dict, List, Optional
import os

app = FastAPI()

# Service metadata
SERVICE_NAME = "service-b"
PHASE = "poc"
COMPLIANCE_MODE = "sandbox"
SERVICE_A_URL = os.getenv("SERVICE_A_URL", "http://service-a:8080")

# Evidence chain storage
evidence_chain = []

def store_evidence(evidence_type: str, data: dict) -> str:
    """Store evidence in the chain with hash linking"""
    timestamp = datetime.utcnow().isoformat()
    previous_hash = evidence_chain[-1]["hash"] if evidence_chain else "0" * 64
    
    evidence = {
        "promotion_id": str(uuid.uuid4()),
        "timestamp": timestamp,
        "service": SERVICE_NAME,
        "previous_hash": previous_hash,
        "evidence": {
            "type": evidence_type,
            "data": data,
            "signatures": []  # To be implemented in Sprint 2
        }
    }
    
    # Calculate hash of current evidence
    evidence_str = json.dumps(evidence, sort_keys=True)
    evidence["hash"] = hashlib.sha256(evidence_str.encode()).hexdigest()
    
    evidence_chain.append(evidence)
    return evidence["promotion_id"]

@app.get("/healthz")
async def health_check():
    # Check service-a dependency
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVICE_A_URL}/healthz")
            if response.status_code != 200:
                raise HTTPException(status_code=503, detail="service-a dependency unhealthy")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"service-a dependency check failed: {str(e)}")
    
    return {
        "status": "healthy",
        "mode": COMPLIANCE_MODE,
        "phase": PHASE,
        "dependencies": {
            "service-a": "healthy"
        }
    }

@app.get("/metrics")
async def metrics():
    # Store metrics as evidence
    metrics_data = generate_latest().decode()
    store_evidence("metrics", {"raw": metrics_data, "timestamp": datetime.utcnow().isoformat()})
    return Response(metrics_data, media_type="text/plain")

@app.get("/api/v1/data")
async def get_data():
    # Get data from service-a
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICE_A_URL}/api/v1/data")
        service_a_data = response.json()
    
    # Add our data
    data = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "value": "service-b data",
        "service_a_data": service_a_data
    }
    return data

@app.get("/api/v1/evidence")
async def get_evidence():
    return {"chain": evidence_chain}

@app.post("/api/v1/evidence/{evidence_type}")
async def add_evidence(evidence_type: str, data: dict):
    promotion_id = store_evidence(evidence_type, data)
    return {"status": "success", "promotion_id": promotion_id}

class PromotionRequest:
    def __init__(self, service: str, target_state: str, evidence_refs: List[Dict], dependencies: Dict[str, List[str]]):
        self.service = service
        self.target_state = target_state
        self.evidence_refs = evidence_refs
        self.dependencies = dependencies

@app.post("/api/v1/promote")
async def promote_service(request: dict):
    # Check service-a compliance state
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVICE_A_URL}/healthz")
            service_a_status = response.json()
            
            if service_a_status.get("mode") != "compliant":
                return {
                    "status": "error",
                    "message": "Required dependency service-a is not in compliant state",
                    "details": {
                        "service": "service-a",
                        "current_state": service_a_status.get("mode")
                    }
                }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to check service-a compliance state: {str(e)}"
        }
    
    promotion_request = PromotionRequest(**request)
    
    # Store promotion attempt in evidence chain
    promotion_evidence = {
        "timestamp": datetime.utcnow().isoformat(),
        "request": request,
        "dependencies_state": {
            "service-a": service_a_status
        }
    }
    
    store_evidence("promotion_attempt", promotion_evidence)
    
    return {
        "status": "success",
        "message": "Promotion validation passed",
        "timestamp": promotion_evidence["timestamp"]
    }