# backend/models/user.py
"""
User model for APEX - stores user authentication and profile information.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..services.postgres_db import Base


class User(Base):
    __tablename__ = "users"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Authentication
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Profile Information
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone_number = Column(String(20))

    # Risk Profile
    risk_tolerance = Column(String(20), default="moderate")  # conservative, moderate, aggressive
    investment_experience = Column(String(20), default="beginner")  # beginner, intermediate, advanced

    # Preferences
    preferences = Column(JSON, default=dict)  # Store UI preferences, notification settings, etc.

    # Security
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255))

    # External Integrations
    plaid_access_token = Column(String(255))  # Encrypted Plaid access token
    alpaca_api_key = Column(String(255))  # Encrypted Alpaca API key
    alpaca_secret_key = Column(String(255))  # Encrypted Alpaca secret

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime)

    # Relationships
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

    def to_dict(self):
        """Convert user to dictionary (excluding sensitive fields)"""
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone_number": self.phone_number,
            "risk_tolerance": self.risk_tolerance,
            "investment_experience": self.investment_experience,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "two_factor_enabled": self.two_factor_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "preferences": self.preferences,
        }
