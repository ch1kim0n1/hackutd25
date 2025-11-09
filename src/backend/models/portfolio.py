# backend/models/portfolio.py
"""
Portfolio model for APEX - stores portfolio information and positions.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, JSON, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..services.postgres_db import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key to User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Portfolio Details
    name = Column(String(100), nullable=False, default="Main Portfolio")
    description = Column(String(500))
    portfolio_type = Column(String(50), default="brokerage")  # brokerage, ira, 401k, roth_ira, etc.

    # Broker Integration
    broker_name = Column(String(50), default="alpaca")  # alpaca, plaid, manual
    broker_account_id = Column(String(255))  # External broker account ID

    # Portfolio Metrics (cached for performance)
    total_value = Column(Numeric(15, 2), default=0.0)  # Current total portfolio value
    cash_balance = Column(Numeric(15, 2), default=0.0)  # Available cash
    buying_power = Column(Numeric(15, 2), default=0.0)  # Buying power (cash + margin)
    total_equity = Column(Numeric(15, 2), default=0.0)  # Equity (value - margin debt)

    # Performance Metrics
    total_pl = Column(Numeric(15, 2), default=0.0)  # Total profit/loss
    total_pl_pct = Column(Float, default=0.0)  # Total profit/loss percentage
    day_pl = Column(Numeric(15, 2), default=0.0)  # Day profit/loss
    day_pl_pct = Column(Float, default=0.0)  # Day profit/loss percentage

    # Risk Metrics (cached)
    current_var_95 = Column(Float)  # Value at Risk (95% confidence)
    current_var_99 = Column(Float)  # Value at Risk (99% confidence)
    sharpe_ratio = Column(Float)  # Risk-adjusted return
    max_drawdown = Column(Float)  # Maximum drawdown percentage
    beta = Column(Float)  # Portfolio beta vs S&P 500

    # Target Allocation (stored as JSON: {"AAPL": 0.10, "GOOGL": 0.15, ...})
    target_allocation = Column(JSON, default=dict)

    # Status
    is_active = Column(Integer, default=1)
    is_paper = Column(Integer, default=1)  # Paper trading vs live trading

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_synced_at = Column(DateTime)  # Last time synced with broker

    # Relationships
    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="portfolio", cascade="all, delete-orphan")
    performance_records = relationship("PerformanceRecord", back_populates="portfolio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Portfolio(id={self.id}, user_id={self.user_id}, name={self.name}, value=${self.total_value})>"

    def to_dict(self):
        """Convert portfolio to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "description": self.description,
            "portfolio_type": self.portfolio_type,
            "broker_name": self.broker_name,
            "broker_account_id": self.broker_account_id,
            "total_value": float(self.total_value) if self.total_value else 0.0,
            "cash_balance": float(self.cash_balance) if self.cash_balance else 0.0,
            "buying_power": float(self.buying_power) if self.buying_power else 0.0,
            "total_equity": float(self.total_equity) if self.total_equity else 0.0,
            "total_pl": float(self.total_pl) if self.total_pl else 0.0,
            "total_pl_pct": self.total_pl_pct,
            "day_pl": float(self.day_pl) if self.day_pl else 0.0,
            "day_pl_pct": self.day_pl_pct,
            "current_var_95": self.current_var_95,
            "current_var_99": self.current_var_99,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "beta": self.beta,
            "target_allocation": self.target_allocation,
            "is_active": bool(self.is_active),
            "is_paper": bool(self.is_paper),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
        }


class Position(Base):
    """Individual stock/asset position within a portfolio"""
    __tablename__ = "positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)

    # Asset Information
    symbol = Column(String(20), nullable=False, index=True)
    asset_class = Column(String(50), default="stock")  # stock, etf, option, crypto, bond
    exchange = Column(String(20))

    # Position Details
    quantity = Column(Numeric(15, 8), nullable=False)  # Support fractional shares
    average_entry_price = Column(Numeric(15, 4), nullable=False)
    current_price = Column(Numeric(15, 4))
    market_value = Column(Numeric(15, 2))

    # Profit/Loss
    unrealized_pl = Column(Numeric(15, 2))
    unrealized_pl_pct = Column(Float)
    realized_pl = Column(Numeric(15, 2), default=0.0)  # From closed portions

    # Cost Basis
    cost_basis = Column(Numeric(15, 2))  # Total cost (qty * avg_entry_price)

    # Timestamps
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")

    def __repr__(self):
        return f"<Position(symbol={self.symbol}, qty={self.quantity}, value=${self.market_value})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "portfolio_id": str(self.portfolio_id),
            "symbol": self.symbol,
            "asset_class": self.asset_class,
            "exchange": self.exchange,
            "quantity": float(self.quantity) if self.quantity else 0.0,
            "average_entry_price": float(self.average_entry_price) if self.average_entry_price else 0.0,
            "current_price": float(self.current_price) if self.current_price else 0.0,
            "market_value": float(self.market_value) if self.market_value else 0.0,
            "unrealized_pl": float(self.unrealized_pl) if self.unrealized_pl else 0.0,
            "unrealized_pl_pct": self.unrealized_pl_pct,
            "realized_pl": float(self.realized_pl) if self.realized_pl else 0.0,
            "cost_basis": float(self.cost_basis) if self.cost_basis else 0.0,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at else None,
        }
