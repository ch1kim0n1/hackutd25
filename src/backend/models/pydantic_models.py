"""
Pydantic models for JSON-based data storage.
Replaces SQLAlchemy database models with Pydantic validation models.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class InvestmentExperience(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class User(BaseModel):
    """User model for authentication and profile"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False

    # Profile
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None

    # Risk Profile
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    investment_experience: InvestmentExperience = InvestmentExperience.BEGINNER

    # Preferences
    preferences: Dict[str, Any] = Field(default_factory=dict)

    # Security
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None
    encryption_key: Optional[str] = None

    # External Integrations (store as base64 encrypted strings)
    plaid_access_token: Optional[str] = None
    alpaca_api_key: Optional[str] = None
    alpaca_secret_key: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self, exclude_sensitive: bool = True) -> Dict[str, Any]:
        """Convert to dictionary, optionally excluding sensitive fields"""
        data = self.dict()
        if exclude_sensitive:
            sensitive_fields = [
                'hashed_password', 'two_factor_secret', 'encryption_key',
                'plaid_access_token', 'alpaca_api_key', 'alpaca_secret_key'
            ]
            for field in sensitive_fields:
                data.pop(field, None)
        return data


class Portfolio(BaseModel):
    """Portfolio model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str = "Default Portfolio"
    description: Optional[str] = None
    total_value: float = 0.0
    cash_balance: float = 0.0
    positions: List[Dict[str, Any]] = Field(default_factory=list)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Trade(BaseModel):
    """Trade/Order model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    portfolio_id: str
    symbol: str
    side: str  # buy, sell
    order_type: str  # market, limit, stop, stop_limit
    quantity: float
    price: Optional[float] = None
    status: str = "pending"  # pending, filled, cancelled, rejected
    filled_quantity: float = 0.0
    filled_price: Optional[float] = None
    external_order_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    filled_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class Goal(BaseModel):
    """Financial goal model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: Optional[str] = None
    target_amount: float
    current_amount: float = 0.0
    target_date: Optional[datetime] = None
    status: GoalStatus = GoalStatus.ACTIVE
    category: Optional[str] = None  # retirement, education, home, etc.
    priority: int = 1  # 1-5
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.target_amount <= 0:
            return 0.0
        return min(100.0, (self.current_amount / self.target_amount) * 100)


class Account(BaseModel):
    """Linked financial account model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    account_name: str
    account_type: str  # checking, savings, credit, investment, etc.
    institution_name: str
    account_number_last4: Optional[str] = None
    balance: float = 0.0
    currency: str = "USD"
    is_active: bool = True
    plaid_account_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Transaction(BaseModel):
    """Financial transaction model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    account_id: str
    date: datetime
    description: str
    amount: float
    category: Optional[str] = None
    merchant: Optional[str] = None
    is_pending: bool = False
    plaid_transaction_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Subscription(BaseModel):
    """User subscription model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    tier: str = "free"  # free, basic, pro, enterprise
    status: str = "active"
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    auto_renew: bool = True
    payment_method: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VoiceCommand(BaseModel):
    """Voice command model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    command_text: str
    transcription: str
    intent: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # pending, confirmed, rejected, executed
    execution_result: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RAGDocument(BaseModel):
    """RAG document/embedding model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    document_name: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding_id: Optional[str] = None  # Reference to ChromaDB embedding
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
