# backend/models/goal.py
"""
Goal model for APEX - stores user financial goals and projections.
"""
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Float, JSON, ForeignKey, Integer, Numeric, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..services.postgres_db import Base


class Goal(Base):
    __tablename__ = "goals"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key to User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Goal Details
    name = Column(String(200), nullable=False)  # e.g., "Retire by 65", "$1M portfolio"
    description = Column(Text)
    goal_type = Column(String(50), default="retirement")  # retirement, house, education, general

    # Financial Target
    target_amount = Column(Numeric(15, 2), nullable=False)  # Target dollar amount
    current_amount = Column(Numeric(15, 2), default=0.0)  # Current progress
    initial_investment = Column(Numeric(15, 2), default=0.0)  # Starting amount

    # Timeline
    target_date = Column(Date, nullable=False)  # When to achieve goal
    years_to_goal = Column(Integer)  # Calculated: years until target_date

    # Contribution Plan
    monthly_contribution = Column(Numeric(10, 2), default=0.0)  # Monthly contribution amount
    annual_contribution = Column(Numeric(10, 2), default=0.0)  # Annual contribution (if not monthly)

    # Return Assumptions
    expected_return = Column(Float, default=0.07)  # Expected annual return (7% default)
    conservative_return = Column(Float, default=0.05)  # Conservative scenario (5%)
    aggressive_return = Column(Float, default=0.10)  # Aggressive scenario (10%)

    # Compounding
    compounding_frequency = Column(String(20), default="monthly")  # monthly, quarterly, annually

    # Goal Probability (calculated by Risk Agent)
    success_probability = Column(Float)  # Probability of achieving goal (0-1)
    conservative_projection = Column(Numeric(15, 2))  # Projected amount (conservative)
    moderate_projection = Column(Numeric(15, 2))  # Projected amount (moderate)
    aggressive_projection = Column(Numeric(15, 2))  # Projected amount (aggressive)

    # Risk Tolerance for This Goal
    risk_tolerance = Column(String(20), default="moderate")  # conservative, moderate, aggressive

    # Milestones (stored as JSON array)
    # Example: [{"date": "2026-01-01", "target": 100000, "achieved": false}, ...]
    milestones = Column(JSON, default=list)

    # Voice Input
    voice_input_text = Column(Text)  # Original voice input that created this goal

    # Status
    status = Column(String(20), default="active", index=True)  # active, achieved, paused, abandoned
    is_active = Column(Integer, default=1)

    # Agent Validation
    strategy_agent_validated = Column(Integer, default=0)  # Did Strategy Agent validate?
    risk_agent_validated = Column(Integer, default=0)  # Did Risk Agent validate?
    validation_notes = Column(Text)  # Agent feedback on goal achievability

    # Progress Tracking
    last_reviewed_at = Column(DateTime)  # When goal was last reviewed by agents
    progress_percentage = Column(Float, default=0.0)  # Current amount / target amount * 100

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    achieved_at = Column(DateTime)  # When goal was achieved

    # Relationships
    user = relationship("User", back_populates="goals")

    def __repr__(self):
        return f"<Goal(id={self.id}, name={self.name}, target=${self.target_amount}, status={self.status})>"

    def to_dict(self):
        """Convert goal to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "description": self.description,
            "goal_type": self.goal_type,
            "target_amount": float(self.target_amount) if self.target_amount else 0.0,
            "current_amount": float(self.current_amount) if self.current_amount else 0.0,
            "initial_investment": float(self.initial_investment) if self.initial_investment else 0.0,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "years_to_goal": self.years_to_goal,
            "monthly_contribution": float(self.monthly_contribution) if self.monthly_contribution else 0.0,
            "annual_contribution": float(self.annual_contribution) if self.annual_contribution else 0.0,
            "expected_return": self.expected_return,
            "conservative_return": self.conservative_return,
            "aggressive_return": self.aggressive_return,
            "compounding_frequency": self.compounding_frequency,
            "success_probability": self.success_probability,
            "conservative_projection": float(self.conservative_projection) if self.conservative_projection else None,
            "moderate_projection": float(self.moderate_projection) if self.moderate_projection else None,
            "aggressive_projection": float(self.aggressive_projection) if self.aggressive_projection else None,
            "risk_tolerance": self.risk_tolerance,
            "milestones": self.milestones,
            "voice_input_text": self.voice_input_text,
            "status": self.status,
            "is_active": bool(self.is_active),
            "strategy_agent_validated": bool(self.strategy_agent_validated),
            "risk_agent_validated": bool(self.risk_agent_validated),
            "validation_notes": self.validation_notes,
            "last_reviewed_at": self.last_reviewed_at.isoformat() if self.last_reviewed_at else None,
            "progress_percentage": self.progress_percentage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "achieved_at": self.achieved_at.isoformat() if self.achieved_at else None,
        }
