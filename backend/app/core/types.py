"""
APEX Core Types and Enumerations
Unified type definitions for the entire system.
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


class AgentType(str, Enum):
    """Types of agents in the system."""
    MARKET = "market"
    STRATEGY = "strategy"
    RISK = "risk"
    EXECUTOR = "executor"
    EXPLAINER = "explainer"
    USER = "user"


class OrchestratorState(str, Enum):
    """States of the orchestrator."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    ANALYSIS = "analysis"
    DELIBERATION = "deliberation"
    EXECUTION = "execution"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


class MessageType(str, Enum):
    """Types of messages in the agent network."""
    AGENT_COMMUNICATION = "agent_communication"
    USER_INPUT = "user_input"
    SYSTEM_EVENT = "system_event"
    TRADE_EXECUTED = "trade_executed"
    ALERT = "alert"
    DEBUG = "debug"


class MessageImportance(str, Enum):
    """Importance levels for messages."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MarketCondition(str, Enum):
    """Market condition classifications."""
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    EXTREME_VOLATILITY = "extreme_volatility"
    CRISIS = "crisis"


class TradeAction(str, Enum):
    """Trade actions."""
    BUY = "buy"
    SELL = "sell"
    REBALANCE = "rebalance"


@dataclass
class AgentMessage:
    """Standard agent communication message."""
    id: str
    from_agent: str
    to_agent: Optional[str]
    message: str
    timestamp: datetime
    message_type: MessageType
    importance: MessageImportance
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "message_type": self.message_type.value,
            "importance": self.importance.value,
            "metadata": self.metadata or {}
        }


@dataclass
class Portfolio:
    """User portfolio state."""
    user_id: str
    total_value: float
    cash: float
    positions: Dict[str, Dict[str, Any]]  # {symbol: {shares, value, weight}}
    updated_at: datetime


@dataclass
class MarketData:
    """Current market conditions."""
    spy_price: float
    spy_change_pct: float
    vix: float
    vix_change: float
    market_open: bool
    volume_ratio: float
    timestamp: datetime


@dataclass
class Strategy:
    """Portfolio strategy recommendation."""
    id: str
    summary: str
    target_allocation: Dict[str, float]
    recommended_trades: List[Dict[str, Any]]
    confidence: float
    risk_assessment: RiskLevel
    timestamp: datetime


@dataclass
class RiskAnalysis:
    """Risk assessment from Monte Carlo simulation."""
    median_outcome: float
    percentile_5: float
    percentile_95: float
    max_drawdown: float
    prob_loss: float
    sharpe_ratio: float
    var_95: float
    simulations: int
    timestamp: datetime


@dataclass
class TradeExecution:
    """Trade execution record."""
    trade_id: str
    timestamp: datetime
    status: str  # filled, pending, rejected
    orders: List[Dict[str, Any]]
    total_slippage: float
    total_value: float


@dataclass
class AnalysisResult:
    """Complete analysis result from orchestrator."""
    market_report: Dict[str, Any]
    strategy: Strategy
    risk_analysis: RiskAnalysis
    explanations: Dict[str, str]
    deliberation_summary: str
    final_recommendation: str
    approval_required: bool
    timestamp: datetime


# API Request/Response Models (for Pydantic)
class StrategyRequest:
    """Request to generate a strategy."""
    portfolio: Portfolio
    user_profile: Dict[str, Any]
    risk_constraints: Optional[Dict[str, Any]]


class UserInterjectionInput:
    """User input during deliberation."""
    action: str  # "comment", "adjust_risk", "approve", "reject", "pause"
    message: Optional[str]
    data: Optional[Dict[str, Any]]
    timestamp: datetime


class OrchestratorConfig:
    """Configuration for orchestrator."""
    max_deliberation_rounds: int = 5
    enable_gpu: bool = True
    market_data_cache_ttl: int = 300
    require_user_approval: bool = True
    enable_logging: bool = True
    model: str = "nvidia/llama-3.1-nemotron-70b-instruct"
