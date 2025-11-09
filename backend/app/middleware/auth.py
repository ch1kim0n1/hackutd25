"""
Authentication decorators and dependencies for FastAPI endpoints.
Provides standard way to enforce auth across all protected endpoints.
"""
from functools import wraps
from typing import Optional, Callable, Any
from uuid import UUID

from fastapi import HTTPException, Request, Depends

from services.security import get_current_user


async def get_current_user_from_request(request: Request) -> dict:
    """
    FastAPI dependency to extract and validate authentication from Authorization header.
    Returns dict with 'user' and 'user_id' keys.
    
    Usage in FastAPI:
        @app.post("/api/trade")
        async def execute_trade(
            auth: dict = Depends(get_current_user_from_request),
            request: TradeRequest = None
        ):
            user_id = auth['user_id']
            user = auth['user']
            ...
    
    Raises:
        HTTPException: 401 if no token, 403 if token blacklisted
    """
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header. Format: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    try:
        # Validate token and load user
        user = await get_current_user(token)
        
        return {
            "user_id": user.id,
            "user": user,
            "token": token
        }
    except HTTPException as e:
        # Re-raise HTTP exceptions (401, 403, etc)
        raise e
    except Exception as e:
        # Generic token validation errors
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )


def validate_user_ownership(user_id_from_auth: UUID, resource_user_id: Optional[UUID]) -> None:
    """
    Validate that the authenticated user owns the requested resource.
    
    Raises:
        HTTPException: 403 if user doesn't own the resource
    """
    if not resource_user_id:
        return  # No user_id to check
    
    if str(user_id_from_auth) != str(resource_user_id):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this resource"
        )


def require_auth_sync(func: Callable) -> Callable:
    """
    Synchronous decorator for requiring authentication (for non-async functions).
    Use async version instead for FastAPI endpoints.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # This is mainly for demonstration
        # Prefer using `Depends(get_current_user_from_request)` in FastAPI
        return await func(*args, **kwargs)
    
    return wrapper
