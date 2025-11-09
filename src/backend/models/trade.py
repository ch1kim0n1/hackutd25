# backend/models/trade.py
"""
Trade model for APEX - stores all trade orders and execution history.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, JSON, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..services.postgres_db import Base


class Trade(Base):
    __tablename__ = "trades"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key to Portfolio
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)

    # Trade Identification
    broker_order_id = Column(String(255), unique=True, index=True)  # Broker's order ID (e.g., Alpaca)
    client_order_id = Column(String(255), unique=True, index=True)  # Our internal order ID

    # Asset Information
    symbol = Column(String(20), nullable=False, index=True)
    asset_class = Column(String(50), default="stock")

    # Order Details
    side = Column(String(10), nullable=False)  # buy, sell
    order_type = Column(String(20), nullable=False)  # market, limit, stop, stop_limit
    time_in_force = Column(String(10), default="day")  # day, gtc, ioc, fok

    # Quantity and Pricing
    quantity = Column(Numeric(15, 8), nullable=False)  # Support fractional shares
    filled_quantity = Column(Numeric(15, 8), default=0.0)
    limit_price = Column(Numeric(15, 4))  # For limit orders
    stop_price = Column(Numeric(15, 4))  # For stop orders
    filled_avg_price = Column(Numeric(15, 4))  # Average execution price

    # Financial Details
    notional = Column(Numeric(15, 2))  # Dollar amount (for fractional shares)
    filled_notional = Column(Numeric(15, 2))  # Actual dollar amount filled
    commission = Column(Numeric(10, 4), default=0.0)  # Trading commission
    slippage = Column(Numeric(10, 4))  # Difference between expected and actual price

    # Order Status
    status = Column(String(20), nullable=False, default="pending", index=True)
    # Status values: pending, submitted, partially_filled, filled, cancelled, rejected, expired

    # Agent Attribution (which agents approved this trade)
    strategy_agent_id = Column(String(50))  # Which strategy agent recommended
    risk_agent_approved = Column(Integer, default=0)  # Did risk agent approve?
    executor_agent_id = Column(String(50))  # Which executor executed

    # Trade Reasoning (for audit trail)
    reasoning = Column(Text)  # Why was this trade made?
    agent_confidence = Column(Float)  # Agent's confidence score (0-1)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime)  # When submitted to broker
    filled_at = Column(DateTime)  # When fully filled
    cancelled_at = Column(DateTime)  # When cancelled
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Error Handling
    error_message = Column(Text)  # If order failed

    # Metadata
    metadata = Column(JSON, default=dict)  # Additional broker-specific data

    # Relationships
    portfolio = relationship("Portfolio", back_populates="trades")

    def __repr__(self):
        return f"<Trade(id={self.id}, symbol={self.symbol}, side={self.side}, qty={self.quantity}, status={self.status})>"

    def to_dict(self):
        """Convert trade to dictionary"""
        return {
            "id": str(self.id),
            "portfolio_id": str(self.portfolio_id),
            "broker_order_id": self.broker_order_id,
            "client_order_id": self.client_order_id,
            "symbol": self.symbol,
            "asset_class": self.asset_class,
            "side": self.side,
            "order_type": self.order_type,
            "time_in_force": self.time_in_force,
            "quantity": float(self.quantity) if self.quantity else 0.0,
            "filled_quantity": float(self.filled_quantity) if self.filled_quantity else 0.0,
            "limit_price": float(self.limit_price) if self.limit_price else None,
            "stop_price": float(self.stop_price) if self.stop_price else None,
            "filled_avg_price": float(self.filled_avg_price) if self.filled_avg_price else None,
            "notional": float(self.notional) if self.notional else None,
            "filled_notional": float(self.filled_notional) if self.filled_notional else None,
            "commission": float(self.commission) if self.commission else 0.0,
            "slippage": float(self.slippage) if self.slippage else None,
            "status": self.status,
            "strategy_agent_id": self.strategy_agent_id,
            "risk_agent_approved": bool(self.risk_agent_approved),
            "executor_agent_id": self.executor_agent_id,
            "reasoning": self.reasoning,
            "agent_confidence": self.agent_confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }
