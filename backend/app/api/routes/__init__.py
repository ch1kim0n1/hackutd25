"""
APEX API Routes
Consolidated API endpoints for the APEX backend.
"""

from fastapi import APIRouter
import logging

# Create the main API router
router = APIRouter()

logger = logging.getLogger(__name__)

# Global service instances - set to None for demo mode
orchestrator = None
war_room = None

# Basic health endpoint (always available)
@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "APEX Backend is running"}

print("APEX Routes initialized in demo mode")

# Import and include essential route modules for demo
try:
    from . import agent_chat
    router.include_router(agent_chat.router, prefix="/chat", tags=["Agent Chat"])
    logger.info("✅ Agent chat routes loaded")
except ImportError as e:
    logger.warning(f"Agent chat routes not available: {e}")

try:
    from . import orchestrator_routes
    router.include_router(orchestrator_routes.router, prefix="/orchestrator", tags=["Orchestrator"])
    logger.info("✅ Orchestrator routes loaded")
except ImportError as e:
    logger.warning(f"Orchestrator routes not available: {e}")

# Import and include all route modules (with error handling)
try:
    from . import auth
    router.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    logger.info("✅ Auth routes loaded")
except ImportError as e:
    logger.warning(f"Auth routes not available: {e}")

try:
    from . import market
    router.include_router(market.router, prefix="/api/v1/market", tags=["Market Data"])
    logger.info("✅ Market routes loaded")
except ImportError as e:
    logger.warning(f"Market routes not available: {e}")

try:
    from . import portfolio
    router.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
    logger.info("✅ Portfolio routes loaded")
except ImportError as e:
    logger.warning(f"Portfolio routes not available: {e}")

# Trading routes - trades.py only contains utility functions, not a router
# try:
#     from . import trades
#     router.include_router(trades.router, prefix="/api/v1/trades", tags=["Trading"])
#     logger.info("✅ Trading routes loaded")
# except ImportError as e:
#     logger.warning(f"Trading routes not available: {e}")

# Strategy routes - strategy.py only contains utility functions, not a router
# try:
#     from . import strategy
#     router.include_router(strategy.router, prefix="/api/v1/strategy", tags=["Strategy"])
#     logger.info("✅ Strategy routes loaded")
# except ImportError as e:
#     logger.warning(f"Strategy routes not available: {e}")

try:
    from . import finance
    router.include_router(finance.router, prefix="/api/v1/finance", tags=["Personal Finance"])
    logger.info("✅ Finance routes loaded")
except ImportError as e:
    logger.warning(f"Finance routes not available: {e}")

try:
    from . import voice
    router.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice"])
    logger.info("✅ Voice routes loaded")
except ImportError as e:
    logger.warning(f"Voice routes not available: {e}")

try:
    from . import agent_chat
    router.include_router(agent_chat.router, prefix="/chat", tags=["Agent Chat"])
    logger.info("Agent chat routes loaded")
except ImportError as e:
    logger.warning(f"Agent chat routes not available: {e}")

try:
    from . import crash_simulator
    router.include_router(crash_simulator.router, prefix="/api/v1/crash-simulator", tags=["Crash Simulator"])
    logger.info("✅ Crash simulator routes loaded")
except ImportError as e:
    logger.warning(f"Crash simulator routes not available: {e}")
