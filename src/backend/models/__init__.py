# backend/models/__init__.py
"""
Database models for APEX.
All SQLAlchemy models must be imported here to ensure they are registered with Base.
"""

from .user import User
from .portfolio import Portfolio, Position
from .trade import Trade
from .goal import Goal
from .subscription import Subscription
from .performance import PerformanceRecord, AgentDecisionLog

__all__ = [
    "User",
    "Portfolio",
    "Position",
    "Trade",
    "Goal",
    "Subscription",
    "PerformanceRecord",
    "AgentDecisionLog",
]
