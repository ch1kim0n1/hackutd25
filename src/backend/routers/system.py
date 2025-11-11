"""
System Router
Health checks, status monitoring, and system information endpoints.
"""

import os
import psutil
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["system"])


class StatusResponse(BaseModel):
    """Status response model"""
    state: str
    is_paused: bool
    is_running: bool
    error_count: int
    decision_count: int


@router.get("/")
async def root():
    """Basic health check endpoint"""
    return {
        "name": "APEX API",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.
    Returns detailed system status including storage, services, and configuration.
    """
    # Check data storage
    data_dir = Path("data")
    storage_healthy = data_dir.exists() and data_dir.is_dir()

    # Check environment variables
    env_vars_healthy = all([
        os.getenv("JWT_SECRET_KEY"),
        os.getenv("ALPACA_API_KEY"),
        os.getenv("ALPACA_SECRET_KEY"),
    ])

    # System metrics
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('.')

    # Determine overall health
    is_healthy = storage_healthy and env_vars_healthy

    # Import global services to check status
    # Note: These are imported from main app state
    from server import orchestrator, finance_service, voice_service

    health_data = {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "uptime_seconds": (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds(),
        "checks": {
            "storage": {
                "status": "ok" if storage_healthy else "error",
                "data_directory_exists": storage_healthy,
                "path": str(data_dir)
            },
            "environment": {
                "status": "ok" if env_vars_healthy else "error",
                "required_vars_set": env_vars_healthy
            },
            "system": {
                "status": "ok",
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024 * 1024 * 1024),
                "cpu_count": psutil.cpu_count()
            }
        },
        "services": {
            "orchestrator": orchestrator is not None,
            "finance_service": finance_service is not None,
            "voice_service": voice_service is not None,
        }
    }

    status_code = 200 if is_healthy else 503
    return JSONResponse(content=health_data, status_code=status_code)


@router.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get orchestrator status"""
    from server import orchestrator
    from fastapi import HTTPException

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    status = orchestrator.get_status()
    return StatusResponse(
        state=status.get("state", "stopped"),
        is_paused=status.get("is_paused", False),
        is_running=status.get("is_running", False),
        error_count=status.get("error_count", 0),
        decision_count=status.get("decision_count", 0)
    )
