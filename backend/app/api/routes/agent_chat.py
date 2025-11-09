"""
Interactive Agent Chat API for War Room
Handles collaborative agent conversations with user interaction and confidence levels
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio
import random
import uuid

router = APIRouter()

# Simple in-memory message storage
message_history: List[Dict[str, Any]] = []
is_session_active = False
last_message_id = 0

# Track pending user questions
pending_questions: Dict[str, Dict[str, Any]] = {}  # question_id -> question_data

# Track sequential agent discussion state
discussion_state: Dict[str, Any] = {
    "current_agent_index": 0,
    "agents": ["explainer", "market", "strategy", "risk"],
    "user_message": "",
    "completed": True,
    "active": False,
    "mode": "introduction",  # "introduction" or "response"
    "introduction_complete": False  # Whether all agents have introduced themselves
}

def reset_discussion_state():
    """Reset the discussion state to initial values"""
    global discussion_state
    discussion_state = {
        "current_agent_index": 0,
        "agents": ["explainer", "market", "strategy", "risk"],
        "user_message": "",
        "completed": True,
        "active": False,
        "mode": "introduction",
        "introduction_complete": False
    }

# Agent definitions with enhanced capabilities
AGENTS = {
    "market": {
        "name": "Market Agent",
        "emoji": "🔍",
        "role": "Market Intelligence",
        "personality": "Analytical and data-driven",
        "expertise": ["market_trends", "economic_indicators", "sector_analysis"]
    },
    "strategy": {
        "name": "Strategy Agent",
        "emoji": "🧠",
        "role": "Portfolio Optimization",
        "personality": "Strategic and risk-aware",
        "expertise": ["asset_allocation", "portfolio_construction", "tactical_adjustments"]
    },
    "risk": {
        "name": "Risk Agent",
        "emoji": "⚠️",
        "role": "Risk Management",
        "personality": "Conservative and vigilant",
        "expertise": ["volatility_assessment", "stress_testing", "risk_limits"]
    },
    "explainer": {
        "name": "Explainer Agent",
        "emoji": "💬",
        "role": "Education & Translation",
        "personality": "Patient and clear",
        "expertise": ["user_education", "clarification", "consensus_building"]
    }
}

class ChatMessage(BaseModel):
    """User message model"""
    content: str
    timestamp: str = None

class AgentQuestion(BaseModel):
    """Model for agent questions to user"""
    question_id: str
    agent_id: str
    question_type: str  # "confirmation", "opinion", "clarification", "decision"
    question: str
    options: Optional[List[str]] = None
    context: Optional[str] = None
    urgency: str = "normal"  # "low", "normal", "high"

class AgentResponse(BaseModel):
    """Model for agent responses with confidence"""
    agent_id: str
    content: str
    confidence: float  # 0.0 to 1.0
    reasoning: Optional[str] = None
    requires_user_input: bool = False
    question: Optional[AgentQuestion] = None

# WebSocket connection manager
class ChatConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            print(f"Chat WebSocket connected. Total: {len(self.active_connections)}")
        except Exception as e:
            print(f"Error accepting WebSocket connection: {e}")
            raise

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"Chat WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to WebSocket: {e}")
                # Remove broken connection
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")

manager = ChatConnectionManager()

def generate_agent_response(user_message: str, agent_id: str, context: Dict[str, Any] = None) -> AgentResponse:
    """Generate an intelligent agent response with confidence levels and potential questions"""
    user_msg_lower = user_message.lower()
    agent = AGENTS[agent_id]
    context = context or {}

    # Calculate confidence based on agent expertise and message relevance
    base_confidence = 0.8  # Default high confidence
    expertise_match = any(expert in user_msg_lower for expert in agent["expertise"])
    if expertise_match:
        base_confidence = 0.95  # Very confident in area of expertise
    elif any(word in user_msg_lower for word in ["uncertain", "maybe", "perhaps"]):
        base_confidence = 0.6  # Lower confidence for ambiguous queries

    # Check if we need to force a question for sequential discussion
    force_question = context.get("force_question", False)

    # Context-aware responses with confidence levels
    if any(word in user_msg_lower for word in ["volatility", "risk", "vol"]):
        responses = {
            "market": {
                "content": "Market volatility is currently elevated at 18.2 VIX. We're seeing increased options activity suggesting investor caution. This is normal post-Fed announcements.",
                "confidence": 0.92,
                "reasoning": "Based on real-time VIX data and options flow analysis"
            },
            "strategy": {
                "content": "High volatility creates opportunities for rebalancing. I recommend maintaining our current asset allocation but increasing cash reserves to 15% for tactical opportunities.",
                "confidence": 0.88,
                "reasoning": "Historical data shows volatility spikes often precede 3-6 month opportunities",
                "requires_user_input": True,
                "question": AgentQuestion(
                    question_id=str(uuid.uuid4()),
                    agent_id="strategy",
                    question_type="confirmation",
                    question="Would you like me to implement this cash reserve increase now, or would you prefer to maintain the current allocation?",
                    options=["Implement 15% cash reserve", "Keep current allocation", "Custom cash level"],
                    context="Volatility-driven rebalancing opportunity"
                )
            },
            "risk": {
                "content": "Volatility assessment: Current levels are within our risk tolerance (target: 12-20 VIX). No immediate portfolio adjustments needed, but monitoring closely.",
                "confidence": 0.95,
                "reasoning": "Risk parameters calibrated to handle VIX up to 25 without breaching limits"
            },
            "explainer": {
                "content": "Volatility measures how much stock prices fluctuate. Higher volatility means more uncertainty. Our agents are designed to handle this by maintaining diversified positions.",
                "confidence": 0.9,
                "reasoning": "Educational explanation based on standard financial concepts",
                "requires_user_input": True,
                "question": AgentQuestion(
                    question_id=str(uuid.uuid4()),
                    agent_id="explainer",
                    question_type="opinion",
                    question="On a scale of 1-10, how comfortable are you with market volatility right now?",
                    options=["1-3: Very uncomfortable", "4-6: Somewhat comfortable", "7-10: Very comfortable"],
                    context="Understanding risk tolerance"
                )
            }
        }

    elif any(word in user_msg_lower for word in ["bull", "bear", "market", "outlook"]):
        responses = {
            "market": {
                "content": "Market sentiment analysis shows 65% positive news flow. Tech sector leading with earnings beats. Economic indicators (employment, GDP) remain strong.",
                "confidence": 0.87,
                "reasoning": "Sentiment analysis of 500+ news sources and economic data"
            },
            "strategy": {
                "content": "Market outlook supports our growth-oriented strategy. We're positioned for both bull and bear scenarios with appropriate hedges in place.",
                "confidence": 0.82,
                "reasoning": "Portfolio stress-tested against multiple market scenarios",
                "requires_user_input": True,
                "question": AgentQuestion(
                    question_id=str(uuid.uuid4()),
                    agent_id="strategy",
                    question_type="decision",
                    question="Given the current market conditions, should we increase our equity exposure or maintain defensive positioning?",
                    options=["Increase equity exposure", "Maintain defensive position", "Reduce risk further"],
                    context="Market outlook assessment"
                )
            },
            "risk": {
                "content": "Market risk assessment: Current conditions favor risk-on positioning. Our stop-losses are set at -15% individual positions, -10% portfolio level.",
                "confidence": 0.91,
                "reasoning": "Risk metrics calculated using Value-at-Risk and stress testing"
            },
            "explainer": {
                "content": "Market direction can be 'bullish' (rising) or 'bearish' (falling). Our agents analyze multiple indicators to determine the most likely direction and adjust accordingly.",
                "confidence": 0.88,
                "reasoning": "Educational content aligned with agent analysis"
            }
        }

    elif any(word in user_msg_lower for word in ["tech", "technology", "ai", "software"]):
        responses = {
            "market": {
                "content": "Technology sector showing strong momentum with 78% earnings beat rate. AI and cloud computing driving growth. NVIDIA up 12% on latest quarter.",
                "confidence": 0.93,
                "reasoning": "Real-time earnings data and sector momentum analysis"
            },
            "strategy": {
                "content": "Tech allocation currently at 45% of portfolio, justified by strong fundamentals and growth potential. EPS growth projected at 15% annually.",
                "confidence": 0.85,
                "reasoning": "Fundamental analysis and growth projections validated",
                "requires_user_input": True,
                "question": AgentQuestion(
                    question_id=str(uuid.uuid4()),
                    agent_id="strategy",
                    question_type="opinion",
                    question="Do you have a preference for specific technology sub-sectors (AI, Cloud, Semiconductors, etc.)?",
                    options=["AI & Machine Learning", "Cloud Computing", "Semiconductors", "Broad Tech exposure", "Reduce tech exposure"],
                    context="Technology sector preferences"
                )
            },
            "risk": {
                "content": "Tech concentration risk monitored closely. Diversified across large-cap, mid-cap, and growth stocks. Beta of 1.3 means higher volatility than market.",
                "confidence": 0.89,
                "reasoning": "Risk metrics calculated using correlation analysis and beta calculations"
            },
            "explainer": {
                "content": "Technology stocks often lead market performance due to innovation and growth. We balance this with diversification to manage risk while capturing upside potential.",
                "confidence": 0.86,
                "reasoning": "Educational explanation of technology investing principles"
            }
        }

    else:
        # General responses with varying confidence
        responses = {
            "market": {
                "content": f"Market analysis complete. Current conditions are favorable for our strategy. '{user_message}' noted and incorporated into ongoing assessment.",
                "confidence": 0.75,
                "reasoning": "General market monitoring and trend analysis"
            },
            "strategy": {
                "content": f"Strategic consideration: '{user_message}'. This aligns with our current portfolio optimization approach. No major adjustments needed at this time.",
                "confidence": 0.78,
                "reasoning": "Strategic framework evaluation and portfolio fit assessment"
            },
            "risk": {
                "content": f"Risk assessment: '{user_message}' acknowledged. Current risk metrics remain within acceptable parameters. Continuous monitoring active.",
                "confidence": 0.82,
                "reasoning": "Risk parameter monitoring and compliance checking"
            },
            "explainer": {
                "content": f"Thank you for your input about '{user_message}'. The agents have processed this information and are working collaboratively to provide the best investment guidance.",
                "confidence": 0.88,
                "reasoning": "Educational synthesis and agent coordination",
                "requires_user_input": True,
                "question": AgentQuestion(
                    question_id=str(uuid.uuid4()),
                    agent_id="explainer",
                    question_type="clarification",
                    question="Could you provide more details about your investment goals or concerns regarding this topic?",
                    context="Seeking better understanding of user needs"
                )
            }
        }

    response_data = responses.get(agent_id, {
        "content": f"{agent['name']}: Message received and processed.",
        "confidence": 0.7,
        "reasoning": "General response processing"
    })

    # If forcing a question, ensure we have one
    if force_question and not response_data.get("question"):
        # Create a forced question based on agent type
        if agent_id == "market":
            forced_question = AgentQuestion(
                question_id=str(uuid.uuid4()),
                agent_id="market",
                question_type="opinion",
                question="Based on current market conditions, do you want me to monitor any specific sectors or assets more closely?",
                options=["Technology stocks", "Bonds/Fixed Income", "Commodities", "Cryptocurrency", "No specific preferences"],
                context="Market monitoring preferences"
            )
        elif agent_id == "strategy":
            forced_question = AgentQuestion(
                question_id=str(uuid.uuid4()),
                agent_id="strategy",
                question_type="decision",
                question="Regarding your portfolio strategy, which risk level are you most comfortable with?",
                options=["Conservative (lower risk)", "Moderate (balanced)", "Aggressive (higher risk)", "Current strategy is fine"],
                context="Risk tolerance assessment"
            )
        elif agent_id == "risk":
            forced_question = AgentQuestion(
                question_id=str(uuid.uuid4()),
                agent_id="risk",
                question_type="confirmation",
                question="To ensure proper risk management, should I implement additional safeguards for market downturns?",
                options=["Yes, add protections", "No, current measures are sufficient", "Modify existing safeguards"],
                context="Risk protection measures"
            )
        elif agent_id == "explainer":
            forced_question = AgentQuestion(
                question_id=str(uuid.uuid4()),
                agent_id="explainer",
                question_type="clarification",
                question="To provide the most relevant information, what aspect of our discussion would you like me to explain further?",
                options=["Market analysis", "Strategy implications", "Risk factors", "Next steps", "Everything is clear"],
                context="Clarification needs"
            )

        response_data["requires_user_input"] = True
        response_data["question"] = forced_question

    return AgentResponse(
        agent_id=agent_id,
        content=response_data["content"],
        confidence=response_data["confidence"],
        reasoning=response_data.get("reasoning"),
        requires_user_input=response_data.get("requires_user_input", False),
        question=response_data.get("question")
    )

async def simulate_agent_discussion(user_message: str, context: Dict[str, Any] = None):
    """Handle agent discussions in introduction or response mode"""
    context = context or {}

    print(f"🔄 simulate_agent_discussion called with: message='{user_message}', context={context}, mode={discussion_state['mode']}")

    # Check if this is a response to a pending question
    if "question_response" in context:
        print(f"📝 Handling question response in {discussion_state['mode']} mode")
        await handle_question_response(context["question_response"])

        if discussion_state["mode"] == "introduction":
            # Continue with next introduction
            await continue_agent_discussion(user_message, context)
        elif discussion_state["mode"] == "response":
            # In response mode, user responses continue the collaborative discussion
            await continue_response_discussion(user_message, context)
        return

    # Handle user messages based on current mode
    if user_message and user_message.strip() and user_message.lower() != "continue":
        if discussion_state["mode"] == "introduction":
            if not discussion_state["introduction_complete"]:
                # Start or continue introductions
                if not discussion_state["active"]:
                    print(f"🚀 Starting introduction sequence")
                    await start_introduction_sequence()
                else:
                    print(f"⚠️ Introduction already active, ignoring message")
            else:
                # Introduction complete, switch to response mode
                print(f"🔄 Switching to response mode for user message: '{user_message}'")
                discussion_state["mode"] = "response"
                await handle_user_request(user_message)
        elif discussion_state["mode"] == "response":
            # Handle user request collaboratively
            print(f"💬 Handling user request in response mode: '{user_message}'")
            await handle_user_request(user_message)
    else:
        print(f"⏭️ Ignoring empty or continuation message: '{user_message}'")

async def start_introduction_sequence():
    """Start the introduction sequence where each agent introduces themselves"""
    global discussion_state

    # Initialize for introduction mode
    discussion_state.update({
        "current_agent_index": 0,
        "active": True,
        "completed": False,
        "introduction_complete": False
    })

    print(f"🎬 Started introduction sequence")
    # Start with first agent introduction
    await send_next_introduction()

async def send_next_introduction():
    """Send next agent introduction and FREEZE until user responds"""
    print(f"🤖 send_next_introduction called - index: {discussion_state['current_agent_index']}, active: {discussion_state['active']}")

    if not discussion_state["active"]:
        print("🚫 Introduction not active, stopping")
        return

    if discussion_state["current_agent_index"] >= len(discussion_state["agents"]):
        # All introductions complete
        print("✅ All introductions complete!")
        discussion_state["introduction_complete"] = True
        discussion_state["active"] = False
        return

    agent_id = discussion_state["agents"][discussion_state["current_agent_index"]]
    print(f"🎭 Agent {discussion_state['current_agent_index'] + 1}/{len(discussion_state['agents'])} introducing: {agent_id}")

    # Generate introduction message with question
    intro_response = generate_agent_introduction(agent_id)

    await add_agent_response(intro_response, "user")

    # FREEZE: Deactivate until user responds
    discussion_state["active"] = False
    print(f"🛑 INTRODUCTION FREEZE: Agent {agent_id} introduced. WAITING FOR USER RESPONSE.")

    # Move to next agent
    discussion_state["current_agent_index"] += 1


async def continue_agent_discussion(user_message: str, context: Dict[str, Any]):
    """Continue introduction sequence after user responds"""
    print(f"🔄 continue_agent_discussion called - user responded to introduction, REACTIVATING")

    # REACTIVATE for next introduction
    discussion_state["active"] = True
    print(f"▶️ Introduction REACTIVATED. Current agent index: {discussion_state['current_agent_index']}")

    # Send next introduction
    await send_next_introduction()

def generate_agent_introduction(agent_id: str) -> AgentResponse:
    """Generate an agent's introduction message with a question"""
    agent = AGENTS[agent_id]

    # Introduction messages for each agent
    introductions = {
        "explainer": {
            "content": f"Hello! I'm the {agent['name']} ({agent['emoji']}). I help clarify complex financial concepts and coordinate between the other agents. My role is {agent['role'].lower()}.",
            "question": AgentQuestion(
                question_id=str(uuid.uuid4()),
                agent_id="explainer",
                question_type="confirmation",
                question="Are you familiar with financial markets, or would you like me to explain basic concepts?",
                options=["I'm familiar - continue", "Please explain basics", "I need help with specific terms"],
                context="Assessing user knowledge level"
            )
        },
        "market": {
            "content": f"Hi there! I'm the {agent['name']} ({agent['emoji']}). I monitor real-time market data, trends, and news. Currently tracking VIX at 18.2 with moderate volatility.",
            "question": AgentQuestion(
                question_id=str(uuid.uuid4()),
                agent_id="market",
                question_type="opinion",
                question="What market aspects are you most interested in learning about?",
                options=["Stock market trends", "Economic indicators", "Sector performance", "Global markets"],
                context="Understanding user interests"
            )
        },
        "strategy": {
            "content": f"Greetings! I'm the {agent['name']} ({agent['emoji']}). I optimize portfolios and create investment strategies. Current allocation: 65% equities, 25% bonds, 10% cash.",
            "question": AgentQuestion(
                question_id=str(uuid.uuid4()),
                agent_id="strategy",
                question_type="decision",
                question="What is your primary investment goal?",
                options=["Capital preservation", "Income generation", "Growth", "Balanced approach"],
                context="Understanding investment objectives"
            )
        },
        "risk": {
            "content": f"Hello! I'm the {agent['name']} ({agent['emoji']}). I manage risk and ensure portfolio safety. Risk limits are within acceptable ranges with 14.2% volatility.",
            "question": AgentQuestion(
                question_id=str(uuid.uuid4()),
                agent_id="risk",
                question_type="confirmation",
                question="How comfortable are you with investment risk?",
                options=["Very conservative", "Moderately conservative", "Moderate risk", "Higher risk tolerance"],
                context="Risk tolerance assessment"
            )
        }
    }

    intro = introductions[agent_id]

    return AgentResponse(
        agent_id=agent_id,
        content=intro["content"],
        confidence=0.95,
        reasoning="Agent self-introduction",
        requires_user_input=True,
        question=intro["question"]
    )

