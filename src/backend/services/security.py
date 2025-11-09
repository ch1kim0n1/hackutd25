# backend/services/security.py
"""
Security services for APEX: 2FA, rate limiting, encryption, and authentication.
"""
import os
import hashlib
import secrets
from typing import Optional, Dict
from datetime import datetime, timedelta
import pyotp
from cryptography.fernet import Fernet
from passlib.context import CryptContext
import jwt


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordService:
    """Password hashing and verification"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)


class TwoFactorAuth:
    """Two-factor authentication using TOTP (Time-based One-Time Password)"""

    @staticmethod
    def generate_secret() -> str:
        """Generate a new 2FA secret key"""
        return pyotp.random_base32()

    @staticmethod
    def get_totp_uri(secret: str, username: str, issuer: str = "APEX") -> str:
        """
        Get TOTP provisioning URI for QR code generation.

        Args:
            secret: 2FA secret key
            username: User's username
            issuer: Issuer name (app name)

        Returns:
            Provisioning URI (otpauth://...)
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=username, issuer_name=issuer)

    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """
        Verify a TOTP token.

        Args:
            secret: User's 2FA secret
            token: 6-digit token from authenticator app

        Returns:
            True if valid
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # Allow 1 period before/after

    @staticmethod
    def get_current_token(secret: str) -> str:
        """Get current TOTP token (for testing)"""
        totp = pyotp.TOTP(secret)
        return totp.now()


class EncryptionService:
    """Encrypt/decrypt sensitive data (API keys, access tokens)"""

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption service.

        Args:
            encryption_key: Base64-encoded Fernet key (generate with Fernet.generate_key())
        """
        if encryption_key:
            self.key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        else:
            # Get from environment or generate
            self.key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())

        self.fernet = Fernet(self.key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext.

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted string (base64-encoded)
        """
        encrypted = self.fernet.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext.

        Args:
            ciphertext: Encrypted string

        Returns:
            Decrypted plaintext
        """
        decrypted = self.fernet.decrypt(ciphertext.encode())
        return decrypted.decode()

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key"""
        return Fernet.generate_key().decode()


class JWTService:
    """JWT token generation and validation for API authentication"""

    def __init__(self, secret_key: Optional[str] = None):
        """Initialize JWT service"""
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60  # 1 hour
        self.refresh_token_expire_days = 30  # 30 days

    def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token.

        Args:
            data: Data to encode in token (e.g., {"sub": user_id})
            expires_delta: Optional custom expiration

        Returns:
            JWT token string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire, "type": "access"})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: Dict) -> str:
        """Create JWT refresh token (longer expiration)"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token data or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # Token expired
        except jwt.JWTError:
            return None  # Invalid token


class RateLimiter:
    """
    Rate limiting for API endpoints.
    In-memory implementation (use Redis in production for distributed systems).
    """

    def __init__(self):
        """Initialize rate limiter"""
        self.requests = {}  # {key: [(timestamp, count), ...]}
        self.limits = {
            "default": {"requests": 100, "window": 60},  # 100 requests per minute
            "auth": {"requests": 5, "window": 60},  # 5 auth attempts per minute
            "trade": {"requests": 10, "window": 60},  # 10 trades per minute
            "plaid": {"requests": 20, "window": 60},  # 20 Plaid requests per minute
        }

    def check_rate_limit(
        self,
        key: str,
        limit_type: str = "default"
    ) -> tuple[bool, Optional[int]]:
        """
        Check if request is within rate limit.

        Args:
            key: Unique identifier (user_id, IP, etc.)
            limit_type: Type of limit to apply

        Returns:
            (is_allowed, retry_after_seconds)
        """
        limit_config = self.limits.get(limit_type, self.limits["default"])
        max_requests = limit_config["requests"]
        window_seconds = limit_config["window"]

        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        # Get or initialize request log for this key
        if key not in self.requests:
            self.requests[key] = []

        # Clean old requests outside window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]

        # Check if under limit
        if len(self.requests[key]) < max_requests:
            self.requests[key].append(now)
            return True, None
        else:
            # Calculate retry-after
            oldest_request = min(self.requests[key])
            retry_after = (oldest_request + timedelta(seconds=window_seconds) - now).seconds
            return False, retry_after

    def reset(self, key: str):
        """Reset rate limit for a key"""
        if key in self.requests:
            del self.requests[key]


class APIKeyService:
    """Manage API keys for third-party integrations"""

    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure random API key"""
        return f"apex_{secrets.token_urlsafe(32)}"

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for storage (never store plaintext)"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    @staticmethod
    def verify_api_key(api_key: str, hashed_key: str) -> bool:
        """Verify API key against stored hash"""
        return hashlib.sha256(api_key.encode()).hexdigest() == hashed_key


# Global instances
password_service = PasswordService()
two_factor_auth = TwoFactorAuth()
encryption_service = EncryptionService()
jwt_service = JWTService()
rate_limiter = RateLimiter()
api_key_service = APIKeyService()
