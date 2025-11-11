"""
APEX API Routers
Modular endpoint organization for better maintainability.
"""

from .auth import router as auth_router
from .system import router as system_router
from .portfolio import router as portfolio_router

__all__ = [
    "auth_router",
    "system_router",
    "portfolio_router",
]