async def handle_user_request(user_message: str):
    """Handle user requests collaboratively in response mode"""
    print(f"🎯 Handling user request: '{user_message}'")

    # Reset for new collaborative response
    discussion_state.update({
        "active": True,
        "user_message": user_message,
        "current_agent_index": 0
    })

    # Start collaborative response from all agents
    await send_collaborative_response()

async def send_collaborative_response():
    """Send collaborative responses from all agents to user request"""
    user_message = discussion_state["user_message"]

    # Send responses from all agents
    for i, agent_id in enumerate(discussion_state["agents"]):
        print(f"🤝 Agent {i+1}/{len(discussion_state['agents'])} responding collaboratively: {agent_id}")

        # Generate response to user message
        agent_response = generate_agent_response(user_message, agent_id, {"collaborative": True})
        await add_agent_response(agent_response, "user")

        # Brief pause between responses
        if i < len(discussion_state["agents"]) - 1:
            await asyncio.sleep(1)

    # Generate final consensus
    await generate_final_consensus(user_message)

async def continue_response_discussion(user_message: str, context: Dict[str, Any]):
    """Continue response discussion after user answers agent questions"""
    print(f"🔄 Continuing response discussion after user answer")
    # For now, just complete the discussion
    discussion_state["active"] = False
    discussion_state["completed"] = True

