"""
APEX System Constants
Centralized configuration constants used throughout the system.
"""

import os
from enum import Enum

# ======================================
# API & MODELS
# ======================================

# OpenRouter API Configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Anthropic API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Default Models
DEFAULT_MODEL = "nvidia/llama-3.1-nemotron-70b-instruct"
FALLBACK_MODEL = "nvidia/nemotron-nano-9b-v2:free"  # Free tier fallback
EXPLAINER_MODEL = "claude-sonnet-4-20250514"  # Use Claude for explanations

# ======================================
# TRADING & MARKET
# ======================================

# Alpaca Broker Configuration
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_PAPER_MODE = os.getenv("ALPACA_PAPER_MODE", "true").lower() == "true"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets" if ALPACA_PAPER_MODE else "https://api.alpaca.markets"

# Market Data
MARKET_DATA_CACHE_TTL = 300  # 5 minutes
HISTORICAL_DATA_DAYS = 252   # 1 trading year
VIX_THRESHOLD_LOW = 12.0      # Low volatility threshold
VIX_THRESHOLD_HIGH = 30.0     # High volatility threshold

# Portfolio Constraints
MAX_POSITION_SIZE = 0.20      # 20% max single position
MAX_SECTOR_EXPOSURE = 0.40    # 40% max sector exposure
MIN_CASH_RESERVE = 0.05       # 5% min cash
MAX_PORTFOLIO_DRAWDOWN = 0.15 # 15% max portfolio loss

# ======================================
# MONTE CARLO SIMULATIONS
# ======================================

DEFAULT_NUM_SIMULATIONS = 10000
GPU_SIMULATIONS = 100000  # Higher number with GPU acceleration
TIME_HORIZON_YEARS = 1.0
TRADING_DAYS_PER_YEAR = 252

# ======================================
# AGENT ORCHESTRATION
# ======================================

MAX_DELIBERATION_ROUNDS = 5
DELIBERATION_TIMEOUT_SECONDS = 300  # 5 minutes max deliberation
MESSAGE_BUFFER_SIZE = 500

# ======================================
# REDIS CONFIGURATION
# ======================================

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_DB = 0

# Redis channels
REDIS_CHANNEL_AGENTS = "agent_messages"
REDIS_CHANNEL_USER_INPUT = "user_input"
REDIS_CHANNEL_WAR_ROOM = "war_room"
REDIS_CHANNEL_ALERTS = "alerts"

# ======================================
# DATABASE
# ======================================

DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017/apex")

# Collection names
COLLECTION_USERS = "users"
COLLECTION_PORTFOLIOS = "portfolios"
COLLECTION_TRADES = "trades"
COLLECTION_STRATEGIES = "strategies"
COLLECTION_AGENT_LOGS = "agent_logs"

# ======================================
# API CONFIGURATION
# ======================================

API_VERSION = "1.0.0"
API_PREFIX = "/api"
API_TIMEOUT = 30  # seconds

# CORS
CORS_ORIGINS = ["*"]  # In production, restrict to specific origins
CORS_CREDENTIALS = True
CORS_METHODS = ["*"]
CORS_HEADERS = ["*"]

# ======================================
# VOICE I/O
# ======================================

VOICE_SAMPLE_RATE = 16000  # Hz
VOICE_CHANNELS = 1
VOICE_FORMAT = "wav"
VOICE_MAX_DURATION = 120  # seconds (2 minutes max)

# Speech Recognition
SPEECH_RECOGNITION_LANGUAGE = "en-US"
SPEECH_CONFIDENCE_THRESHOLD = 0.7

# Text-to-Speech
TTS_VOICE = "en-US-Standard-A"
TTS_SPEAKING_RATE = 1.0

# ======================================
# NEWS & MARKET DATA SOURCES
# ======================================

RSS_FEEDS = [
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("Reuters Business", "http://feeds.reuters.com/reuters/businessNews"),
    ("CNBC", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
]

# Web scraping
WEB_SCRAPE_TIMEOUT = 10  # seconds
WEB_SCRAPE_USER_AGENT = "APEX/1.0 (Financial Analysis Bot)"

# ======================================
# CRASH SIMULATOR
# ======================================

CRASH_SCENARIOS = {
    "2008_financial_crisis": {
        "name": "2008 Financial Crisis",
        "years": 2,
        "max_drawdown": -0.57,  # 57% max decline
        "recovery_years": 4
    },
    "2020_covid_crash": {
        "name": "2020 COVID Crash",
        "years": 0.5,
        "max_drawdown": -0.34,  # 34% max decline
        "recovery_years": 1
    },
    "dot_com_bubble": {
        "name": "Dot-Com Bubble",
        "years": 3,
        "max_drawdown": -0.78,  # 78% max decline
        "recovery_years": 7
    }
}

# Simulation acceleration
SIMULATION_SPEED_MULTIPLIER = 100  # 100x speed for demo

# ======================================
# LOGGING
# ======================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "logs/apex.log"

# ======================================
# DEBUG & DEVELOPMENT
# ======================================

DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
MOCK_DATA_MODE = os.getenv("MOCK_DATA_MODE", "false").lower() == "true"

# Enable/disable features
ENABLE_GPU_ACCELERATION = os.getenv("ENABLE_GPU", "true").lower() == "true"
ENABLE_LIVE_TRADING = False  # Always false in hackathon (paper trading only)
REQUIRE_USER_APPROVAL = True  # Always require approval for trades

# ======================================
# PERFORMANCE TUNING
# ======================================

# Connection pools
DB_POOL_SIZE = 10
REDIS_POOL_SIZE = 5

# Async concurrency
MAX_CONCURRENT_REQUESTS = 100
REQUEST_TIMEOUT = 30

# Cache settings
CACHE_TTL_DEFAULT = 300  # seconds
CACHE_TTL_MARKET_DATA = 300
CACHE_TTL_NEWS = 600
CACHE_TTL_USER_DATA = 3600

# ======================================
# FILE PATHS
# ======================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORICAL_DATA_DIR = os.path.join(DATA_DIR, "historical-markets")
MOCK_DATA_DIR = os.path.join(DATA_DIR, "mock-data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# ======================================
# ASSET CLASSES & TICKERS
# ======================================

ASSET_CLASSES = {
    "US Equity": ["SPY", "QQQ", "IWM", "VTI", "VOO"],
    "Bonds": ["TLT", "IEF", "AGG", "BND", "LQD"],
    "Commodities": ["GLD", "SLV", "DBC", "USO"],
    "International": ["VEA", "VWO", "EFA"],
    "Real Estate": ["VNQ", "IYR"],
}

# Benchmark tickers
BENCHMARK_TICKERS = ["SPY", "^VIX"]

# ======================================
# RISK PROFILES
# ======================================

RISK_PROFILES = {
    "conservative": {
        "equity_pct": 0.30,
        "bonds_pct": 0.60,
        "alternatives_pct": 0.10
    },
    "moderate": {
        "equity_pct": 0.60,
        "bonds_pct": 0.30,
        "alternatives_pct": 0.10
    },
    "aggressive": {
        "equity_pct": 0.80,
        "bonds_pct": 0.10,
        "alternatives_pct": 0.10
    }
}

# ======================================
# EXPLANATION LEVELS
# ======================================

class ExplanationLevel(str, Enum):
    """Levels of explanation detail."""
    BEGINNER = "beginner"  # ELI5 - Simple terms
    INTERMEDIATE = "intermediate"  # Some financial knowledge assumed
    ADVANCED = "advanced"  # Full technical detail

# ======================================
# MESSAGE TEMPLATES
# ======================================

SYSTEM_MESSAGES = {
    "war_room_started": "🎬 War Room initialized. All agent communications will appear here.",
    "orchestrator_started": "🚀 Orchestrator starting... Agents assembling for discussion.",
    "user_paused": "🛑 Agents paused. Waiting for your input.",
    "user_resumed": "▶️ Resuming agent analysis with your input incorporated.",
    "trade_approved": "✅ Trade approved and executed.",
    "trade_rejected": "❌ Trade rejected by user.",
}
