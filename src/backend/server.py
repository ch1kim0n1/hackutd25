"""
APEX FastAPI Server
Provides REST API and WebSocket endpoints with security hardening
"""

import asyncio
import logging
import io
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form, Query, Depends, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
import json

from orchestrator import Orchestrator, OrchestratorState
from core.agent_network import AgentNetwork
from services.voice import VoiceService
from engines.crash_simulator import CrashScenario, simulate_crash
from engines.crash_scenario_engine import CrashScenarioEngine
from services.news_search import aggregate_news, web_search
from services.mock_plaid import mock_plaid_data
from services.news_aggregator import news_aggregator
from integrations.alpaca_broker import AlpacaBroker
from war_room_interface import WarRoomInterface
from services.rag.chroma_service import ChromaService
from services.rag.query_engine import RAGQueryEngine
from services.finance_adapter import FinanceAdapter
from services.logging_service import logger as structured_logger, RequestLogger
from middleware.exception_handler import setup_exception_handlers
from api.auth import get_current_user, login_user, refresh_access_token, logout_user
from services.historical_data import HistoricalDataLoader


# Initialize logging
logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


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


# Create FastAPI app with enhanced security
app = FastAPI(
    title="APEX API",
    description="Multi-Agent Financial Investment System API",
    version="2.0.0"
)

# Setup global exception handlers
setup_exception_handlers(app)

# HTTPS enforcement (enable in production)
if os.getenv("FORCE_HTTPS", "false").lower() == "true":
    app.add_middleware(HTTPSRedirectMiddleware)

# CORS middleware - restrict to frontend origins
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    frontend_url,
]

if os.getenv("ENVIRONMENT") == "development":
    # Allow all in development (careful!)
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID"],
    max_age=600,  # Cache CORS preflight for 10 minutes
)

# Global orchestrator instance
orchestrator: Optional[Orchestrator] = None
orchestrator_task: Optional[asyncio.Task] = None
voice_service: Optional[Any] = None
finance_service: Optional[Any] = None
crash_engine: Optional[CrashScenarioEngine] = None
crash_simulation_task: Optional[asyncio.Task] = None
alpaca_broker: Optional[Any] = None
war_room: Optional[Any] = None
chroma_service: Optional[Any] = None
rag_engine: Optional[Any] = None
finance_adapter: Optional[Any] = None

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
        # Initialize database schema and run migrations
        from services.postgres_db import init_db
        logger.info("📊 Initializing database schema...")
        await init_db()
        logger.info("✅ Database initialized")
        
        # Seed test data if needed
        from services.seed_data import seed_test_data
        logger.info("🌱 Seeding test data...")
        await seed_test_data()
        logger.info("✅ Test data seeded")
        
        orchestrator = Orchestrator(redis_url="redis://localhost:6379")
        await orchestrator.initialize()

        asyncio.create_task(redis_to_websocket_relay())

        # Lazy import voice and personal finance services to avoid hard dependency during demo
        try:
            from services.voice import VoiceService as _VoiceService
            voice_service = _VoiceService()
        except Exception as ve:
            logger.warning(f"Voice service unavailable: {ve}")

        try:
            from services.personal_finance import PersonalFinanceService as _PersonalFinanceService
            finance_service = _PersonalFinanceService()
        except Exception as fe:
            logger.warning(f"Personal finance service unavailable: {fe}")
            finance_service = None

        await finance_service.ensure_indexes()
        
        alpaca_broker = AlpacaBroker(paper=True)
        await alpaca_broker.initialize()
        
        data_loader = HistoricalDataLoader()
        crash_engine = CrashScenarioEngine(data_loader)

        logger.info("✅ Server initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize server: {e}")
        # Do not crash the server during demo; continue with limited functionality
        return


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown"""
    global orchestrator, orchestrator_task

    logger.info("🛑 Shutting down APEX API Server...")

    if orchestrator_task:
        orchestrator_task.cancel()

    if orchestrator:
        await orchestrator.stop()

    # Close database connections
    from services.postgres_db import close_db
    await close_db()
    
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


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/auth/login")
async def login(request: LoginRequest):
    """
    Authenticate user and return access + refresh tokens
    
    Request body:
        {
            "username": "user@example.com",
            "password": "secure_password"
        }
    
    Returns:
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer",
            "expires_in": 900
        }
    """
    from services.auth import login_user
    return await login_user(request.username, request.password)


@app.post("/auth/refresh")
async def refresh(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    
    Request body:
        {
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
        }
    
    Returns:
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer",
            "expires_in": 900
        }
    """
    from services.auth import refresh_access_token
    return await refresh_access_token(request.refresh_token)


@app.post("/auth/logout")
async def logout(background_tasks: BackgroundTasks, request: Request):
    """
    Logout user by revoking their access token
    
    Header:
        Authorization: Bearer <access_token>
    
    Returns:
        {
            "message": "Successfully logged out"
        }
    """
    from services.auth import logout_user
    
    auth_header = request.headers.get("authorization", "")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token_str = auth_header[7:]
    await logout_user(token_str)
    
    return {"message": "Successfully logged out"}


@app.get("/auth/me")
async def get_me(request: Request):
    """
    Get current authenticated user info
    
    Header:
        Authorization: Bearer <access_token>
    
    Returns:
        {
            "id": "uuid",
            "username": "user@example.com",
            "email": "user@example.com",
            "created_at": "2024-01-01T00:00:00Z"
        }
    """
    from services.auth import get_current_user
    
    auth_header = request.headers.get("authorization", "")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token_str = auth_header[7:]
    user = await get_current_user(token_str)
    
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }


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


@app.post("/orchestrator/pause")
async def pause_war_room_orchestrator():
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
    
    return {"message": "Orchestrator paused", "status": "paused"}