async def generate_final_consensus(user_message: str):
    """Generate final consensus after all agents have responded"""
    await asyncio.sleep(2)

    consensus_response = AgentResponse(
        agent_id="explainer",
        content="""🤝 **AGENT CONSENSUS REACHED**

All agents have provided their analysis and recommendations. Based on our discussion:

• Market conditions show moderate volatility with upward momentum
• Strategy recommendations focus on balanced risk-adjusted positioning  
• Risk management protocols are actively monitoring and protecting capital

The agents are ready to implement any decisions or provide further analysis as needed.""",
        confidence=0.95,
        reasoning="Synthesized input from all agent perspectives",
        requires_user_input=True,
        question=AgentQuestion(
            question_id=str(uuid.uuid4()),
            agent_id="explainer",
            question_type="decision",
            question="Would you like the agents to proceed with these recommendations, or do you have additional questions?",
            options=["Proceed with recommendations", "I have questions", "Modify approach", "Get more details"],
            context="Final consensus decision"
        )
    )

    await add_agent_response(consensus_response, "user")

    # Mark discussion as completed and inactive so new user messages can start new discussions
    discussion_state["completed"] = True
    discussion_state["active"] = False
    print(f"✅ Discussion completed and deactivated. Ready for new user messages.")

async def add_agent_response(response: AgentResponse, to: str):
    """Add agent response to message history (HTTP polling approach)"""
    global last_message_id

    message = {
        "id": last_message_id,
        "type": "agent_message",
        "from": response.agent_id,
        "to": to,
        "content": response.content,
        "confidence": response.confidence,
        "reasoning": response.reasoning,
        "timestamp": datetime.now().isoformat(),
        "message_type": "agent_message"
    }

    # Add question if present
    if response.question:
        message["question"] = response.question.dict()
        # Track pending questions
        pending_questions[response.question.question_id] = {
            "question": response.question.dict(),
            "timestamp": datetime.now().isoformat()
        }

    last_message_id += 1
    message_history.append(message)

async def handle_question_response(question_response: Dict[str, Any]):
    """Handle user response to agent questions"""
    question_id = question_response.get("question_id")
    user_answer = question_response.get("answer")

    if question_id in pending_questions:
        question_data = pending_questions[question_id]
        agent_id = question_data["question"]["agent_id"]

        # Generate follow-up response based on user answer
        followup_content = f"Thank you for your response. I've noted your preference for: {user_answer}"

        # Agent-specific follow-up logic
        if agent_id == "strategy":
            if "cash reserve" in question_data["question"]["context"]:
                followup_content += ". I'll implement this change to optimize our risk-adjusted returns."
            elif "equity exposure" in question_data["question"]["context"]:
                followup_content += ". This aligns with our current market assessment."
            elif "technology sub-sectors" in question_data["question"]["context"]:
                followup_content += ". I'll adjust our technology allocation accordingly."

        elif agent_id == "explainer":
            if "risk tolerance" in question_data["question"]["context"]:
                followup_content += ". This helps me better explain concepts at your comfort level."
            else:
                followup_content += ". This additional context improves our collaboration."

        # Create agent response
        agent_response = AgentResponse(
            agent_id=agent_id,
            content=followup_content,
            confidence=0.95,
            reasoning="Processing user response and updating strategy"
        )

        await add_agent_response(agent_response, "user")

        # Remove question from pending list
        del pending_questions[question_id]


