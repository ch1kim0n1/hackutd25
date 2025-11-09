# backend/services/dao/user_dao.py
"""
Data Access Object for User model.
Handles all database operations for users with proper async support.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from uuid import UUID
import logging

from ...models.user import User

logger = logging.getLogger(__name__)


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
            logger.info(f"User created: {username}")
            return user
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"User creation failed (duplicate): {e}")
            return None
        except Exception as e:
            await db.rollback()
            logger.error(f"User creation error: {e}")
            raise

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id) -> Optional[User]:
        """Get user by ID"""
        try:
            if isinstance(user_id, str):
                user_id = UUID(user_id)
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            result = await db.execute(select(User).where(User.username == username))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching user {username}: {e}")
            return None

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            result = await db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {e}")
            return None

    @staticmethod
    async def update(
        db: AsyncSession,
        user_id,
        **kwargs
    ) -> Optional[User]:
        """Update user fields"""
        try:
            if isinstance(user_id, str):
                user_id = UUID(user_id)
            
            stmt = update(User).where(User.id == user_id).values(**kwargs)
            await db.execute(stmt)
            await db.commit()
            
            # Fetch updated user
            return await UserDAO.get_by_id(db, user_id)
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            raise

    @staticmethod
    async def delete(db: AsyncSession, user_id) -> bool:
        """Delete a user"""
        try:
            if isinstance(user_id, str):
                user_id = UUID(user_id)
            
            stmt = delete(User).where(User.id == user_id)
            result = await db.execute(stmt)
            await db.commit()
            logger.info(f"User {user_id} deleted")
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting user {user_id}: {e}")
            return False

    @staticmethod
    async def list_all(
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """List all users with pagination"""
        try:
            stmt = select(User).limit(limit).offset(offset)
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

    @staticmethod
    async def search_by_username(
        db: AsyncSession,
        username_pattern: str
    ) -> List[User]:
        """Search users by username pattern"""
        try:
            stmt = select(User).where(User.username.like(f"%{username_pattern}%"))
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []

    @staticmethod
    async def count_active_users(db: AsyncSession) -> int:
        """Count active users"""
        try:
            result = await db.execute(select(User).where(User.is_active == True))
            return len(result.scalars().all())
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0
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
    async def set_encrypted_credential(
        db: AsyncSession,
        user_id: UUID,
        credential_type: str,
        plaintext_value: str
    ) -> bool:
        """
        Encrypt and store a credential for a user.
        
        Args:
            db: Database session
            user_id: User ID
            credential_type: 'plaid_token', 'alpaca_api_key', or 'alpaca_secret_key'
            plaintext_value: The plaintext credential to encrypt
        
        Returns:
            True if successful, False otherwise
        """
        from ..credential_encryption import CredentialEncryptionService
        
        try:
            # Get user and their encryption key
            user = await UserDAO.get_by_id(db, user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # If user doesn't have an encryption key, generate one
            if not user.encryption_key:
                user.encryption_key = CredentialEncryptionService.generate_encryption_key()
                logger.info(f"Generated encryption key for user {user_id}")
            
            # Encrypt the credential
            ciphertext = CredentialEncryptionService.encrypt_credential(
                plaintext_value,
                user.encryption_key
            )
            
            # Store the encrypted credential
            if credential_type == 'plaid_token':
                user.plaid_access_token = ciphertext
            elif credential_type == 'alpaca_api_key':
                user.alpaca_api_key = ciphertext
            elif credential_type == 'alpaca_secret_key':
                user.alpaca_secret_key = ciphertext
            else:
                logger.error(f"Unknown credential type: {credential_type}")
                return False
            
            await db.commit()
            logger.info(f"Encrypted credential stored for user {user_id}: {credential_type}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to set encrypted credential: {e}")
            return False

    @staticmethod
    async def get_encrypted_credential(
        db: AsyncSession,
        user_id: UUID,
        credential_type: str
    ) -> Optional[str]:
        """
        Retrieve and decrypt a credential for a user.
        
        Args:
            db: Database session
            user_id: User ID
            credential_type: 'plaid_token', 'alpaca_api_key', or 'alpaca_secret_key'
        
        Returns:
            Decrypted plaintext credential, or None if not found
        """
        from ..credential_encryption import CredentialEncryptionService
        
        try:
            # Get user
            user = await UserDAO.get_by_id(db, user_id)
            if not user or not user.encryption_key:
                logger.error(f"User or encryption key not found for {user_id}")
                return None
            
            # Get the encrypted credential
            if credential_type == 'plaid_token':
                ciphertext = user.plaid_access_token
            elif credential_type == 'alpaca_api_key':
                ciphertext = user.alpaca_api_key
            elif credential_type == 'alpaca_secret_key':
                ciphertext = user.alpaca_secret_key
            else:
                logger.error(f"Unknown credential type: {credential_type}")
                return None
            
            if not ciphertext:
                logger.warning(f"No credential stored for user {user_id}: {credential_type}")
                return None
            
            # Decrypt and return
            plaintext = CredentialEncryptionService.decrypt_credential(
                ciphertext,
                user.encryption_key
            )
            
            return plaintext
            
        except Exception as e:
            logger.error(f"Failed to get encrypted credential: {e}")
            return None

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
