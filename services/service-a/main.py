from fastapi import FastAPI, Response
from prometheus_client import generate_latest
import json
import time
import uuid
from datetime import datetime
import hashlib
from metrics import init_metrics

app = FastAPI()

# Initialize metrics collection
init_metrics(app)

# Evidence chain storage
evidence_chain = []

def store_evidence(evidence_type: str, data: dict) -> str:
    """Store evidence in the chain with hash linking"""
    timestamp = datetime.utcnow().isoformat()
    previous_hash = evidence_chain[-1]["hash"] if evidence_chain else "0" * 64
    
    evidence = {
        "promotion_id": str(uuid.uuid4()),
        "timestamp": timestamp,
        "service": "service-a",
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
    return {"status": "healthy", "mode": "sandbox", "phase": "poc"}

@app.get("/metrics")
async def metrics():
    # Store metrics as evidence
    metrics_data = generate_latest().decode()
    store_evidence("metrics", {"raw": metrics_data, "timestamp": datetime.utcnow().isoformat()})
    return Response(metrics_data, media_type="text/plain")

@app.get("/api/v1/data")
async def get_data():
    # Sample data endpoint
    data = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "value": "sample data"
    }
    return data

@app.get("/api/v1/evidence")
async def get_evidence():
    return {"chain": evidence_chain}

@app.post("/api/v1/evidence/{evidence_type}")
async def add_evidence(evidence_type: str, data: dict):
    promotion_id = store_evidence(evidence_type, data)
    return {"status": "success", "promotion_id": promotion_id}

# Import promotion and validation components
from promotion import PromotionManager, PromotionRequest
from validation_gates import ValidationGatekeeper

# Initialize components
promotion_manager = PromotionManager()
validation_gatekeeper = ValidationGatekeeper()

@app.post("/api/v1/promote")
async def promote_service(request: PromotionRequest):
    # Validate through gates
    validation_context = {
        "evidence_chain": evidence_chain,
        "dependencies": request.dependencies.dict()
    }
    
    gate_results = validation_gatekeeper.validate_all(validation_context)
    
    # Check if any blocking gates failed
    blocking_failures = [
        result for result in gate_results
        if result["type"] == "blocking" and not result["result"]["valid"]
    ]
    
    if blocking_failures:
        return {
            "status": "error",
            "message": "Blocking validations failed",
            "details": blocking_failures
        }
    
    # Process promotion
    result = promotion_manager.request_promotion(request)
    
    # Store promotion result in evidence chain
    store_evidence("promotion", {
        "request": request.dict(),
        "gate_results": gate_results,
        "result": result
    })
    
    return result
    start_time = time.time()
    try:
        result = {
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "data": "sample data",
            "metadata": {
                "phase": "poc",
                "compliance_mode": "sandbox",
                "mesh_enforcement": "pending"
            }
        }
        REQUEST_COUNT.labels(
            method='GET',
            endpoint='/api/v1/data',
            status='200'
        ).inc()
        return result
    finally:
        REQUEST_LATENCY.labels(
            method='GET',
            endpoint='/api/v1/data'
        ).observe(time.time() - start_time)