# HTTP polling system - no WebSocket complexity
# Messages are stored in memory and polled via HTTP endpoints

@router.get("/status")
async def get_chat_status():
    """Get chat session status"""
    return {
        "is_active": is_session_active,
        "connected_clients": len(manager.active_connections),
        "message_count": len(message_history)
    }

@router.get("/messages")
async def get_messages(limit: int = 50):
    """Get recent chat messages"""
    return {
        "count": len(message_history[-limit:]),
        "messages": message_history[-limit:]
    }

@router.post("/reset")
async def reset_chat():
    """Reset the chat session"""
    global message_history, is_session_active, last_message_id, pending_questions, discussion_state
    message_history = []
    is_session_active = False
    last_message_id = 0
    pending_questions = {}
    discussion_state = {
        "current_agent_index": 0,
        "agents": ["explainer", "market", "strategy", "risk"],
        "user_message": "",
        "completed": True,
        "active": False
    }

    return {"message": "Chat session reset", "status": "success"}

@router.post("/send")
async def send_message(message: ChatMessage):
    """Send a message to the chat (HTTP polling approach)"""
    global last_message_id

    if not message.content or not message.content.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    # Check if discussion is already active - don't allow new messages until current discussion is complete
    if discussion_state["active"] and not discussion_state["completed"]:
        raise HTTPException(
            status_code=409,
            detail="Please respond to the current agent question before sending a new message"
        )

    user_msg = {
        "id": last_message_id,
        "type": "user_input",
        "from": "user",
        "to": "all",
        "content": message.content.strip(),
        "timestamp": datetime.now().isoformat(),
        "message_type": "user_input",
        "importance": "high"
    }

    last_message_id += 1
    message_history.append(user_msg)

    print(f"📨 User sent message: '{message.content.strip()}', starting agent discussion")

    # Start agent discussion asynchronously
    asyncio.create_task(simulate_agent_discussion(message.content.strip()))

    return {
        "status": "sent",
        "message_id": user_msg["id"],
        "timestamp": user_msg["timestamp"]
    }

