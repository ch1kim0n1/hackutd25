"""
APEX FastAPI Server
Provides REST API and WebSocket endpoints for the frontend
"""

import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import json

from orchestrator import Orchestrator, OrchestratorState
from core.agent_network import AgentNetwork


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class UserInput(BaseModel):
    """User input/feedback model"""
    action: str  # "approve", "reject", "pause", "resume", "comment"
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class StartRequest(BaseModel):
    """Request to start orchestrator"""
    config: Optional[Dict[str, Any]] = None


class StatusResponse(BaseModel):
    """Orchestrator status response"""
    state: str
    is_paused: bool
    is_running: bool
    error_count: int
    decision_count: int


# Create FastAPI app
app = FastAPI(
    title="APEX API",
    description="Multi-Agent Financial Investment System API",
    version="1.0.0"
)

# CORS middleware for Electron frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator: Optional[Orchestrator] = None
orchestrator_task: Optional[asyncio.Task] = None

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


# Background task to relay Redis messages to WebSocket clients
async def redis_to_websocket_relay():
    """Relay messages from Redis pub/sub to WebSocket clients"""
    global orchestrator

    if not orchestrator:
        logger.warning("Orchestrator not initialized, relay cannot start")
        return

    logger.info("🔄 Starting Redis → WebSocket relay")

    while True:
        try:
            # Get recent messages from agent network
            messages = await orchestrator.network.get_message_history(limit=5)

            for msg in messages:
                # Format message for frontend
                formatted_msg = {
                    "type": msg.get("type", "agent_message"),
                    "from": msg.get("from", "system"),
                    "to": msg.get("to", "all"),
                    "content": msg.get("message", ""),
                    "timestamp": msg.get("timestamp", datetime.now().isoformat()),
                    "data": msg.get("data", {})
                }

                # Broadcast to all WebSocket clients
                await manager.broadcast(formatted_msg)

            await asyncio.sleep(0.5)  # Poll every 500ms

        except Exception as e:
            logger.error(f"Error in relay: {e}")
            await asyncio.sleep(1)


# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on server startup"""
    global orchestrator

    logger.info("🚀 Starting APEX API Server...")

    try:
        orchestrator = Orchestrator(redis_url="redis://localhost:6379")
        await orchestrator.initialize()

        # Start Redis→WebSocket relay
        asyncio.create_task(redis_to_websocket_relay())

        logger.info("✅ Server initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize server: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown"""
    global orchestrator, orchestrator_task

    logger.info("🛑 Shutting down APEX API Server...")

    if orchestrator_task:
        orchestrator_task.cancel()

    if orchestrator:
        await orchestrator.stop()

    logger.info("✅ Server shutdown complete")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "name": "APEX API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/status", response_model=StatusResponse)
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


@app.post("/api/start")
async def start_orchestrator(request: StartRequest):
    """Start the orchestrator main loop"""
    global orchestrator, orchestrator_task

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


@app.post("/api/stop")
async def stop_orchestrator():
    """Stop the orchestrator"""
    global orchestrator, orchestrator_task

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    if not orchestrator.is_running:
        return {"message": "Orchestrator not running", "status": "stopped"}

    # Stop orchestrator
    await orchestrator.stop()

    if orchestrator_task:
        orchestrator_task.cancel()

    logger.info("⏹ Orchestrator stopped")

    return {
        "message": "Orchestrator stopped successfully",
        "status": "stopped"
    }


@app.post("/api/pause")
async def pause_orchestrator():
    """Pause the orchestrator (for user interjection)"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    await orchestrator.pause()

    return {
        "message": "Orchestrator paused",
        "status": "paused"
    }


@app.post("/api/resume")
async def resume_orchestrator():
    """Resume the orchestrator after pause"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    await orchestrator.resume()

    return {
        "message": "Orchestrator resumed",
        "status": "running"
    }


@app.post("/api/user-input")
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


@app.get("/api/portfolio")
async def get_portfolio():
    """Get current portfolio state"""
    # TODO: Implement actual portfolio retrieval from database/broker
    # For now, return mock data

    return {
        "total_value": 10000.00,
        "cash": 5000.00,
        "positions": [
            {
                "symbol": "AAPL",
                "shares": 10,
                "current_price": 180.50,
                "value": 1805.00,
                "cost_basis": 175.00,
                "gain_loss": 55.00,
                "gain_loss_pct": 3.14
            }
        ],
        "performance": {
            "day_change": 125.50,
            "day_change_pct": 1.27,
            "total_gain_loss": 500.00,
            "total_gain_loss_pct": 5.26
        }
    }


@app.get("/api/history")
async def get_history(limit: int = 10):
    """Get decision history"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    history = orchestrator.get_decision_history(limit=limit)

    return {
        "count": len(history),
        "decisions": history
    }


@app.get("/api/agents")
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


@app.get("/api/messages")
async def get_messages(limit: int = 50):
    """Get recent agent messages"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    messages = await orchestrator.network.get_message_history(limit=limit)

    return {
        "count": len(messages),
        "messages": messages
    }


# WebSocket endpoint for War Room

@app.websocket("/ws/warroom")
async def warroom_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time War Room updates"""
    await manager.connect(websocket)

    try:
        # Send welcome message
        await manager.send_personal(websocket, {
            "type": "system",
            "from": "system",
            "to": "user",
            "content": "Connected to APEX War Room",
            "timestamp": datetime.now().isoformat()
        })

        # Send recent message history
        if orchestrator:
            recent_messages = await orchestrator.network.get_message_history(limit=20)

            for msg in recent_messages:
                await manager.send_personal(websocket, {
                    "type": msg.get("type", "agent_message"),
                    "from": msg.get("from", "system"),
                    "to": msg.get("to", "all"),
                    "content": msg.get("message", ""),
                    "timestamp": msg.get("timestamp", datetime.now().isoformat()),
                    "data": msg.get("data", {})
                })

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle user messages from War Room
            if message.get("type") == "user_message":
                # Publish to agent network
                if orchestrator:
                    await orchestrator.network.publish(
                        topic="user_input",
                        message={
                            "type": "user_input",
                            "action": "comment",
                            "message": message.get("content", ""),
                            "timestamp": datetime.now().isoformat()
                        }
                    )

                # Broadcast to all clients
                await manager.broadcast({
                    "type": "user_input",
                    "from": "user",
                    "to": "all",
                    "content": message.get("content", ""),
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from War Room")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Error handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
