"""
Database configuration and utilities
"""

import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from app.core.settings import settings

logger = logging.getLogger(__name__)

# Try to import SQLAlchemy components, but allow app to run without them in demo mode
try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy.orm import DeclarativeBase
    from sqlalchemy.pool import NullPool
    
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        poolclass=NullPool if settings.ENVIRONMENT == "testing" else None,
    )

    # Create async session factory
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    database_available = True
except ImportError as e:
    logger.warning(f"Database dependencies not available: {e}. Running in demo mode without database.")
    engine = None
    AsyncSessionLocal = None
    database_available = False
    
    # Create a mock DeclarativeBase for compatibility
    class DeclarativeBase:
        pass


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.

    Usage:
        async with get_db() as db:
            # use db
            pass
    """
    if not database_available or AsyncSessionLocal is None:
        logger.warning("Database not available, yielding None")
        yield None
        return
        
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()


async def create_tables():
    """Create all database tables"""
    if not database_available or engine is None:
        logger.warning("Database not available, skipping table creation")
        return
        
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from app.models import user, portfolio, trade, goal, agent_log  # noqa: F401
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise


async def drop_tables():
    """Drop all database tables (for testing/cleanup)"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("✅ Database tables dropped successfully")
    except Exception as e:
        logger.error(f"❌ Failed to drop database tables: {e}")
        raise


async def init_db():
    """Initialize database with tables and migrations"""
    logger.info("📊 Initializing database...")

    # Create tables
    await create_tables()

    # Run Alembic migrations if available
    try:
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

        # Upgrade to latest
        command.upgrade(alembic_cfg, "head")
        logger.info("✅ Database migrations applied")

    except ImportError:
        logger.warning("Alembic not available, skipping migrations")
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        raise


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("✅ Database connections closed")


# Health check
async def check_db_connection() -> bool:
    """Check if database is accessible"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