@app.post("/orchestrator/resume")
async def resume_war_room_orchestrator():
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
    
    return {"message": "Orchestrator resumed", "status": "running"}


@app.post("/user-input")
async def submit_user_voice_input(input_data: UserInput):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    await manager.broadcast({
        "type": "user_message",
        "from": "user",
        "to": "all",
        "content": input_data.message or "",
        "timestamp": datetime.now().isoformat(),
        "data": input_data.data or {}
    })
    
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
    
    return {"message": "User input received", "status": "success"}


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
async def get_portfolio(request: Request, auth_data: dict = Depends(lambda: None)):
    """
    Get user's portfolio information.
    
    Requires authentication header:
        Authorization: Bearer <access_token>
    """
    from middleware.auth import get_current_user_from_request
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    if not alpaca_broker:
        raise HTTPException(status_code=503, detail="Alpaca broker not initialized")
    
    try:
        RequestLogger.log_request(
            structured_logger,
            "get_portfolio",
            user_id=str(user_id)
        )
        
        account = await alpaca_broker.get_account()
        positions = await alpaca_broker.get_positions()
        
        total_pl = sum(float(pos.get('unrealized_pl', 0)) for pos in positions) if isinstance(positions, list) else 0
        total_value = account.get('portfolio_value', 0)
        initial_value = float(total_value) - total_pl
        
        return {
            "total_value": total_value,
            "day_return": total_pl / initial_value * 100 if initial_value > 0 else 0,
            "total_return": (float(total_value) - 100000) / 100000 * 100,
        }
    except Exception as e:
        logger.error(f"Error fetching portfolio for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/account")
async def get_account():
    if not alpaca_broker:
        raise HTTPException(status_code=503, detail="Alpaca broker not initialized")
    
    try:
        account = await alpaca_broker.get_account()
        return {
            "portfolio_value": account.get('portfolio_value', 0),
            "cash": account.get('cash', 0),
            "buying_power": account.get('buying_power', 0),
            "equity": account.get('equity', 0),
            "status": "ACTIVE"
        }
    except Exception as e:
        logger.error(f"Error fetching account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/positions")
async def get_positions():
    if not alpaca_broker:
        raise HTTPException(status_code=503, detail="Alpaca broker not initialized")
    
    try:
        positions = await alpaca_broker.get_positions()
        if isinstance(positions, dict) and 'error' in positions:
            return []
        
        return [
            {
                "symbol": pos['symbol'],
                "qty": pos['qty'],
                "avg_entry_price": pos.get('avg_fill_price', 0),
                "current_price": pos.get('current_price', 0),
                "market_value": pos.get('market_value', 0),
                "unrealized_pl": pos.get('unrealized_pl', 0),
                "unrealized_plpc": pos.get('unrealized_plpc', 0),
                "side": "long"
            }
            for pos in positions
        ]
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        return []


@app.get("/api/orders")
async def get_orders():
    if not alpaca_broker:
        raise HTTPException(status_code=503, detail="Alpaca broker not initialized")
    
    try:
        orders = await alpaca_broker.get_orders()
        if isinstance(orders, dict) and 'error' in orders:
            return []
        return orders
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        return []


class TradeRequest(BaseModel):
    symbol: str
    side: str
    qty: float
    type: str = 'market'
    time_in_force: str = 'day'
    limit_price: Optional[float] = None


