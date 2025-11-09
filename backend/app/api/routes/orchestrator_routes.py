"""
Orchestrator API routes
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import json
import logging

from app.api.routes import orchestrator, war_room

router = APIRouter()
logger = logging.getLogger(__name__)


class StartRequest(BaseModel):
    """Request to start orchestrator"""
    config: Optional[Dict[str, Any]] = None


class UserInput(BaseModel):
    """User input/feedback model"""
    action: str  # "approve", "reject", "pause", "resume", "comment"
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class StatusResponse(BaseModel):
    """Orchestrator status response"""
    state: str
    is_paused: bool
    is_running: bool
    error_count: int
    decision_count: int


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for War Room"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.message_queue: asyncio.Queue = asyncio.Queue()

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            self.active_connections.remove(conn)

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")


manager = ConnectionManager()


@router.post("/start")
async def start_orchestrator(request: StartRequest):
    """Start the orchestrator main loop"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    if orchestrator.is_running:
        return {"message": "Orchestrator already running", "status": "running"}

    # Update config if provided
    if request.config:
        orchestrator.config.update(request.config)

    # Start orchestrator in background
    orchestrator_task = asyncio.create_task(orchestrator.start())

    logger.info("▶️ Orchestrator started")

    return {
        "message": "Orchestrator started successfully",
        "status": "running",
        "config": orchestrator.config
    }


@router.post("/stop")
async def stop_orchestrator():
    """Stop the orchestrator"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    if not orchestrator.is_running:
        return {"message": "Orchestrator not running", "status": "stopped"}

    # Stop orchestrator
    await orchestrator.stop()

    logger.info("⏹ Orchestrator stopped")

    return {
        "message": "Orchestrator stopped successfully",
        "status": "stopped"
    }


@router.post("/pause")
async def pause_orchestrator():
    """Pause the orchestrator (for user interjection)"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    await orchestrator.pause()

    await manager.broadcast({
        "type": "system",
        "from": "system",
        "to": "all",
        "content": "⏸️ User interjection detected - Agents paused",
        "timestamp": datetime.now().isoformat()
    })

    return {
        "message": "Orchestrator paused",
        "status": "paused"
    }


@router.post("/resume")
async def resume_orchestrator():
    """Resume the orchestrator after pause"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    await orchestrator.resume()

    await manager.broadcast({
        "type": "system",
        "from": "system",
        "to": "all",
        "content": "▶️ Agents resuming with updated context",
        "timestamp": datetime.now().isoformat()
    })

    return {
        "message": "Orchestrator resumed",
        "status": "running"
    }


@router.post("/user-input")
async def submit_user_input(input_data: UserInput):
    """Submit user input/feedback to the system"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    # Publish user input to agent network
    await orchestrator.network.publish(
        topic="user_input",
        message={
            "type": "user_input",
            "action": input_data.action,
            "message": input_data.message,
            "data": input_data.data or {},
            "timestamp": datetime.now().isoformat()
        }
    )

    # Broadcast to War Room
    await manager.broadcast({
        "type": "user_input",
        "from": "user",
        "to": "all",
        "content": input_data.message or input_data.action,
        "timestamp": datetime.now().isoformat(),
        "data": {"action": input_data.action}
    })

    logger.info(f"User input received: {input_data.action}")

    return {
        "message": "User input received",
        "action": input_data.action
    }


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get orchestrator status"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    status = orchestrator.get_status()

    return StatusResponse(
        state=status["state"],
        is_paused=status["is_paused"],
        is_running=status["is_running"],
        error_count=status["error_count"],
        decision_count=status["decision_count"]
    )


@router.get("/messages")
async def get_messages(limit: int = 50):
    """Get recent agent messages"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    messages = await orchestrator.network.get_message_history(limit=limit)

    return {
        "count": len(messages),
        "messages": messages
    }


@router.get("/agents")
async def get_agents():
    """Get status of all agents"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    agents_status = {}

    for name, agent in orchestrator.agents.items():
        if agent:
            agents_status[name] = {
                "name": name,
                "status": "active",
                "type": agent.__class__.__name__
            }
        else:
            agents_status[name] = {
                "name": name,
                "status": "not_initialized",
                "type": None
            }

    return {
        "count": len(agents_status),
        "agents": agents_status
    }


@router.get("/history")
async def get_history(limit: int = 10):
    """Get decision history"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    history = orchestrator.get_decision_history(limit=limit)

    return {
        "count": len(history),
        "decisions": history
    }
