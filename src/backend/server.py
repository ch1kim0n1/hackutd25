"""
APEX FastAPI Server
Provides REST API and WebSocket endpoints for the frontend
"""

import asyncio
import logging
import io
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import json

from orchestrator import Orchestrator, OrchestratorState
from core.agent_network import AgentNetwork
from services.voice import VoiceService
from engines.crash_simulator import CrashScenario, simulate_crash
from services.personal_finance import PersonalFinanceService
from services.news_search import aggregate_news, web_search


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


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Phase 1 testing"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "phase": "Phase 1 - Foundation"
    }


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "APEX API",
        "description": "Multi-Agent Financial Investment System",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

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
voice_service: Optional[VoiceService] = None
finance_service: Optional[PersonalFinanceService] = None

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
    global orchestrator, voice_service, finance_service

    logger.info("🚀 Starting APEX API Server...")

    try:
        orchestrator = Orchestrator(redis_url="redis://localhost:6379")
        await orchestrator.initialize()

        # Start Redis→WebSocket relay
        asyncio.create_task(redis_to_websocket_relay())

        # Initialize services
        voice_service = VoiceService()
        finance_service = PersonalFinanceService()
        await finance_service.ensure_indexes()

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


# New: Phase 2 - War Room specific endpoints
@app.post("/orchestrator/start")
async def start_war_room_orchestrator(request: StartRequest):
    """Start orchestrator with War Room broadcasting (Phase 2)"""
    global orchestrator, orchestrator_task

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    if orchestrator.is_running:
        return {"message": "Orchestrator already running", "status": "running"}

    # Broadcast start message to War Room
    await manager.broadcast({
        "type": "system",
        "from": "system",
        "to": "all",
        "content": "🚀 Orchestrator starting... Agents assembling for discussion.",
        "timestamp": datetime.now().isoformat(),
        "data": {"config": request.config or {}}
    })

    # Update config if provided
    if request.config:
        orchestrator.config.update(request.config)
        logger.info(f"Config updated: {request.config}")

    # Start orchestrator in background
    orchestrator_task = asyncio.create_task(orchestrator.start())

    logger.info("▶️ Orchestrator started via War Room")

    return {
        "message": "Orchestrator started successfully",
        "status": "running",
        "config": orchestrator.config
    }


