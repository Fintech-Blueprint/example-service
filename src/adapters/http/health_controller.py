from fastapi import APIRouter, Depends, Header
from typing import Optional
import subprocess

router = APIRouter()

@router.get("/healthz")
async def health_check(authorization: Optional[str] = Header(None)):
    """Health check endpoint for smoke tests."""
    try:
        # Get git commit for service version
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
    except:
        commit = "unknown"
        
    return {
        "status": "healthy",
        "version": "1.0.0",
        "commit": commit,
        "timestamp": "2025-09-24T13:00:00Z"  # Note: Using static timestamp for determinism
    }