@router.post("/respond/{question_id}")
async def respond_to_question(question_id: str, answer: str):
    """Respond to a specific agent question"""
    global last_message_id

    if question_id not in pending_questions:
        raise HTTPException(status_code=404, detail="Question not found")

    # Remove from pending questions
    question_data = pending_questions.pop(question_id)

    # Add response to message history
    response_msg = {
        "id": last_message_id,
        "type": "user_response",
        "from": "user",
        "to": "all",
        "content": f"Response to question: {answer}",
        "question_id": question_id,
        "timestamp": datetime.now().isoformat(),
        "message_type": "user_response"
    }

    last_message_id += 1
    message_history.append(response_msg)

    # Continue the sequential discussion with the next agent
    context = {"question_response": {
        "question_id": question_id,
        "answer": answer,
        "timestamp": datetime.now().isoformat()
    }}
    asyncio.create_task(simulate_agent_discussion("continue", context))

    return {"status": "responded", "question_id": question_id}

@router.get("/poll")
async def poll_messages(since_id: int = -1):
    """Poll for new messages since the given ID"""
    new_messages = []
    for msg in message_history:
        if msg["id"] > since_id:
            new_messages.append(msg)

    return {
        "messages": new_messages,
        "has_new": len(new_messages) > 0,
        "latest_id": message_history[-1]["id"] if message_history else -1
    }

