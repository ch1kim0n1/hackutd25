# backend/services/postgres_db.py
"""
PostgreSQL database connection and session management for APEX.
Handles all structured financial data (users, portfolios, trades, goals, etc.)
"""
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager

# Database URL from environment
DATABASE_URL = os.getenv(
    "POSTGRES_URL",
    "postgresql+asyncpg://apex_user:apex_password@localhost:5432/apex_db"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging during development
    pool_pre_ping=True,  # Verify connections before using
    pool_size=20,  # Connection pool size
    max_overflow=10,  # Additional connections beyond pool_size
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for all SQLAlchemy models
Base = declarative_base()


# Dependency for FastAPI endpoints
async def get_postgres_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.
    Usage in FastAPI:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_postgres_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session():
    """
    Context manager for database sessions outside of FastAPI.
    Usage:
        async with get_db_session() as db:
            result = await db.execute(query)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database: create all tables.
    Called on application startup.
    """
    async with engine.begin() as conn:
        # Import all models to register them with Base
        from ..models import user, portfolio, trade, goal, subscription, performance

        # Create pgvector extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Close database connections.
    Called on application shutdown.
    """
    await engine.dispose()