@app.post("/api/trade")
async def place_trade(request: Request, trade: TradeRequest, auth_data: dict = Depends(lambda: None)):
    """
    Place a buy or sell order.
    
    Requires authentication header:
        Authorization: Bearer <access_token>
    """
    from middleware.auth import get_current_user_from_request
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    if not alpaca_broker:
        raise HTTPException(status_code=503, detail="Alpaca broker not initialized")
    
    try:
        # Log trade request with user context
        RequestLogger.log_request(
            structured_logger,
            "place_trade",
            user_id=str(user_id),
            data={"symbol": trade.symbol, "qty": trade.qty, "side": trade.side}
        )
        
        if trade.side == 'buy':
            result = await alpaca_broker.buy(
                symbol=trade.symbol,
                qty=int(trade.qty),
                order_type=trade.type,
                limit_price=trade.limit_price
            )
        else:
            result = await alpaca_broker.sell(
                symbol=trade.symbol,
                qty=int(trade.qty),
                order_type=trade.type,
                limit_price=trade.limit_price
            )
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        await manager.broadcast({
            "type": "executor",
            "from": "executor",
            "to": "all",
            "content": f"⚡ Order placed: {trade.side.upper()} {trade.qty} {trade.symbol} @ {trade.type.upper()}",
            "timestamp": datetime.now().isoformat(),
            "data": {"order": result}
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing trade for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/finance/accounts")
async def get_finance_accounts(request: Request, auth_data: dict = Depends(lambda: None)):
    """Get user's financial accounts (requires authentication)"""
    from middleware.auth import get_current_user_from_request
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    RequestLogger.log_request(structured_logger, "get_finance_accounts", user_id=str(user_id))
    
    if not finance_adapter:
        accounts = mock_plaid_data.get_accounts()
    else:
        accounts = await finance_adapter.get_accounts()
    return {"accounts": accounts, "count": len(accounts)}


@app.get("/api/finance/transactions")
async def get_finance_transactions(request: Request, days: int = 90, auth_data: dict = Depends(lambda: None)):
    """Get user's financial transactions (requires authentication)"""
    from middleware.auth import get_current_user_from_request
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    RequestLogger.log_request(structured_logger, "get_finance_transactions", user_id=str(user_id))
    
    if not finance_adapter:
        transactions = mock_plaid_data.get_transactions(days)
    else:
        transactions = await finance_adapter.get_transactions(days)
    return {"transactions": transactions, "count": len(transactions)}


@app.get("/api/finance/subscriptions")
async def get_subscriptions(request: Request, auth_data: dict = Depends(lambda: None)):
    """Get user's subscriptions (requires authentication)"""
    from middleware.auth import get_current_user_from_request
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    RequestLogger.log_request(structured_logger, "get_subscriptions", user_id=str(user_id))
    
    if not finance_adapter:
        subscriptions = mock_plaid_data.get_subscriptions()
    else:
        subscriptions = await finance_adapter.get_subscriptions()
    
    total_annual = sum(sub['annual_cost'] for sub in subscriptions)
    return {
        "subscriptions": subscriptions,
        "count": len(subscriptions),
        "total_monthly": total_annual / 12,
        "total_annual": total_annual
    }


@app.get("/api/finance/net-worth")
async def get_net_worth(request: Request, auth_data: dict = Depends(lambda: None)):
    """Get user's net worth (requires authentication)"""
    from middleware.auth import get_current_user_from_request
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    RequestLogger.log_request(structured_logger, "get_net_worth", user_id=str(user_id))
    
    if not finance_adapter:
        return mock_plaid_data.get_net_worth()
    return finance_adapter.get_net_worth()


@app.get("/api/finance/cash-flow")
async def get_cash_flow(request: Request, days: int = 30, auth_data: dict = Depends(lambda: None)):
    """Get user's cash flow (requires authentication)"""
    from middleware.auth import get_current_user_from_request
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    RequestLogger.log_request(structured_logger, "get_cash_flow", user_id=str(user_id))
    
    if not finance_adapter:
        return mock_plaid_data.get_cash_flow(days)
    return finance_adapter.get_cash_flow(days)


@app.get("/api/finance/health-score")
async def get_health_score(request: Request, auth_data: dict = Depends(lambda: None)):
    """Get user's financial health score (requires authentication)"""
    from middleware.auth import get_current_user_from_request
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    RequestLogger.log_request(structured_logger, "get_health_score", user_id=str(user_id))
    
    if not finance_adapter:
        return mock_plaid_data.calculate_health_score()
    return finance_adapter.calculate_health_score()


@app.get("/api/finance/adapter-status")
async def get_finance_status():
    """Get status of finance adapter (real Plaid or mock)"""
    if not finance_adapter:
        return {"status": "not_initialized", "mode": "unknown"}
    return finance_adapter.get_status()


# ============================================================================
# Plaid Integration Endpoints
# ============================================================================

@app.post("/api/plaid/create-link-token")
async def create_plaid_link_token(
    request: Request,
    redirect_uri: Optional[str] = None,
    auth_data: dict = Depends(lambda: None)
):
    """
    Create a Plaid Link token for account connection flow.
    
    Returns a link_token that can be used to launch Plaid Link UI.
    
    Requires authentication header:
        Authorization: Bearer <access_token>
    """
    from middleware.auth import get_current_user_from_request
    from services.plaid_integration import PlaidIntegration
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    try:
        plaid = PlaidIntegration()
        token_data = await plaid.create_link_token(str(user_id), redirect_uri)
        
        RequestLogger.log_request(
            structured_logger,
            "create_plaid_link_token",
            user_id=str(user_id)
        )
        
        return token_data
        
    except Exception as e:
        logger.error(f"Failed to create Plaid link token: {e}")
        raise HTTPException(status_code=500, detail="Failed to create link token")


@app.post("/api/plaid/exchange-token")
async def exchange_plaid_token(
    request: Request,
    public_token: str,
    auth_data: dict = Depends(lambda: None)
):
    """
    Exchange Plaid public token for access token and save credentials.
    
    Called after user connects account in Plaid Link.
    Stores encrypted access token in user's account.
    
    Requires authentication header:
        Authorization: Bearer <access_token>
    """
    from middleware.auth import get_current_user_from_request
    from services.plaid_integration import PlaidIntegration
    from services.postgres_db import AsyncSessionLocal
    from services.dao.user_dao import UserDAO
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    try:
        plaid = PlaidIntegration()
        access_token = await plaid.exchange_public_token(str(user_id), public_token)
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Token exchange failed")
        
        # Store encrypted access token
        async with AsyncSessionLocal() as db:
            await UserDAO.set_encrypted_credential(
                db,
                user_id,
                "plaid_token",
                access_token
            )
        
        RequestLogger.log_request(
            structured_logger,
            "exchange_plaid_token",
            user_id=str(user_id)
        )
        
        return {
            "status": "success",
            "message": "Plaid account connected successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        raise HTTPException(status_code=500, detail="Failed to exchange token")


@app.get("/api/plaid/accounts")
async def get_plaid_accounts(
    request: Request,
    auth_data: dict = Depends(lambda: None)
):
    """
    Retrieve linked bank accounts from Plaid.
    
    Requires authentication header:
        Authorization: Bearer <access_token>
    """
    from middleware.auth import get_current_user_from_request
    from services.plaid_integration import PlaidIntegration
    from services.postgres_db import AsyncSessionLocal
    from services.dao.user_dao import UserDAO
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    try:
        # Get stored Plaid access token
        async with AsyncSessionLocal() as db:
            plaid_token = await UserDAO.get_encrypted_credential(
                db,
                user_id,
                "plaid_token"
            )
        
        if not plaid_token:
            return {
                "accounts": [],
                "message": "No Plaid account connected. Use /api/plaid/create-link-token first."
            }
        
        plaid = PlaidIntegration()
        accounts = await plaid.get_accounts(str(user_id), plaid_token)
        
        RequestLogger.log_request(
            structured_logger,
            "get_plaid_accounts",
            user_id=str(user_id),
            data={"account_count": len(accounts)}
        )
        
        return {
            "accounts": accounts,
            "count": len(accounts)
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch Plaid accounts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch accounts")


@app.get("/api/plaid/transactions")
async def get_plaid_transactions(
    request: Request,
    days: int = 90,
    auth_data: dict = Depends(lambda: None)
):
    """
    Retrieve transactions from linked bank accounts via Plaid.
    
    Args:
        days: Number of days of history to retrieve (default 90, max 730)
    
    Requires authentication header:
        Authorization: Bearer <access_token>
    """
    from middleware.auth import get_current_user_from_request
    from services.plaid_integration import PlaidIntegration
    from services.postgres_db import AsyncSessionLocal
    from services.dao.user_dao import UserDAO
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    # Validate days parameter
    if days < 1 or days > 730:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 730")
    
    try:
        # Get stored Plaid access token
        async with AsyncSessionLocal() as db:
            plaid_token = await UserDAO.get_encrypted_credential(
                db,
                user_id,
                "plaid_token"
            )
        
        if not plaid_token:
            return {
                "transactions": [],
                "message": "No Plaid account connected"
            }
        
        plaid = PlaidIntegration()
        transactions = await plaid.get_transactions(str(user_id), plaid_token, days)
        
        RequestLogger.log_request(
            structured_logger,
            "get_plaid_transactions",
            user_id=str(user_id),
            data={"transaction_count": len(transactions), "days": days}
        )
        
        return {
            "transactions": transactions,
            "count": len(transactions),
            "days": days
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch Plaid transactions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch transactions")


@app.get("/api/plaid/status")
async def get_plaid_status(request: Request):
    """Get Plaid integration status (no auth required for status check)"""
    from services.plaid_integration import PlaidIntegration
    
    try:
        plaid = PlaidIntegration()
        return plaid.get_status()
    except Exception as e:
        logger.error(f"Failed to get Plaid status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")


# ============================================================================
# Goal Planner Endpoints (CRUD + Risk Assessment)
# ============================================================================

@app.post("/api/goals")
async def create_goal(
    request: Request,
    name: str,
    target_amount: float,
    target_date: str,  # ISO format: 2024-12-31
    category: str,
    description: str = None,
    priority: str = "medium",
    auth_data: dict = Depends(lambda: None)
):
    """
    Create a new financial goal.
    
    Args:
        name: Goal name (e.g., "Home Down Payment")
        target_amount: Target amount in USD
        target_date: Target date in ISO format (YYYY-MM-DD)
        category: Category (retirement, housing, travel, education, etc.)
        description: Optional goal description
        priority: Priority level (low, medium, high)
    
    Requires authentication header:
        Authorization: Bearer <access_token>
    """
    from middleware.auth import get_current_user_from_request
    from services.dao.goal_dao import GoalDAO
    from services.postgres_db import AsyncSessionLocal
    from datetime import datetime as dt
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    try:
        # Parse target date
        try:
            target_dt = dt.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        async with AsyncSessionLocal() as db:
            goal = await GoalDAO.create(
                db,
                user_id=user_id,
                name=name,
                target_amount=Decimal(str(target_amount)),
                target_date=target_dt,
                category=category,
                description=description,
                priority=priority
            )
        
        RequestLogger.log_request(
            structured_logger,
            "create_goal",
            user_id=str(user_id),
            data={"goal_name": name, "target": target_amount}
        )
        
        return {
            "id": str(goal.id),
            "name": goal.name,
            "target_amount": float(goal.target_amount),
            "target_date": goal.target_date.isoformat(),
            "category": goal.category,
            "status": "active",
            "created_at": goal.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Goal creation error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create goal")


@app.get("/api/goals")
async def get_user_goals(
    request: Request,
    status: str = None,
    auth_data: dict = Depends(lambda: None)
):
    """
    Get all goals for the user.
    
    Args:
        status: Optional filter by status (active, completed, paused)
    
    Requires authentication header:
        Authorization: Bearer <access_token>
    """
    from middleware.auth import get_current_user_from_request
    from services.dao.goal_dao import GoalDAO
    from services.postgres_db import AsyncSessionLocal
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    try:
        async with AsyncSessionLocal() as db:
            if status:
                goals = await GoalDAO.get_by_user_and_status(db, user_id, status)
            else:
                goals = await GoalDAO.get_by_user(db, user_id)
        
        return {
            "goals": [
                {
                    "id": str(g.id),
                    "name": g.name,
                    "target_amount": float(g.target_amount),
                    "current_amount": float(g.current_amount),
                    "target_date": g.target_date.isoformat(),
                    "category": g.category,
                    "priority": g.priority,
                    "status": g.status,
                    "progress_pct": float((g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0)
                }
                for g in goals
            ],
            "count": len(goals)
        }
        
    except Exception as e:
        logger.error(f"Error fetching goals: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch goals")


@app.get("/api/goals/{goal_id}")
async def get_goal(
    goal_id: str,
    request: Request,
    auth_data: dict = Depends(lambda: None)
):
    """Get a specific goal with full details"""
    from middleware.auth import get_current_user_from_request
    from services.dao.goal_dao import GoalDAO
    from services.postgres_db import AsyncSessionLocal
    from uuid import UUID
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    try:
        async with AsyncSessionLocal() as db:
            goal = await GoalDAO.get_by_id(db, UUID(goal_id))
        
        if not goal or str(goal.user_id) != str(user_id):
            raise HTTPException(status_code=404, detail="Goal not found")
        
        return {
            "id": str(goal.id),
            "name": goal.name,
            "description": goal.description,
            "target_amount": float(goal.target_amount),
            "current_amount": float(goal.current_amount),
            "target_date": goal.target_date.isoformat(),
            "category": goal.category,
            "priority": goal.priority,
            "status": goal.status,
            "progress_pct": float((goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0),
            "risk_assessment": goal.risk_assessment,
            "strategy_recommendation": goal.strategy_recommendation,
            "created_at": goal.created_at.isoformat(),
            "updated_at": goal.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching goal: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch goal")


@app.put("/api/goals/{goal_id}")
async def update_goal(
    goal_id: str,
    request: Request,
    name: str = None,
    target_amount: float = None,
    target_date: str = None,
    priority: str = None,
    status: str = None,
    description: str = None,
    auth_data: dict = Depends(lambda: None)
):
    """Update a goal"""
    from middleware.auth import get_current_user_from_request
    from services.dao.goal_dao import GoalDAO
    from services.postgres_db import AsyncSessionLocal
    from uuid import UUID
    from datetime import datetime as dt
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    try:
        # Build update dict
        update_data = {}
        if name:
            update_data["name"] = name
        if target_amount:
            update_data["target_amount"] = Decimal(str(target_amount))
        if target_date:
            try:
                update_data["target_date"] = dt.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format")
        if priority:
            update_data["priority"] = priority
        if status:
            update_data["status"] = status
        if description is not None:
            update_data["description"] = description
        
        async with AsyncSessionLocal() as db:
            goal = await GoalDAO.update(db, UUID(goal_id), user_id, **update_data)
        
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found or unauthorized")
        
        RequestLogger.log_request(
            structured_logger,
            "update_goal",
            user_id=str(user_id),
            data={"goal_id": goal_id}
        )
        
        return {
            "id": str(goal.id),
            "name": goal.name,
            "status": goal.status,
            "message": "Goal updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating goal: {e}")
        raise HTTPException(status_code=500, detail="Failed to update goal")


@app.delete("/api/goals/{goal_id}")
async def delete_goal(
    goal_id: str,
    request: Request,
    auth_data: dict = Depends(lambda: None)
):
    """Delete a goal"""
    from middleware.auth import get_current_user_from_request
    from services.dao.goal_dao import GoalDAO
    from services.postgres_db import AsyncSessionLocal
    from uuid import UUID
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    try:
        async with AsyncSessionLocal() as db:
            success = await GoalDAO.delete(db, UUID(goal_id), user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Goal not found or unauthorized")
        
        RequestLogger.log_request(
            structured_logger,
            "delete_goal",
            user_id=str(user_id),
            data={"goal_id": goal_id}
        )
        
        return {"message": "Goal deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting goal: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete goal")


@app.put("/api/goals/{goal_id}/progress")
async def update_goal_progress(
    goal_id: str,
    current_amount: float,
    request: Request,
    auth_data: dict = Depends(lambda: None)
):
    """Update goal progress (current amount saved)"""
    from middleware.auth import get_current_user_from_request
    from services.dao.goal_dao import GoalDAO
    from services.postgres_db import AsyncSessionLocal
    from uuid import UUID
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    try:
        async with AsyncSessionLocal() as db:
            goal = await GoalDAO.update_progress(
                db,
                UUID(goal_id),
                user_id,
                Decimal(str(current_amount))
            )
        
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        progress_pct = float((goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0)
        
        return {
            "id": str(goal.id),
            "current_amount": float(goal.current_amount),
            "target_amount": float(goal.target_amount),
            "progress_pct": progress_pct,
            "message": f"Progress updated: {progress_pct:.1f}%"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating goal progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to update progress")


@app.get("/api/news")
async def get_news(limit: int = 10):
    headlines = news_aggregator.get_headlines(limit)
    return {"news": headlines, "count": len(headlines)}


@app.get("/api/news/search")
async def search_news(q: str):
    results = news_aggregator.search_news(q)
    return {"news": results, "count": len(results)}


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


class VoiceCommandRequest(BaseModel):
    text: str


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


@app.post("/api/voice/detect-activity")
async def voice_detect_activity(audio: UploadFile = File(...)):
    """Detect if audio contains speech (Voice Activity Detection)"""
    if not voice_service:
        raise HTTPException(status_code=503, detail="Voice service not initialized")
    content = await audio.read()
    result = voice_service.detect_voice_activity(content)
    return result


@app.post("/api/voice/denoise")
async def voice_denoise(audio: UploadFile = File(...)):
    """Reduce background noise from audio"""
    if not voice_service:
        raise HTTPException(status_code=503, detail="Voice service not initialized")
    content = await audio.read()
    denoised = await voice_service.reduce_noise(content)
    return StreamingResponse(io.BytesIO(denoised), media_type="audio/wav")


@app.post("/api/voice/parse-command")
async def voice_parse_command(req: VoiceCommandRequest):
    """Parse voice input for recognized trading/portfolio/goal commands"""
    if not voice_service:
        raise HTTPException(status_code=503, detail="Voice service not initialized")
    result = voice_service.parse_voice_commands(req.text)
    return result


# ============================================================================
# Voice Command Security Endpoints
# ============================================================================

@app.post("/api/voice/execute-command")
async def execute_voice_command(
    request: Request,
    command_type: str,
    symbol: str,
    quantity: float,
    auth_data: dict = Depends(lambda: None)
):
    """
    Execute a voice command (with automatic rate limiting and confirmation).
    
    For high-value trades (>$10k), requires a subsequent /api/voice/confirm call.
    Returns pending_command_id if confirmation needed.
    
    Requires authentication header:
        Authorization: Bearer <access_token>
    """
    from middleware.auth import get_current_user_from_request
    from services.voice_security import (
        voice_command_tracker, VoiceCommandValidator, CommandType, VoiceCommandLogger
    )
    import uuid
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    try:
        # Check rate limit (5 commands per minute)
        is_allowed, error = voice_command_tracker.check_rate_limit(user_id)
        if not is_allowed:
            VoiceCommandLogger.log_command(user_id, command_type, "error", error=error)
            raise HTTPException(status_code=429, detail=error)
        
        # Validate command type
        try:
            cmd_type = CommandType[command_type.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Unknown command type: {command_type}")
        
        # Validate order (for trade commands)
        if cmd_type in [CommandType.BUY, CommandType.SELL]:
            is_valid, error = VoiceCommandValidator.validate_order(
                symbol=symbol,
                quantity=quantity,
                account_balance=50000  # TODO: fetch from user's portfolio
            )
            if not is_valid:
                VoiceCommandLogger.log_command(
                    user_id, command_type, "error",
                    details={"symbol": symbol, "quantity": quantity},
                    error=error
                )
                raise HTTPException(status_code=400, detail=error)
        
        # Create pending command
        command_id = str(uuid.uuid4())[:8]
        pending_cmd = voice_command_tracker.create_pending_command(
            user_id=user_id,
            command_id=command_id,
            command_type=cmd_type,
            amount=quantity,
            symbol=symbol,
            metadata={"request_time": datetime.now().isoformat()}
        )
        
        RequestLogger.log_request(
            structured_logger,
            "execute_voice_command",
            user_id=str(user_id),
            data={"command_id": command_id, "type": command_type, "symbol": symbol, "qty": quantity}
        )
        
        return {
            "command_id": command_id,
            "status": "pending" if pending_cmd["requires_confirmation"] else "confirmed",
            "requires_confirmation": pending_cmd["requires_confirmation"],
            "confirmation_token": pending_cmd.get("confirmation_token"),
            "message": "Confirmation required" if pending_cmd["requires_confirmation"] else "Command executed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice command execution error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute voice command")


@app.post("/api/voice/confirm")
async def confirm_voice_command(
    request: Request,
    command_id: str,
    confirmation_phrase: str,
    auth_data: dict = Depends(lambda: None)
):
    """
    Confirm a pending voice command with explicit confirmation phrase.
    
    Valid confirmation phrases:
        - "yes"
        - "confirm"
        - "execute"
        - "proceed"
        - "approved"
    
    Requires authentication header:
        Authorization: Bearer <access_token>
    """
    from middleware.auth import get_current_user_from_request
    from services.voice_security import voice_command_tracker, VoiceCommandLogger
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    try:
        # Confirm the command
        success, error = voice_command_tracker.confirm_command(
            user_id=user_id,
            command_id=command_id,
            confirmation_phrase=confirmation_phrase
        )
        
        if not success:
            VoiceCommandLogger.log_command(user_id, "confirm", "error", error=error)
            raise HTTPException(status_code=400, detail=error)
        
        # Get the confirmed command
        confirmed_cmd = voice_command_tracker.get_pending_command(user_id, command_id)
        
        RequestLogger.log_request(
            structured_logger,
            "confirm_voice_command",
            user_id=str(user_id),
            data={"command_id": command_id, "type": confirmed_cmd["command_type"]}
        )
        
        VoiceCommandLogger.log_command(user_id, confirmed_cmd["command_type"], "confirmed")
        
        return {
            "command_id": command_id,
            "status": "confirmed",
            "message": f"Command {confirmed_cmd['command_type']} confirmed and ready to execute"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice command confirmation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to confirm command")


@app.post("/api/voice/reject")
async def reject_voice_command(
    request: Request,
    command_id: str,
    auth_data: dict = Depends(lambda: None)
):
    """
    Reject a pending voice command.
    
    Requires authentication header:
        Authorization: Bearer <access_token>
    """
    from middleware.auth import get_current_user_from_request
    from services.voice_security import voice_command_tracker, VoiceCommandLogger
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    try:
        success, error = voice_command_tracker.reject_command(user_id, command_id)
        
        if not success:
            raise HTTPException(status_code=400, detail=error)
        
        RequestLogger.log_request(
            structured_logger,
            "reject_voice_command",
            user_id=str(user_id),
            data={"command_id": command_id}
        )
        
        VoiceCommandLogger.log_command(user_id, "command", "rejected")
        
        return {
            "command_id": command_id,
            "status": "rejected",
            "message": "Command rejected"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice command rejection error: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject command")


@app.get("/api/voice/pending-commands")
async def get_pending_commands(
    request: Request,
    auth_data: dict = Depends(lambda: None)
):
    """
    Get all pending voice commands for the user.
    
    Requires authentication header:
        Authorization: Bearer <access_token>
    """
    from middleware.auth import get_current_user_from_request
    from services.voice_security import voice_command_tracker
    
    auth_data = await get_current_user_from_request(request)
    user_id = auth_data['user_id']
    
    try:
        pending_cmds = voice_command_tracker.list_pending_commands(user_id)
        
        return {
            "pending_commands": pending_cmds,
            "count": len(pending_cmds)
        }
        
    except Exception as e:
        logger.error(f"Error fetching pending commands: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pending commands")


# =======================================
# WAR ROOM ENDPOINTS
# =======================================

@app.get("/api/war-room/messages")
async def get_war_room_messages(limit: int = Query(50, ge=1, le=200)):
    """Get recent War Room messages"""
    if not war_room:
        raise HTTPException(status_code=503, detail="War Room not initialized")
    return {"messages": war_room.get_recent_messages(limit)}


@app.get("/api/war-room/critical")
async def get_critical_messages(limit: int = Query(20, ge=1, le=100)):
    """Get critical/high-priority messages"""
    if not war_room:
        raise HTTPException(status_code=503, detail="War Room not initialized")
    return {"messages": war_room.get_critical_messages(limit)}


@app.get("/api/war-room/search")
async def search_war_room(q: str, limit: int = Query(50, ge=1, le=200)):
    """Search War Room messages"""
    if not war_room:
        raise HTTPException(status_code=503, detail="War Room not initialized")
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter required")
    return {"results": war_room.search_messages(q, limit)}


@app.get("/api/war-room/agent/{agent_name}")
async def get_agent_messages(agent_name: str, limit: int = Query(50, ge=1, le=200)):
    """Get messages from specific agent"""
    if not war_room:
        raise HTTPException(status_code=503, detail="War Room not initialized")
    return {"messages": war_room.get_messages_by_agent(agent_name, limit)}


@app.get("/api/war-room/stats")
async def get_war_room_stats():
    """Get War Room statistics"""
    if not war_room:
        raise HTTPException(status_code=503, detail="War Room not initialized")
    return {"stats": war_room.get_agent_stats()}


@app.get("/api/war-room/summary")
async def get_debate_summary():
    """Get current debate summary and decision points"""
    if not war_room:
        raise HTTPException(status_code=503, detail="War Room not initialized")
    return war_room.get_debate_summary()


@app.post("/api/war-room/thread/start")
async def start_debate_thread(body: Dict[str, str]):
    """Start a new debate thread"""
    if not war_room:
        raise HTTPException(status_code=503, detail="War Room not initialized")
    topic = body.get("topic", "General Debate")
    thread_id = war_room.start_debate_thread(topic)
    return {"thread_id": thread_id, "topic": topic}


@app.get("/api/war-room/thread/{thread_id}")
async def get_thread(thread_id: str):
    """Get messages from a specific thread"""
    if not war_room:
        raise HTTPException(status_code=503, detail="War Room not initialized")
    return {"messages": war_room.get_thread_messages(thread_id)}


@app.post("/api/war-room/thread/{thread_id}/close")
async def close_thread(thread_id: str):
    """Close a debate thread and get summary"""
    if not war_room:
        raise HTTPException(status_code=503, detail="War Room not initialized")
    summary = war_room.close_debate_thread(thread_id)
    return summary


@app.get("/api/war-room/threads")
async def get_active_threads():
    """Get all active debate threads"""
    if not war_room:
        raise HTTPException(status_code=503, detail="War Room not initialized")
    return {"threads": war_room.get_active_threads()}


@app.post("/api/war-room/export")
async def export_war_room():
    """Export War Room conversation to JSON"""
    if not war_room:
        raise HTTPException(status_code=503, detail="War Room not initialized")
    filename = war_room.export_conversation()
    return {"filename": filename, "message": f"Exported {len(war_room.messages)} messages"}


# =======================================
# RAG SYSTEM ENDPOINTS
# =======================================

class RAGQueryRequest(BaseModel):
    """RAG query request"""
    query: str
    limit: int = 5
    include_sources: bool = True


@app.post("/api/rag/search")
async def rag_search(req: RAGQueryRequest):
    """Semantic search across historical market data"""
    if not rag_engine or not chroma_service:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        # Classify intent
        intent = rag_engine.classify_intent(req.query)
        
        # Extract entities
        symbol = rag_engine.extract_symbol(req.query)
        date_str = rag_engine.extract_date(req.query)
        
        # Search based on intent
        results = []
        
        if intent.value == "price_movement" and symbol:
            # Search price movement collection
            query_results = chroma_service.collections["price_movements"].query(
                query_texts=[req.query],
                n_results=req.limit
            )
            results = query_results["documents"][0] if query_results["documents"] else []
            
        elif intent.value == "market_event":
            # Search market events
            query_results = chroma_service.collections["market_events"].query(
                query_texts=[req.query],
                n_results=req.limit
            )
            results = query_results["documents"][0] if query_results["documents"] else []
            
        elif intent.value == "company_info" and symbol:
            # Search company info
            query_results = chroma_service.collections["company_info"].query(
                query_texts=[f"{symbol} company information"],
                n_results=req.limit
            )
            results = query_results["documents"][0] if query_results["documents"] else []
            
        elif intent.value == "news_search":
            # Search news archive
            query_results = chroma_service.collections["news_archive"].query(
                query_texts=[req.query],
                n_results=req.limit
            )
            results = query_results["documents"][0] if query_results["documents"] else []
            
        else:
            # General search across all collections
            all_results = []
            for collection_name, collection in chroma_service.collections.items():
                try:
                    query_results = collection.query(
                        query_texts=[req.query],
                        n_results=max(1, req.limit // 4)
                    )
                    if query_results["documents"]:
                        all_results.extend(query_results["documents"][0])
                except Exception as e:
                    logger.warning(f"Error querying {collection_name}: {e}")
            results = all_results[:req.limit]
        
        return {
            "query": req.query,
            "intent": intent.value,
            "symbol": symbol,
            "date": date_str,
            "results": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"RAG search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"RAG search failed: {str(e)}")


@app.post("/api/rag/index/market-event")
async def add_market_event(body: Dict[str, Any]):
    """Add a market event to the RAG index"""
    if not chroma_service:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        success = chroma_service.add_market_event(
            event_id=body.get("event_id", f"event_{datetime.now().timestamp()}"),
            title=body.get("title"),
            description=body.get("description"),
            date=body.get("date", datetime.now().isoformat()),
            event_type=body.get("event_type", "general"),
            affected_symbols=body.get("affected_symbols", []),
            metadata=body.get("metadata")
        )
        return {"success": success, "message": "Market event indexed"}
    except Exception as e:
        logger.error(f"Error adding market event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add event: {str(e)}")


@app.post("/api/rag/index/news")
async def add_news_article(body: Dict[str, Any]):
    """Add a news article to the RAG index"""
    if not chroma_service:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        success = chroma_service.add_news_article(
            article_id=body.get("article_id", f"article_{datetime.now().timestamp()}"),
            title=body.get("title"),
            content=body.get("content"),
            published_date=body.get("published_date", datetime.now().isoformat()),
            source=body.get("source", "unknown"),
            symbols=body.get("symbols", []),
            sentiment=body.get("sentiment", "neutral"),
            metadata=body.get("metadata")
        )
        return {"success": success, "message": "News article indexed"}
    except Exception as e:
        logger.error(f"Error adding news article: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add article: {str(e)}")


@app.post("/api/rag/index/company")
async def add_company_info(body: Dict[str, Any]):
    """Add company information to the RAG index"""
    if not chroma_service:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        success = chroma_service.add_company_info(
            info_id=body.get("info_id", f"company_{datetime.now().timestamp()}"),
            symbol=body.get("symbol"),
            company_name=body.get("company_name"),
            description=body.get("description"),
            sector=body.get("sector"),
            industry=body.get("industry"),
            metadata=body.get("metadata")
        )
        return {"success": success, "message": "Company info indexed"}
    except Exception as e:
        logger.error(f"Error adding company info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add company: {str(e)}")


@app.post("/api/rag/index/price-movement")
async def add_price_movement(body: Dict[str, Any]):
    """Add price movement explanation to the RAG index"""
    if not chroma_service:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        success = chroma_service.add_price_movement(
            movement_id=body.get("movement_id", f"movement_{datetime.now().timestamp()}"),
            symbol=body.get("symbol"),
            date=body.get("date"),
            price_change_percent=body.get("price_change_percent"),
            explanation=body.get("explanation"),
            contributing_factors=body.get("contributing_factors", []),
            metadata=body.get("metadata")
        )
        return {"success": success, "message": "Price movement indexed"}
    except Exception as e:
        logger.error(f"Error adding price movement: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add movement: {str(e)}")



class ScenarioSimRequest(BaseModel):
    scenario: str
    speed_multiplier: int = 100
    risk_tolerance: str = 'moderate'


@app.get("/crash-simulator/scenarios")
async def get_available_scenarios():
    if not crash_engine:
        raise HTTPException(status_code=503, detail="Crash simulator not initialized")
    
    return {
        "scenarios": list(crash_engine.loader.scenarios.keys()),
        "details": crash_engine.loader.scenarios
    }


@app.post("/crash-simulator/load/{scenario_name}")
async def load_crash_scenario(scenario_name: str):
    if not crash_engine:
        raise HTTPException(status_code=503, detail="Crash simulator not initialized")
    
    try:
        scenario = crash_engine.load_scenario(scenario_name)
        
        await manager.broadcast({
            "type": "system",
            "from": "system",
            "to": "all",
            "content": f"📊 Loaded {scenario['data']['scenario']['name']} - {scenario['total_days']} trading days",
            "timestamp": datetime.now().isoformat(),
            "data": {"scenario": scenario_name}
        })
        
        return {
            "scenario": scenario_name,
            "total_days": scenario['total_days'],
            "symbols": scenario['symbols']
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/crash-simulator/start")
async def start_crash_simulation(req: ScenarioSimRequest):
    global crash_simulation_task
    
    if not crash_engine:
        raise HTTPException(status_code=503, detail="Crash simulator not initialized")
    
    if crash_simulation_task and not crash_simulation_task.done():
        raise HTTPException(status_code=400, detail="Simulation already running")
    
    async def simulation_callback(data):
        await manager.broadcast({
            "type": "market",
            "from": "market",
            "to": "all",
            "content": f"📊 Day {data['day']}: APEX ${data['apex_value']:,.0f} ({data['apex_return']:+.1f}%) vs Buy&Hold ${data['buy_hold_value']:,.0f} ({data['buy_hold_return']:+.1f}%)",
            "timestamp": datetime.now().isoformat(),
            "data": data
        })
        
        if data['day'] % 20 == 0:
            await manager.broadcast({
                "type": "strategy",
                "from": "strategy",
                "to": "all",
                "content": f"🧠 Rebalancing: High volatility detected. Shifting to defensive allocation.",
                "timestamp": datetime.now().isoformat()
            })
    
    async def run_sim():
        try:
            await manager.broadcast({
                "type": "system",
                "from": "system",
                "to": "all",
                "content": f"🚀 Starting crash simulation at {req.speed_multiplier}x speed",
                "timestamp": datetime.now().isoformat()
            })
            
            result = await crash_engine.run_simulation(
                speed_multiplier=req.speed_multiplier,
                message_callback=simulation_callback
            )
            
            await manager.broadcast({
                "type": "system",
                "from": "system",
                "to": "all",
                "content": f"✅ Simulation complete! APEX: {result['apex_return']:+.1f}% | Buy&Hold: {result['buy_hold_return']:+.1f}% | Outperformance: {result['outperformance']:+.1f}%",
                "timestamp": datetime.now().isoformat(),
                "data": result
            })
        except Exception as e:
            logger.error(f"Simulation error: {e}")
    
    crash_simulation_task = asyncio.create_task(run_sim())
    
    return {"message": "Simulation started", "status": "running"}


@app.post("/crash-simulator/stop")
async def stop_crash_simulation():
    if not crash_engine:
        raise HTTPException(status_code=503, detail="Crash simulator not initialized")
    
    crash_engine.stop_simulation()
    
    await manager.broadcast({
        "type": "system",
        "from": "system",
        "to": "all",
        "content": "⏹️ Crash simulation stopped",
        "timestamp": datetime.now().isoformat()
    })
    
    return {"message": "Simulation stopped", "status": "stopped"}


@app.get("/crash-simulator/comparison")
async def get_crash_comparison():
    if not crash_engine:
        raise HTTPException(status_code=503, detail="Crash simulator not initialized")
    
    if not crash_engine.current_scenario:
        raise HTTPException(status_code=400, detail="No scenario loaded")
    
    return crash_engine.get_comparison_data()


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