@app.post("/orchestrator/stop")
async def stop_war_room_orchestrator():
    """Stop orchestrator with War Room notification"""
    global orchestrator, orchestrator_task

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    if not orchestrator.is_running:
        return {"message": "Orchestrator not running", "status": "stopped"}

    # Broadcast stop message to War Room
    await manager.broadcast({
        "type": "system",
        "from": "system",
        "to": "all",
        "content": "⏹️ Orchestrator stopped. Agent discussion ended.",
        "timestamp": datetime.now().isoformat()
    })

    # Stop orchestrator
    await orchestrator.stop()

    if orchestrator_task:
        orchestrator_task.cancel()

    logger.info("⏹ Orchestrator stopped via War Room")

    return {
        "message": "Orchestrator stopped successfully",
        "status": "stopped"
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


# ===============================
# Voice Interface Endpoints
# ===============================

class TtsRequest(BaseModel):
    text: str
    voice: Optional[str] = None


@app.post("/api/voice/transcribe")
async def voice_transcribe(language: Optional[str] = Form(None), audio: UploadFile = File(...)):
    if not voice_service:
        raise HTTPException(status_code=503, detail="Voice service not initialized")
    content = await audio.read()
    result = await voice_service.transcribe_bytes(content, language=language)
    return result


@app.post("/api/voice/synthesize")
async def voice_synthesize(req: TtsRequest):
    if not voice_service:
        raise HTTPException(status_code=503, detail="Voice service not initialized")
    result = await voice_service.synthesize_speech(req.text, voice=req.voice)
    return StreamingResponse(io.BytesIO(result["audio_bytes"]), media_type=result["mime_type"])


# ===============================
# Crash Simulator Endpoint
# ===============================

class CrashSimRequest(BaseModel):
    symbol: str = "SPY"
    start_price: float = 450.0
    days: int = 60
    mu_annual: float = 0.07
    sigma_annual: float = 0.18
    crash_day: int = 10
    crash_severity: float = 0.25
    recovery_speed: float = 0.05
    recovery_days: int = 20
    seed: Optional[int] = 42


@app.post("/api/simulate/crash")
async def simulate_crash_route(req: CrashSimRequest):
    scenario = CrashScenario(
        symbol=req.symbol,
        start_price=req.start_price,
        days=req.days,
        mu_annual=req.mu_annual,
        sigma_annual=req.sigma_annual,
        crash_day=req.crash_day,
        crash_severity=req.crash_severity,
        recovery_speed=req.recovery_speed,
        recovery_days=req.recovery_days,
        seed=req.seed,
    )
    result = simulate_crash(scenario)
    return result


# ===============================
# Personal Finance Endpoints
# ===============================

class FinanceAccountRequest(BaseModel):
    user_id: str
    name: str
    type: str
    institution: Optional[str] = None
    balance: float = 0.0


class FinanceImportRequest(BaseModel):
    user_id: str
    items: List[Dict[str, Any]]


@app.post("/api/finance/accounts")
async def finance_add_account(req: FinanceAccountRequest):
    if not finance_service:
        raise HTTPException(status_code=503, detail="Finance service not initialized")
    created = await finance_service.add_account(
        user_id=req.user_id,
        name=req.name,
        type=req.type,
        institution=req.institution,
        balance=req.balance
    )
    return created


@app.get("/api/finance/accounts")
async def finance_list_accounts(user_id: str = Query(...)):
    if not finance_service:
        raise HTTPException(status_code=503, detail="Finance service not initialized")
    items = await finance_service.list_accounts(user_id=user_id)
    return {"accounts": items, "count": len(items)}


@app.post("/api/finance/transactions/import")
async def finance_import_transactions(req: FinanceImportRequest):
    if not finance_service:
        raise HTTPException(status_code=503, detail="Finance service not initialized")
    result = await finance_service.import_transactions(user_id=req.user_id, items=req.items)
    return result


@app.get("/api/finance/transactions")
async def finance_list_transactions(
    user_id: str = Query(...),
    account_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    limit: int = Query(200)
):
    if not finance_service:
        raise HTTPException(status_code=503, detail="Finance service not initialized")
    items = await finance_service.list_transactions(
        user_id=user_id,
        account_id=account_id,
        category=category,
        start=start,
        end=end,
        limit=limit
    )
    return {"transactions": items, "count": len(items)}


@app.get("/api/finance/summary/spending")
async def finance_spending_summary(user_id: str = Query(...), month: Optional[str] = Query(None)):
    if not finance_service:
        raise HTTPException(status_code=503, detail="Finance service not initialized")
    data = await finance_service.spending_summary_by_category(user_id=user_id, month=month)
    return {"spending": data}


@app.get("/api/finance/summary/cashflow")
async def finance_cashflow_summary(user_id: str = Query(...), month: Optional[str] = Query(None)):
    if not finance_service:
        raise HTTPException(status_code=503, detail="Finance service not initialized")
    data = await finance_service.cashflow_summary(user_id=user_id, month=month)
    return data


# ===============================
# News & Search Endpoints
# ===============================

@app.get("/api/news")
async def news_endpoint(
    query: Optional[str] = Query(None, alias="q"),
    symbols_csv: Optional[str] = Query(None, alias="symbols"),
    max_results: int = Query(50)
):
    symbols = [s.strip().upper() for s in symbols_csv.split(",")] if symbols_csv else None
    articles = await aggregate_news(query=query, symbols=symbols, max_results=max_results)
    return {"articles": articles, "count": len(articles)}


@app.get("/api/search")
async def search_endpoint(q: str = Query(...), max_results: int = Query(20)):
    results = await web_search(q, max_results=max_results)
    return {"results": results, "count": len(results)}


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
