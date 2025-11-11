# backend/api/auth.py
"""
Authentication endpoints and dependency injection for APEX API.
Handles JWT tokens with refresh, expiration, and revocation.
"""
import os
from typing import Optional, Dict
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
import jwt
from services.security import PasswordService, JWTService
from services.dao.json_dao import UserDAO
import logging

logger = logging.getLogger(__name__)

# Initialize services
jwt_service = JWTService(secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production"))
password_service = PasswordService()
user_dao = UserDAO()

# Token revocation list (in production, use Redis)
token_blacklist: set = set()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def login_user(username: str, password: str) -> Dict:
    """
    Authenticate user and return access + refresh tokens.

    Args:
        username: User's username
        password: User's plaintext password

    Returns:
        {"access_token": str, "refresh_token": str, "token_type": "bearer"}

    Raises:
        HTTPException(401): Invalid credentials
    """
    try:
        user = user_dao.get_user_by_username(username)
        if not user:
            logger.warning(f"Login failed: user {username} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Verify password
        if not password_service.verify_password(password, user.hashed_password):
            logger.warning(f"Login failed: invalid password for {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Create tokens
        access_token = jwt_service.create_access_token({"sub": str(user.id), "type": "access"})
        refresh_token = jwt_service.create_refresh_token({"sub": str(user.id), "type": "refresh"})

        logger.info(f"User {username} logged in successfully")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": jwt_service.access_token_expire_minutes * 60
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def refresh_access_token(refresh_token: str) -> Dict:
    """
    Issue new access token using refresh token.
    
    Args:
        refresh_token: Valid refresh token
    
    Returns:
        {"access_token": str, "token_type": "bearer"}
    
    Raises:
        HTTPException(401): Invalid or expired refresh token
    """
    try:
        payload = jwt.decode(
            refresh_token,
            jwt_service.secret_key,
            algorithms=[jwt_service.algorithm]
        )
        
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Create new access token
        new_access_token = jwt_service.create_access_token({"sub": user_id, "type": "access"})
        
        logger.info(f"Refresh token used for user {user_id}")
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": jwt_service.access_token_expire_minutes * 60
        }
    
    except jwt.ExpiredSignatureError:
        logger.warning("Refresh token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency to extract and validate current user from JWT token.
    
    Args:
        token: JWT token from Authorization header
    
    Returns:
        User object from database
    
    Raises:
        HTTPException(401): Invalid, expired, or revoked token
        HTTPException(403): Token is not an access token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Check if token is blacklisted (revoked)
        if token in token_blacklist:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        payload = jwt.decode(
            token,
            jwt_service.secret_key,
            algorithms=[jwt_service.algorithm]
        )
        
        # Verify token type
        token_type = payload.get("type")
        if token_type != "access":
            logger.warning(f"Invalid token type in token: {token_type}")
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("No 'sub' claim in token")
            raise credentials_exception
        
        # Load user from database
        user = user_dao.get_user_by_id(user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return user
    
    except jwt.ExpiredSignatureError:
        logger.info("Expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Auth error: {e}", exc_info=True)
        raise credentials_exception


async def logout_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Revoke user's token by adding to blacklist.
    
    Args:
        token: JWT token to revoke
    
    Returns:
        {"message": "Logged out successfully"}
    """
    try:
        payload = jwt.decode(
            token,
            jwt_service.secret_key,
            algorithms=[jwt_service.algorithm]
        )
        user_id = payload.get("sub")
        token_blacklist.add(token)
        logger.info(f"User {user_id} logged out")
        return {"message": "Logged out successfully"}
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
