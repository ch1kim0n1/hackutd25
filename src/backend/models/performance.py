# backend/models/performance.py
"""
Performance model for APEX - stores portfolio performance metrics over time.
"""
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Float, JSON, ForeignKey, Integer, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..services.postgres_db import Base


class PerformanceRecord(Base):
    """Daily snapshot of portfolio performance metrics"""
    __tablename__ = "performance_records"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key to Portfolio
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)

    # Date of this record
    record_date = Column(Date, nullable=False, index=True)

    # Portfolio Values
    total_value = Column(Numeric(15, 2), nullable=False)
    cash_balance = Column(Numeric(15, 2))
    equity_value = Column(Numeric(15, 2))

    # Returns
    daily_return = Column(Float)  # Daily return percentage
    cumulative_return = Column(Float)  # Cumulative return since inception
    ytd_return = Column(Float)  # Year-to-date return
    mtd_return = Column(Float)  # Month-to-date return

    # Profit/Loss
    daily_pl = Column(Numeric(15, 2))
    total_pl = Column(Numeric(15, 2))

    # Risk Metrics
    volatility = Column(Float)  # 30-day volatility
    sharpe_ratio = Column(Float)  # Risk-adjusted return
    sortino_ratio = Column(Float)  # Downside risk-adjusted return
    max_drawdown = Column(Float)  # Maximum drawdown from peak
    beta = Column(Float)  # Beta vs S&P 500
    alpha = Column(Float)  # Alpha vs S&P 500
    var_95 = Column(Float)  # Value at Risk (95%)
    var_99 = Column(Float)  # Value at Risk (99%)

    # Benchmark Comparison
    sp500_value = Column(Numeric(15, 2))  # Equivalent S&P 500 investment
    sp500_return = Column(Float)  # S&P 500 return for comparison
    outperformance = Column(Float)  # Portfolio return - benchmark return

    # Attribution (what drove performance)
    asset_allocation_return = Column(Float)  # Return from asset allocation
    security_selection_return = Column(Float)  # Return from security selection
    timing_return = Column(Float)  # Return from market timing

    # Position Count
    position_count = Column(Integer)  # Number of positions held
    sectors = Column(JSON, default=dict)  # Sector allocation: {"tech": 0.3, "finance": 0.2, ...}

    # Agent Performance
    agent_decisions_count = Column(Integer)  # Number of agent decisions today
    winning_trades_count = Column(Integer)  # Profitable trades
    losing_trades_count = Column(Integer)  # Unprofitable trades
    win_rate = Column(Float)  # Winning trades / total trades

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="performance_records")

    def __repr__(self):
        return f"<PerformanceRecord(date={self.record_date}, portfolio_id={self.portfolio_id}, value=${self.total_value})>"

    def to_dict(self):
        """Convert performance record to dictionary"""
        return {
            "id": str(self.id),
            "portfolio_id": str(self.portfolio_id),
            "record_date": self.record_date.isoformat() if self.record_date else None,
            "total_value": float(self.total_value) if self.total_value else 0.0,
            "cash_balance": float(self.cash_balance) if self.cash_balance else 0.0,
            "equity_value": float(self.equity_value) if self.equity_value else 0.0,
            "daily_return": self.daily_return,
            "cumulative_return": self.cumulative_return,
            "ytd_return": self.ytd_return,
            "mtd_return": self.mtd_return,
            "daily_pl": float(self.daily_pl) if self.daily_pl else 0.0,
            "total_pl": float(self.total_pl) if self.total_pl else 0.0,
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self.max_drawdown,
            "beta": self.beta,
            "alpha": self.alpha,
            "var_95": self.var_95,
            "var_99": self.var_99,
            "sp500_value": float(self.sp500_value) if self.sp500_value else None,
            "sp500_return": self.sp500_return,
            "outperformance": self.outperformance,
            "asset_allocation_return": self.asset_allocation_return,
            "security_selection_return": self.security_selection_return,
            "timing_return": self.timing_return,
            "position_count": self.position_count,
            "sectors": self.sectors,
            "agent_decisions_count": self.agent_decisions_count,
            "winning_trades_count": self.winning_trades_count,
            "losing_trades_count": self.losing_trades_count,
            "win_rate": self.win_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AgentDecisionLog(Base):
    """MongoDB-style model for logging agent decisions (stored in PostgreSQL for SQL queries)"""
    __tablename__ = "agent_decision_logs"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Agent Information
    agent_name = Column(String(50), nullable=False, index=True)  # market, strategy, risk, executor
    agent_id = Column(String(100), index=True)  # Specific agent instance ID

    # Decision Context
    decision_type = Column(String(50), nullable=False, index=True)  # trade, analysis, validation, alert
    decision_content = Column(JSON, nullable=False)  # Full decision data

    # Related Entities
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    portfolio_id = Column(UUID(as_uuid=True), index=True)
    trade_id = Column(UUID(as_uuid=True), index=True)

    # Decision Outcome
    confidence_score = Column(Float)  # Agent's confidence (0-1)
    was_executed = Column(Integer, default=0)  # Was the decision executed?
    execution_result = Column(String(20))  # success, failed, rejected, pending

    # Performance Tracking
    outcome_value = Column(Numeric(15, 2))  # Financial outcome (profit/loss)
    was_correct = Column(Integer)  # Was the decision correct in hindsight?

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    executed_at = Column(DateTime)
    outcome_measured_at = Column(DateTime)  # When we evaluated if decision was correct

    def __repr__(self):
        return f"<AgentDecisionLog(agent={self.agent_name}, type={self.decision_type}, confidence={self.confidence_score})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "decision_type": self.decision_type,
            "decision_content": self.decision_content,
            "user_id": str(self.user_id) if self.user_id else None,
            "portfolio_id": str(self.portfolio_id) if self.portfolio_id else None,
            "trade_id": str(self.trade_id) if self.trade_id else None,
            "confidence_score": self.confidence_score,
            "was_executed": bool(self.was_executed),
            "execution_result": self.execution_result,
            "outcome_value": float(self.outcome_value) if self.outcome_value else None,
            "was_correct": bool(self.was_correct) if self.was_correct is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "outcome_measured_at": self.outcome_measured_at.isoformat() if self.outcome_measured_at else None,
        }
