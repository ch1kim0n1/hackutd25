"""
Authentication Router
Handles user login, registration, logout, and token management.
"""

import logging
import os
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Rate limiter (will be shared from main app)
limiter = Limiter(key_func=get_remote_address)


# Pydantic Models
class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class UserRegistrationRequest(BaseModel):
    """User registration request model"""
    username: str
    email: str
    password: str


# Endpoints
@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, login_request: LoginRequest):
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
    from services.auth import login_user
    return await login_user(login_request.username, login_request.password)


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
    from services.auth import refresh_access_token
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
    from services.auth import logout_user

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
    from services.auth import get_current_user

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


@router.post("/register")
@limiter.limit("3/hour")
async def register_user(request: Request, registration: UserRegistrationRequest):
    """
    Register a new user account

    Request body:
        {
            "username": "newuser",
            "email": "user@example.com",
            "password": "secure_password"
        }

    Returns:
        {
            "message": "User created successfully",
            "user_id": "uuid",
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer"
        }
    """
    from services.dao.json_dao import UserDAO
    from services.security import PasswordService
    from services.jwt_service import JWTService

    user_dao = UserDAO()
    password_service = PasswordService()
    jwt_service = JWTService(secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production"))

    # Validate username doesn't exist
    existing_user = user_dao.get_user_by_username(registration.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Validate email doesn't exist
    existing_email = user_dao.get_user_by_email(registration.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    # Hash password
    hashed_password = password_service.hash_password(registration.password)

    # Create user
    user_data = {
        "username": registration.username,
        "email": registration.email,
        "hashed_password": hashed_password,
        "is_active": True,
        "is_verified": False,
        "risk_tolerance": "moderate",
        "investment_experience": "beginner"
    }

    try:
        user = user_dao.create_user(user_data)

        # Generate tokens for immediate login
        access_token = jwt_service.create_access_token({"sub": str(user.id), "type": "access"})
        refresh_token = jwt_service.create_refresh_token({"sub": str(user.id), "type": "refresh"})

        logger.info(f"✅ New user registered: {registration.username}")

        return {
            "message": "User created successfully",
            "user_id": str(user.id),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
