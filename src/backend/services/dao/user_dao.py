# backend/services/dao/user_dao.py
"""
Data Access Object for User model.
Handles all database operations for users.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ...models.user import User


class UserDAO:
    """User Data Access Object"""

    @staticmethod
    async def create(
        db: AsyncSession,
        username: str,
        email: str,
        hashed_password: str,
        **kwargs
    ) -> Optional[User]:
        """Create a new user"""
        try:
            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                **kwargs
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except IntegrityError:
            await db.rollback()
            return None

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        result = await db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, user_id: str, **kwargs) -> Optional[User]:
        """Update user"""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**kwargs, updated_at=datetime.utcnow())
            .returning(User)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()

    @staticmethod
    async def update_last_login(db: AsyncSession, user_id: str) -> Optional[User]:
        """Update user's last login timestamp"""
        return await UserDAO.update(db, user_id, last_login=datetime.utcnow())

    @staticmethod
    async def update_preferences(db: AsyncSession, user_id: str, preferences: dict) -> Optional[User]:
        """Update user preferences"""
        return await UserDAO.update(db, user_id, preferences=preferences)

    @staticmethod
    async def activate(db: AsyncSession, user_id: str) -> Optional[User]:
        """Activate user account"""
        return await UserDAO.update(db, user_id, is_active=True)

    @staticmethod
    async def deactivate(db: AsyncSession, user_id: str) -> Optional[User]:
        """Deactivate user account"""
        return await UserDAO.update(db, user_id, is_active=False)

    @staticmethod
    async def verify_email(db: AsyncSession, user_id: str) -> Optional[User]:
        """Mark user email as verified"""
        return await UserDAO.update(db, user_id, is_verified=True)

    @staticmethod
    async def enable_2fa(db: AsyncSession, user_id: str, secret: str) -> Optional[User]:
        """Enable two-factor authentication"""
        return await UserDAO.update(
            db,
            user_id,
            two_factor_enabled=True,
            two_factor_secret=secret
        )

    @staticmethod
    async def disable_2fa(db: AsyncSession, user_id: str) -> Optional[User]:
        """Disable two-factor authentication"""
        return await UserDAO.update(
            db,
            user_id,
            two_factor_enabled=False,
            two_factor_secret=None
        )

    @staticmethod
    async def store_plaid_token(db: AsyncSession, user_id: str, access_token: str) -> Optional[User]:
        """Store Plaid access token (should be encrypted in production)"""
        return await UserDAO.update(db, user_id, plaid_access_token=access_token)

    @staticmethod
    async def store_alpaca_keys(
        db: AsyncSession,
        user_id: str,
        api_key: str,
        secret_key: str
    ) -> Optional[User]:
        """Store Alpaca API keys (should be encrypted in production)"""
        return await UserDAO.update(
            db,
            user_id,
            alpaca_api_key=api_key,
            alpaca_secret_key=secret_key
        )

    @staticmethod
    async def delete(db: AsyncSession, user_id: str) -> bool:
        """Delete user (soft delete by deactivating is recommended)"""
        stmt = delete(User).where(User.id == user_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def count(db: AsyncSession) -> int:
        """Count total users"""
        result = await db.execute(select(User))
        return len(list(result.scalars().all()))
