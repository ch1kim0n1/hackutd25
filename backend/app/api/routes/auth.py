"""
Authentication API routes
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Dict

from app.services.security import login_user, refresh_access_token, logout_user, get_current_user

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


@router.post("/login")
async def login(request: LoginRequest):
    """
    Authenticate user and return access + refresh tokens

    Request body:
        {
            "username": "user@example.com",
            "password": "secure_password"
        }

    Returns:
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer",
            "expires_in": 900
        }
    """
    return await login_user(request.username, request.password)


@router.post("/refresh")
async def refresh(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token

    Request body:
        {
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
        }

    Returns:
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer",
            "expires_in": 900
        }
    """
    return await refresh_access_token(request.refresh_token)


@router.post("/logout")
async def logout(background_tasks: BackgroundTasks, request: Request):
    """
    Logout user by revoking their access token

    Header:
        Authorization: Bearer <access_token>

    Returns:
        {
            "message": "Successfully logged out"
        }
    """
    auth_header = request.headers.get("authorization", "")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token_str = auth_header[7:]
    await logout_user(token_str)

    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_me(request: Request):
    """
    Get current authenticated user info

    Header:
        Authorization: Bearer <access_token>

    Returns:
        {
            "id": "uuid",
            "username": "user@example.com",
            "email": "user@example.com",
            "created_at": "2024-01-01T00:00:00Z"
        }
    """
    auth_header = request.headers.get("authorization", "")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token_str = auth_header[7:]
    user = await get_current_user(token_str)

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }