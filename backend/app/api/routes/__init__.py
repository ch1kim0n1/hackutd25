"""
APEX API Routes
Consolidated API endpoints for the APEX backend.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

from app.core.settings import settings
# Import services with error handling for development
try:
    from app.services.orchestrator import Orchestrator
    orchestrator_available = True
except ImportError:
    orchestrator_available = False
    Orchestrator = None

try:
    from app.services.voice import VoiceService, voice_command_tracker
    voice_available = True
except ImportError:
    voice_available = False
    VoiceService = None
    voice_command_tracker = None

try:
    from app.services.rag.chroma_service import rag_engine
    rag_available = True
except ImportError:
    rag_available = False
    rag_engine = None

try:
    from app.services.finance_adapter import FinanceAdapter
    finance_available = True
except ImportError:
    finance_available = False
    FinanceAdapter = None

try:
    from app.services.logging_service import logger as structured_logger, RequestLogger
    logging_available = True
except ImportError:
    logging_available = False
    structured_logger = None
    RequestLogger = None

try:
    from app.services.alpaca import AlpacaService
    alpaca_available = True
except ImportError:
    alpaca_available = False
    AlpacaService = None

try:
    from app.services.personal_finance import PersonalFinanceService
    personal_finance_available = True
except ImportError:
    personal_finance_available = False
    PersonalFinanceService = None

try:
    from app.services.news_aggregator import news_aggregator
    news_available = True
except ImportError:
    news_available = False
    news_aggregator = None

try:
    from app.services.news_search import aggregate_news, web_search
    news_search_available = True
except ImportError:
    news_search_available = False
    aggregate_news = None
    web_search = None

try:
    from app.workers.crash_scenario_engine import CrashScenarioEngine
    crash_engine_available = True
except ImportError:
    crash_engine_available = False
    CrashScenarioEngine = None

try:
    from app.workers.crash_simulator import CrashScenario, simulate_crash
    crash_simulator_available = True
except ImportError:
    crash_simulator_available = False
    CrashScenario = None
    simulate_crash = None

try:
    from app.adapters.alpaca_broker import AlpacaBroker
    alpaca_broker_available = True
except ImportError:
    alpaca_broker_available = False
    AlpacaBroker = None

try:
    from app.services.war_room_interface import WarRoomInterface
    war_room_available = True
except ImportError:
    war_room_available = False
    WarRoomInterface = None

try:
    from app.services.seed_data import seed_test_data
    seed_available = True
except ImportError:
    seed_available = False
    seed_test_data = None

try:
    from app.services.historical_data import HistoricalDataLoader
    historical_data_available = True
except ImportError:
    historical_data_available = False
    HistoricalDataLoader = None

# Create the main API router
router = APIRouter()

logger = logging.getLogger(__name__)

# Global service instances (should be injected via dependency injection in production)
orchestrator = None
voice_service = None
finance_adapter = None
alpaca_broker = None
crash_engine = None
war_room = None

# Initialize services on import (simplified for now)
def init_services():
    """Initialize global service instances"""
    global orchestrator, voice_service, finance_adapter, alpaca_broker, crash_engine, war_room

    if orchestrator_available and not orchestrator:
        try:
            orchestrator = Orchestrator()
        except Exception as e:
            logger.warning(f"Failed to initialize orchestrator: {e}")

    if voice_available and not voice_service:
        try:
            voice_service = VoiceService()
        except Exception as e:
            logger.warning(f"Failed to initialize voice service: {e}")

    if finance_available and not finance_adapter:
        try:
            finance_adapter = FinanceAdapter()
        except Exception as e:
            logger.warning(f"Failed to initialize finance adapter: {e}")

    if alpaca_broker_available and not alpaca_broker:
        try:
            alpaca_broker = AlpacaBroker(paper=True)
        except Exception as e:
            logger.warning(f"Failed to initialize Alpaca broker: {e}")

    if crash_engine_available and historical_data_available and not crash_engine:
        try:
            data_loader = HistoricalDataLoader()
            crash_engine = CrashScenarioEngine(data_loader)
        except Exception as e:
            logger.warning(f"Failed to initialize crash engine: {e}")

    if war_room_available and not war_room:
        try:
            # For demo mode, create a mock agent network or skip initialization
            if settings.DEMO_MODE:
                logger.info("Demo mode: Skipping WarRoomInterface initialization")
                war_room = None
            else:
                # In full mode, we'd need to initialize agent_network first
                logger.warning("WarRoomInterface requires agent_network - not initialized in demo mode")
                war_room = None
        except Exception as e:
            logger.warning(f"Failed to initialize war room: {e}")

# Initialize services
init_services()

# Basic health endpoint (always available)
@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "APEX Backend is running"}

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

try:
    from . import trades
    router.include_router(trades.router, prefix="/api/v1/trades", tags=["Trading"])
    logger.info("✅ Trading routes loaded")
except ImportError as e:
    logger.warning(f"Trading routes not available: {e}")

try:
    from . import strategy
    router.include_router(strategy.router, prefix="/api/v1/strategy", tags=["Strategy"])
    logger.info("✅ Strategy routes loaded")
except ImportError as e:
    logger.warning(f"Strategy routes not available: {e}")

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
    from . import orchestrator_routes
    router.include_router(orchestrator_routes.router, prefix="/api/v1/orchestrator", tags=["Orchestrator"])
    logger.info("✅ Orchestrator routes loaded")
except ImportError as e:
    logger.warning(f"Orchestrator routes not available: {e}")

try:
    from . import crash_simulator
    router.include_router(crash_simulator.router, prefix="/api/v1/crash-simulator", tags=["Crash Simulator"])
    logger.info("✅ Crash simulator routes loaded")
except ImportError as e:
    logger.warning(f"Crash simulator routes not available: {e}")
