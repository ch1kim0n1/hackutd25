"""
Centralized configuration for APEX backend.
Uses pydantic-settings for environment variable validation and type safety.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via .env file or environment variables.
    """

    # ============================================================================
    # Application
    # ============================================================================
    APP_NAME: str = "APEX Financial OS"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="development|staging|production")
    DEBUG: bool = Field(default=True, description="Enable debug mode")

    # ============================================================================
    # API Server
    # ============================================================================
    API_HOST: str = Field(default="0.0.0.0", description="API server host")
    API_PORT: int = Field(default=8000, description="API server port")
    API_BASE_URL: str = Field(default="http://localhost:8000", description="External API base URL")

    # ============================================================================
    # CORS
    # ============================================================================
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # ============================================================================
    # Database
    # ============================================================================
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://apex_user:apex_password@localhost:5432/apex_db",
        description="PostgreSQL connection URL"
    )
    DB_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=20, description="Max overflow connections")

    # ============================================================================
    # Redis
    # ============================================================================
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL for pub/sub and caching"
    )
    REDIS_ENABLED: bool = Field(
        default=True,
        description="Enable Redis (fallback to in-memory if disabled)"
    )

    # ============================================================================
    # Security & Authentication
    # ============================================================================
    JWT_SECRET_KEY: str = Field(
        default="CHANGEME_insecure_dev_secret_key_replace_in_production",
        description="Secret key for JWT token signing"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiry")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiry")

    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_SPECIAL: bool = True

    # ============================================================================
    # External APIs - AI/LLM
    # ============================================================================
    OPENROUTER_API_KEY: str = Field(
        default="",
        description="OpenRouter API key for LLM access"
    )
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    DEFAULT_LLM_MODEL: str = Field(
        default="nvidia/llama-3.1-nemotron-70b-instruct",
        description="Default LLM model for agents"
    )

    # ============================================================================
    # External APIs - Trading (Alpaca)
    # ============================================================================
    ALPACA_API_KEY: str = Field(default="", description="Alpaca API key")
    ALPACA_SECRET_KEY: str = Field(default="", description="Alpaca secret key")
    ALPACA_BASE_URL: str = Field(
        default="https://paper-api.alpaca.markets",
        description="Alpaca API base URL (paper or live)"
    )
    ALPACA_PAPER_TRADING: bool = Field(
        default=True,
        description="Use paper trading (safer default)"
    )

    # ============================================================================
    # External APIs - Banking (Plaid)
    # ============================================================================
    PLAID_CLIENT_ID: Optional[str] = Field(default=None, description="Plaid client ID")
    PLAID_SECRET: Optional[str] = Field(default=None, description="Plaid secret")
    PLAID_ENVIRONMENT: str = Field(
        default="sandbox",
        description="Plaid environment: sandbox|development|production"
    )
    PLAID_ENABLED: bool = Field(
        default=False,
        description="Enable Plaid integration (uses mock if disabled)"
    )

    # ============================================================================
    # Vector Database (ChromaDB for RAG)
    # ============================================================================
    CHROMA_PERSIST_DIRECTORY: str = Field(
        default="./data/chroma_db",
        description="ChromaDB persistence directory"
    )
    CHROMA_COLLECTION_NAME: str = Field(
        default="apex_financial_knowledge",
        description="ChromaDB collection name"
    )

    # ============================================================================
    # Voice Services
    # ============================================================================
    VOICE_ENABLED: bool = Field(default=False, description="Enable voice input/output")
    VOICE_MODEL: str = Field(default="base", description="Whisper model size")
    VOICE_RATE_LIMIT: int = Field(
        default=10,
        description="Max voice commands per minute"
    )

    # ============================================================================
    # Logging
    # ============================================================================
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="json",
        description="Log format: json|text"
    )
    LOG_FILE: Optional[str] = Field(
        default=None,
        description="Log file path (None = stdout only)"
    )

    # ============================================================================
    # Agent Orchestration
    # ============================================================================
    AGENT_TIMEOUT_SECONDS: int = Field(
        default=30,
        description="Default timeout for agent operations"
    )
    DEBATE_MAX_ROUNDS: int = Field(
        default=3,
        description="Maximum debate rounds between agents"
    )
    CONSENSUS_THRESHOLD: float = Field(
        default=0.7,
        description="Consensus threshold (0-1) for agent decisions"
    )

    # ============================================================================
    # GPU / Performance
    # ============================================================================
    ENABLE_GPU: bool = Field(
        default=False,
        description="Enable GPU acceleration (requires CUDA)"
    )
    GPU_DEVICE_ID: int = Field(default=0, description="GPU device ID")

    # ============================================================================
    # Feature Flags
    # ============================================================================
    ENABLE_CRASH_SIMULATOR: bool = Field(
        default=True,
        description="Enable market crash simulation features"
    )
    ENABLE_SUBSCRIPTION_DETECTION: bool = Field(
        default=True,
        description="Enable subscription detection in transactions"
    )

    class Config:
        env_file = "../../.env"  # Load from root
        env_file_encoding = "utf-8"
        env_prefix = "BACKEND_"  # All env vars prefixed with BACKEND_
        case_sensitive = False
        extra = "ignore"  # Ignore extra env vars


# ============================================================================
# Global settings instance
# ============================================================================
settings = Settings()


# ============================================================================
# Helper functions
# ============================================================================
def is_production() -> bool:
    """Check if running in production environment"""
    return settings.ENVIRONMENT.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment"""
    return settings.ENVIRONMENT.lower() == "development"


def get_db_url_sync() -> str:
    """Get synchronous database URL (for alembic)"""
    return settings.DATABASE_URL.replace("+asyncpg", "").replace("+psycopg", "")


def validate_settings() -> None:
    """
    Validate critical settings at startup.
    Raises ValueError if configuration is invalid.
    """
    errors = []

    # Check JWT secret in production
    if is_production() and "CHANGEME" in settings.JWT_SECRET_KEY:
        errors.append("JWT_SECRET_KEY must be changed in production")

    # Check required API keys
    if not settings.OPENROUTER_API_KEY:
        errors.append("OPENROUTER_API_KEY is required for agent operations")

    if not settings.ALPACA_API_KEY or not settings.ALPACA_SECRET_KEY:
        errors.append("ALPACA_API_KEY and ALPACA_SECRET_KEY are required for trading")

    # Validate URLs
    if not settings.API_BASE_URL.startswith(("http://", "https://")):
        errors.append("API_BASE_URL must start with http:// or https://")

    if errors:
        raise ValueError(
            "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )


# ============================================================================
# Export settings instance
# ============================================================================
__all__ = ["settings", "Settings", "validate_settings", "is_production", "is_development"]
