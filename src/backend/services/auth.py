"""
Authentication service - wraps API auth functions for use in services
"""
from typing import Dict, Optional
from fastapi import HTTPException
from uuid import UUID

from ..api.auth import (
    login_user as _login_user,
    refresh_access_token as _refresh_access_token,
    get_current_user as _get_current_user,
    logout_user as _logout_user,
)


async def login_user(username: str, password: str) -> Dict:
    """
    Authenticate user and return tokens
    
    Args:
        username: User's username or email
        password: User's plaintext password
    
    Returns:
        {
            "access_token": str,
            "refresh_token": str,
            "token_type": "bearer",
            "expires_in": int (seconds)
        }
    
    Raises:
        HTTPException: 401 on invalid credentials
    """
    return await _login_user(username, password)


async def refresh_access_token(refresh_token: str) -> Dict:
    """
    Issue new access token using refresh token
    
    Args:
        refresh_token: Valid refresh token
    
    Returns:
        {
            "access_token": str,
            "token_type": "bearer",
            "expires_in": int (seconds)
        }
    
    Raises:
        HTTPException: 401 on invalid/expired refresh token
    """
    return await _refresh_access_token(refresh_token)


async def get_current_user(token: str):
    """
    Validate token and return current user
    
    Args:
        token: JWT access token
    
    Returns:
        User model instance
    
    Raises:
        HTTPException: 401 on invalid/expired token, 403 on blacklisted token
    """
    return await _get_current_user(token)


async def logout_user(token: str) -> None:
    """
    Revoke user's access token
    
    Args:
        token: JWT access token to revoke
    
    Raises:
        HTTPException: 401 on invalid token
    """
    return await _logout_user(token)