@router.post("/start")
async def start_session():
    """Start a new chat session"""
    global is_session_active, last_message_id

    if is_session_active:
        return {"status": "already_active", "message": "Session already active"}

    is_session_active = True

    # Add initial agent introductions
    intro_messages = [
        {
            "id": last_message_id,
            "type": "agent_message",
            "from": "explainer",
            "to": "user",
            "content": "Welcome to APEX Agent War Room! I'm the Explainer Agent. I'll help clarify what the other agents are discussing. The Market, Strategy, and Risk agents are now active and ready to assist with your investment questions.",
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat(),
            "message_type": "agent_message"
        },
        {
            "id": last_message_id + 1,
            "type": "agent_message",
            "from": "market",
            "to": "all",
            "content": "Market Agent online. Scanning financial markets and news feeds. Current VIX: 18.2, S&P trending upward.",
            "confidence": 0.92,
            "timestamp": datetime.now().isoformat(),
            "message_type": "agent_message"
        },
        {
            "id": last_message_id + 2,
            "type": "agent_message",
            "from": "strategy",
            "to": "all",
            "content": "Strategy Agent engaged. Portfolio optimization active. Current allocation: 65% equities, 25% bonds, 10% cash.",
            "confidence": 0.88,
            "timestamp": datetime.now().isoformat(),
            "message_type": "agent_message"
        },
        {
            "id": last_message_id + 3,
            "type": "agent_message",
            "from": "risk",
            "to": "all",
            "content": "Risk Agent monitoring. Portfolio volatility: 14.2%. Risk limits within acceptable ranges.",
            "confidence": 0.91,
            "timestamp": datetime.now().isoformat(),
            "message_type": "agent_message"
        }
    ]

    for msg in intro_messages:
        message_history.append(msg)
        last_message_id += 1

    return {
        "status": "started",
        "message": "Chat session started",
        "initial_messages": intro_messages
    }
