# backend/models/subscription.py
"""
Subscription model for APEX - tracks recurring subscriptions and identifies waste.
"""
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Float, JSON, ForeignKey, Integer, Numeric, Text, Date, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..services.postgres_db import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key to User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Subscription Details
    name = Column(String(200), nullable=False)  # e.g., "Netflix", "Spotify Premium"
    merchant = Column(String(200))  # Merchant name from Plaid
    category = Column(String(50))  # streaming, software, gym, etc.

    # Pricing
    amount = Column(Numeric(10, 2), nullable=False)  # Subscription amount
    currency = Column(String(3), default="USD")
    billing_cycle = Column(String(20), default="monthly")  # monthly, annual, quarterly

    # Calculated Annual Cost
    annual_cost = Column(Numeric(10, 2))  # amount * 12 (if monthly)

    # Recurring Transaction Detection
    plaid_transaction_id = Column(String(255))  # Original Plaid transaction ID
    is_auto_detected = Column(Boolean, default=True)  # Was this auto-detected by ML?
    detection_confidence = Column(Float)  # ML model confidence (0-1)

    # Status
    status = Column(String(20), default="active", index=True)  # active, cancelled, paused
    is_waste = Column(Boolean, default=False)  # Flagged as potential waste?
    waste_reason = Column(Text)  # Why flagged as waste

    # Usage Tracking
    last_used_date = Column(Date)  # When was this service last used (if trackable)
    usage_frequency = Column(String(20))  # daily, weekly, monthly, rarely, never

    # Savings Potential
    potential_savings = Column(Numeric(10, 2))  # How much could be saved if cancelled
    cheaper_alternative = Column(String(200))  # Suggested cheaper alternative
    alternative_savings = Column(Numeric(10, 2))  # Savings if switched to alternative

    # Renewal
    next_billing_date = Column(Date)
    renewal_reminder_sent = Column(Boolean, default=False)

    # Cancellation
    cancellation_requested = Column(Boolean, default=False)
    cancelled_at = Column(DateTime)
    cancellation_confirmation = Column(String(200))  # Confirmation number/ID

    # Timestamps
    first_detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata
    metadata = Column(JSON, default=dict)  # Additional subscription info

    # Relationships
    user = relationship("User", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription(id={self.id}, name={self.name}, amount=${self.amount}, status={self.status})>"

    def to_dict(self):
        """Convert subscription to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "merchant": self.merchant,
            "category": self.category,
            "amount": float(self.amount) if self.amount else 0.0,
            "currency": self.currency,
            "billing_cycle": self.billing_cycle,
            "annual_cost": float(self.annual_cost) if self.annual_cost else 0.0,
            "plaid_transaction_id": self.plaid_transaction_id,
            "is_auto_detected": self.is_auto_detected,
            "detection_confidence": self.detection_confidence,
            "status": self.status,
            "is_waste": self.is_waste,
            "waste_reason": self.waste_reason,
            "last_used_date": self.last_used_date.isoformat() if self.last_used_date else None,
            "usage_frequency": self.usage_frequency,
            "potential_savings": float(self.potential_savings) if self.potential_savings else None,
            "cheaper_alternative": self.cheaper_alternative,
            "alternative_savings": float(self.alternative_savings) if self.alternative_savings else None,
            "next_billing_date": self.next_billing_date.isoformat() if self.next_billing_date else None,
            "renewal_reminder_sent": self.renewal_reminder_sent,
            "cancellation_requested": self.cancellation_requested,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "cancellation_confirmation": self.cancellation_confirmation,
            "first_detected_at": self.first_detected_at.isoformat() if self.first_detected_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }
