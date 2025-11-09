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
import sys

router = APIRouter()
logger = logging.getLogger(__name__)

# Get orchestrator reference from parent module to avoid circular imports
def get_orchestrator():
    """Get orchestrator instance from parent routes module"""
    try:
        routes_module = sys.modules.get('app.api.routes')
        if routes_module and hasattr(routes_module, 'orchestrator'):
            return routes_module.orchestrator
        return None
    except:
        return None

def get_war_room():
    """Get war room instance from parent routes module"""
    try:
        routes_module = sys.modules.get('app.api.routes')
        if routes_module and hasattr(routes_module, 'war_room'):
            return routes_module.war_room
        return None
    except:
        return None

print("ORCHESTRATOR ROUTES MODULE LOADED")


@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify orchestrator routes are loaded"""
    return {"message": "Orchestrator routes are working!", "status": "ok"}


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
    orchestrator = get_orchestrator()
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    if orchestrator.is_running:
        return {"message": "Orchestrator already running", "status": "running"}

    # Update config if provided
    if request.config:
        orchestrator.config.update(request.config)

    # Start orchestrator in background
    orchestrator_task = asyncio.create_task(orchestrator.start())

    # For demo mode, simulate some agent activity
    if hasattr(orchestrator, 'network'):
        asyncio.create_task(simulate_demo_agent_activity())

    logger.info("▶️ Orchestrator started")

    return {
        "message": "Orchestrator started successfully",
        "status": "running",
        "config": orchestrator.config
    }


async def simulate_demo_agent_activity():
    """Simulate proper multi-agent deliberation flow as described in README"""
    await asyncio.sleep(2)

    # Phase 1: Initial Analysis (Agents working independently)
    initial_analysis = [
        {
            "type": "agent_message",
            "from": "market",
            "to": "all",
            "content": "🔍 MARKET ANALYSIS: VIX at 18.2 (-0.8% today). S&P 500 showing bullish momentum with tech sector leading. Fed rate decision next week could impact volatility. Sentiment analysis: 65% positive news flow.",
            "timestamp": datetime.now().isoformat()
        },
        {
            "type": "agent_message",
            "from": "strategy",
            "to": "all",
            "content": "🧠 STRATEGY PROPOSAL: Based on market conditions, recommend 65% equities (45% tech/20% diversified), 25% bonds, 10% cash. Expected return: 9.2% annually with Sharpe ratio of 1.8.",
            "timestamp": datetime.now().isoformat()
        },
        {
            "type": "agent_message",
            "from": "risk",
            "to": "all",
            "content": "⚠️ RISK ASSESSMENT: Portfolio volatility at 14.2% (acceptable range 10-18%). Monte Carlo simulation: 85% probability of positive returns over 1 year. Max drawdown stress test: -18.5% (within limits).",
            "timestamp": datetime.now().isoformat()
        }
    ]

    for message in initial_analysis:
        await asyncio.sleep(2)
        await manager.broadcast(message)

    # Phase 2: Deliberation - Agents discussing and challenging each other
    await asyncio.sleep(3)

    deliberation_rounds = [
        # Round 1: Strategy challenging Market's optimism
        {
            "type": "agent_message",
            "from": "strategy",
            "to": "market",
            "content": "🧠 STRATEGY → MARKET: Your VIX reading seems optimistic. Tech sector concentration at 45% could amplify volatility if rates rise. Should we consider defensive positioning?",
            "timestamp": datetime.now().isoformat()
        },
        {
            "type": "agent_message",
            "from": "market",
            "to": "strategy",
            "content": "🔍 MARKET → STRATEGY: Valid concern about rate sensitivity. However, current yield curve suggests Fed pause likely. Tech fundamentals remain strong - EPS growth projected at 15%. Risk-adjusted opportunity favors maintaining exposure.",
            "timestamp": datetime.now().isoformat()
        },

        # Risk Agent joining the discussion
        {
            "type": "agent_message",
            "from": "risk",
            "to": "strategy",
            "content": "⚠️ RISK → STRATEGY: Your Sharpe ratio of 1.8 looks good, but I calculated 14.2% volatility vs your 12% assumption. Can you verify your risk calculations? Tech sector beta of 1.3 increases portfolio sensitivity.",
            "timestamp": datetime.now().isoformat()
        },

        # Strategy responding to Risk concerns
        {
            "type": "agent_message",
            "from": "strategy",
            "to": "risk",
            "content": "🧠 STRATEGY → RISK: You're correct on volatility - updating to 14.2%. However, the higher returns from tech justify the increased risk. Alternative: 40% tech + 10% defensive sectors (utilities/healthcare) to maintain diversification while preserving growth potential.",
            "timestamp": datetime.now().isoformat()
        },

        # Market Agent providing additional context
        {
            "type": "agent_message",
            "from": "market",
            "to": "all",
            "content": "🔍 MARKET → ALL: Breaking news: Tech earnings reports this week show 78% beat estimates. This supports Strategy's optimistic outlook. However, Risk is right to flag concentration risk - monitoring closely.",
            "timestamp": datetime.now().isoformat()
        },

        # Consensus building
        {
            "type": "agent_message",
            "from": "risk",
            "to": "all",
            "content": "⚠️ RISK → ALL: Consensus check: Market conditions favorable (agreed), Strategy allocation reasonable with risk mitigation (agreed), Volatility within acceptable bounds (conditional). Ready for user input or finalization.",
            "timestamp": datetime.now().isoformat()
        }
    ]

    for message in deliberation_rounds:
        await asyncio.sleep(3)
        await manager.broadcast(message)

    # Final explanation to user
    await asyncio.sleep(2)
    await manager.broadcast({
        "type": "agent_message",
        "from": "explainer",
        "to": "user",
        "content": "💬 EXPLAINER → USER: The agents have completed their initial analysis and deliberation. We've reached consensus on a balanced portfolio strategy. You can now provide input, ask questions, or request finalization. What would you like to discuss?",
        "timestamp": datetime.now().isoformat()
    })


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
    orchestrator = get_orchestrator()
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

    # For demo, simulate agent responses to user input
    if input_data.message and orchestrator.is_running:
        asyncio.create_task(simulate_agent_response(input_data.message))

    logger.info(f"User input received: {input_data.action}")

    return {
        "message": "User input received",
        "action": input_data.action
    }


async def simulate_agent_response(user_message: str):
    """Simulate intelligent multi-agent deliberation in response to user input"""
    await asyncio.sleep(1)

    user_msg_lower = user_message.lower()

    # Agent-to-agent discussion triggered by user input
    discussion_flow = []

    if "volatility" in user_msg_lower or "risk" in user_msg_lower or "conservative" in user_msg_lower:
        # Risk-focused discussion
        discussion_flow = [
            {
                "type": "agent_message",
                "from": "risk",
                "to": "user",
                "content": f"⚠️ RISK → USER: Thank you for raising concerns about {user_message.split()[-1] if 'volatility' in user_msg_lower else 'risk'}. Let me consult with the other agents to reassess our position.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "risk",
                "to": "strategy",
                "content": "⚠️ RISK → STRATEGY: User is concerned about volatility/risk. Current allocation has 45% tech exposure with beta 1.3. Should we reduce concentration to address user concerns?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "strategy",
                "to": "risk",
                "content": "🧠 STRATEGY → RISK: Valid user concern. I can reduce tech from 45% to 35% and increase defensive sectors (utilities/healthcare) to 15%. This maintains growth potential while reducing volatility to ~11.8%. Market, what do you think about the timing?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "market",
                "to": "strategy",
                "content": "🔍 MARKET → STRATEGY: Current market momentum supports maintaining some tech exposure, but user risk preferences take priority. The adjustment makes sense - we can always increase exposure if conditions improve.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "explainer",
                "to": "user",
                "content": f"💬 EXPLAINER → USER: The agents have discussed your {user_message.split()[-1] if 'volatility' in user_msg_lower else 'risk'} concerns and agreed to adjust the portfolio. Tech allocation reduced from 45% to 35%, volatility estimate now 11.8%. This balances your risk preferences with growth objectives.",
                "timestamp": datetime.now().isoformat()
            }
        ]

    elif "tech" in user_msg_lower or "technology" in user_msg_lower:
        # Tech-focused discussion
        discussion_flow = [
            {
                "type": "agent_message",
                "from": "market",
                "to": "user",
                "content": "🔍 MARKET → USER: Great question about tech! Current momentum is strong with 78% earnings beats this quarter. Let me get Strategy's perspective on the allocation.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "strategy",
                "to": "market",
                "content": "🧠 STRATEGY → MARKET: Tech fundamentals remain compelling - 15% EPS growth projected. Current 45% allocation provides good diversification within sector. Risk, any concerns about concentration?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "risk",
                "to": "strategy",
                "content": "⚠️ RISK → STRATEGY: Tech beta of 1.3 increases portfolio sensitivity, but diversification across large-cap, mid-cap, and growth stocks mitigates single-company risk. Current allocation within acceptable bounds.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "market",
                "to": "all",
                "content": "🔍 MARKET → ALL: Breaking: NVIDIA earnings exceeded expectations by 12%. This validates our tech sector confidence. User can be reassured about both fundamentals and diversification.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "explainer",
                "to": "user",
                "content": "💬 EXPLAINER → USER: Tech sector analysis complete! The agents confirm strong fundamentals (15% EPS growth) with good diversification. Recent NVIDIA earnings beat supports our confidence. Current 45% allocation balances growth opportunity with risk management.",
                "timestamp": datetime.now().isoformat()
            }
        ]

    elif "bull" in user_msg_lower or "bear" in user_msg_lower or "market" in user_msg_lower:
        # Market outlook discussion
        discussion_flow = [
            {
                "type": "agent_message",
                "from": "market",
                "to": "all",
                "content": f"🔍 MARKET → ALL: User asking about market outlook. Current assessment: Bullish momentum with tech leading. VIX at healthy 18.2. Strategy and Risk, please validate.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "strategy",
                "to": "market",
                "content": "🧠 STRATEGY → MARKET: Market conditions support our bullish outlook. Portfolio positioned for growth while maintaining risk controls. Any sector rotations you recommend?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "risk",
                "to": "strategy",
                "content": "⚠️ RISK → STRATEGY: Bull market increases volatility risk. Current stop-losses at -15% for individual positions. Monte Carlo shows 78% probability of positive 1-year returns.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "market",
                "to": "risk",
                "content": "🔍 MARKET → RISK: Agree with caution. Economic indicators (employment, GDP growth) remain positive. Fed likely to maintain accommodative stance. Risk mitigation measures are appropriate.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "explainer",
                "to": "user",
                "content": f"💬 EXPLAINER → USER: Market outlook discussion complete! Agents agree on bullish momentum but emphasize risk management. Economic fundamentals remain strong, supporting our current strategy with appropriate safeguards in place.",
                "timestamp": datetime.now().isoformat()
            }
        ]

    else:
        # General discussion about user input
        discussion_flow = [
            {
                "type": "agent_message",
                "from": "explainer",
                "to": "all",
                "content": f"💬 EXPLAINER → ALL: User input received: '{user_message}'. Agents, please analyze and discuss how this impacts our current strategy.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "strategy",
                "to": "market",
                "content": f"🧠 STRATEGY → MARKET: User feedback may require strategy adjustment. Does current market data support or contradict their perspective?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "market",
                "to": "strategy",
                "content": f"🔍 MARKET → STRATEGY: Market data shows mixed signals. User perspective is valuable - we should incorporate their insights into our analysis.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "risk",
                "to": "all",
                "content": f"⚠️ RISK → ALL: User input acknowledged. Will monitor for any risk implications from this feedback. Current risk metrics remain within acceptable ranges.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "agent_message",
                "from": "explainer",
                "to": "user",
                "content": f"💬 EXPLAINER → USER: Thank you for your input! The agents have discussed your feedback and incorporated it into their analysis. Your perspective helps ensure our strategy remains balanced and well-informed.",
                "timestamp": datetime.now().isoformat()
            }
        ]

    # Send discussion flow with realistic timing
    for i, response in enumerate(discussion_flow):
        # Vary timing to feel more natural (1-3 seconds between responses)
        delay = 1.5 if i == 0 else 2.0 + (i * 0.5)  # Increasing delay for more natural conversation
        await asyncio.sleep(delay)
        await manager.broadcast(response)


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get orchestrator status"""
    orchestrator = get_orchestrator()
    logger.info(f"Orchestrator status requested. Orchestrator object: {orchestrator}")
    if not orchestrator:
        logger.error("Orchestrator is None!")
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        status = orchestrator.get_status()
        logger.info(f"Orchestrator status: {status}")
        return StatusResponse(
            state=status["state"],
            is_paused=status["is_paused"],
            is_running=status["is_running"],
            error_count=status["error_count"],
            decision_count=status["decision_count"]
        )
    except Exception as e:
        logger.error(f"Error getting orchestrator status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.get("/messages")
async def get_messages(limit: int = 50):
    """Get recent agent messages"""
    orchestrator = get_orchestrator()
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    messages = await orchestrator.network.get_message_history(limit=limit)

    # Convert messages to frontend format
    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            "id": msg.get("timestamp", "") or str(hash(str(msg))),
            "type": msg.get("type", "agent_message"),
            "from": msg.get("from", "system"),
            "to": msg.get("to", "all"),
            "content": msg.get("message", ""),
            "timestamp": msg.get("timestamp", ""),
            "data": msg.get("data", {})
        })

    return {
        "count": len(formatted_messages),
        "messages": formatted_messages
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
