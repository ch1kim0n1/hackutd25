# APEX Codebase Inventory

## Summary
- **Total Python files**: 88
- **Total TypeScript/React files**: 63
- **Total lines of code**: ~25,000+ (estimated)
- **Largest file**: `server.py` (2,554 LOC) ⚠️

## Architecture Overview

### Backend (Python/FastAPI)
- **Framework**: FastAPI with async endpoints
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Cache/Queue**: Redis
- **AI**: OpenRouter API (NVIDIA models)
- **Trading**: Alpaca API
- **Finance**: Plaid API (mock fallback)
- **Vector DB**: ChromaDB for RAG

### Frontend (TypeScript/React)
- **Framework**: React 18 + Vite
- **UI**: HeroUI components + TailwindCSS
- **State**: React hooks
- **API**: REST + WebSocket

### Agents (APEX Core)
- **Market Agent**: News + VIX analysis
- **Strategy Agent**: Portfolio allocation
- **Risk Agent**: Monte Carlo simulations
- **Executor Agent**: Trade execution
- **Explainer Agent**: Educational responses
- **User Agent**: Voice/text input

## Key Files Inventory

### Backend Core (High Priority)

| File | LOC | Purpose | Key Imports | Test Coverage | Issues |
|------|-----|---------|-------------|---------------|---------|
| `server.py` | 2,554 | **MONOLITH** - All API routes, WebSocket, DB init, services | FastAPI, orchestrator, all services | None | ⚠️ **MASSIVE FILE** - needs splitting |
| `orchestrator.py` | 1,200+ | Agent coordination & debate engine | AgentNetwork, Redis, asyncio | None | Complex async logic |
| `core/agent_network.py` | 800+ | Agent communication layer | Redis pub/sub | None | Core business logic |

### Agent Files

| File | LOC | Purpose | Key Dependencies |
|------|-----|---------|------------------|
| `agents/market_agent.py` | 440 | News + market data analysis | OpenRouter, yfinance, feedparser |
| `agents/strategy_agent.py` | 760 | Portfolio optimization | OpenRouter, market_agent |
| `agents/risk_agent.py` | 900 | Monte Carlo risk assessment | NumPy/CuPy, OpenRouter |
| `agents/executor_agent.py` | 300 | Trade execution | Alpaca API |
| `agents/explainer_agent.py` | 200 | Educational responses | OpenRouter |

### Service Layer (Consolidated)

| File | LOC | Purpose | Status |
|------|-----|---------|---------|
| `services/security.py` | 380 | Auth, JWT, encryption, rate limiting | ✅ Consolidated |
| `services/voice.py` | 730 | STT/TTS, commands, goal parsing | ✅ Consolidated |
| `services/rag/chroma_service.py` | 680 | Vector DB + RAG queries | ✅ Consolidated |
| `services/plaid_integration.py` | 320 | Real Plaid API integration | ✅ Active |
| `services/mock_plaid.py` | 260 | Mock financial data | ✅ Fallback |

### API Layer

| File | LOC | Purpose | Endpoints |
|------|-----|---------|-----------|
| `api/auth.py` | 150 | Authentication endpoints | /auth/login, /auth/refresh |
| `api/market.py` | 80 | Market data endpoints | /api/market |
| `api/portfolio.py` | 120 | Portfolio management | /api/portfolio, /api/accounts |
| `api/trades.py` | 90 | Trading endpoints | /api/trade |
| `api/strategy.py` | 60 | Strategy endpoints | /api/strategy |

### External Integrations

| File | LOC | Purpose | API |
|------|-----|---------|------|
| `integrations/alpaca_broker.py` | 250 | Alpaca trading API | Alpaca Markets |
| `engines/crash_scenario_engine.py` | 300 | Market crash simulation | Historical data |

### Database/Models

| File | LOC | Purpose | Tables |
|------|-----|---------|---------|
| `models/user.py` | 60 | User accounts | users |
| `models/portfolio.py` | 80 | Portfolio holdings | portfolios, positions |
| `models/trade.py` | 50 | Trade records | trades |
| `models/goal.py` | 70 | Financial goals | goals |

### Frontend Structure

| Directory | Files | Purpose |
|-----------|-------|---------|
| `components/` | 31 | UI components (charts, forms, agents) |
| `pages/` | 4 | Main app pages (dashboard, trading, etc.) |
| `services/` | 15 | API clients and utilities |
| `hooks/` | 1 | React hooks |
| `types/` | 1 | TypeScript definitions |

## Dependency Analysis

### Most Imported Modules
1. `datetime`: 56 imports (time handling)
2. `typing`: 51 imports (type hints)
3. `os`: 24 imports (environment)
4. `logging`: 18 imports (structured logging)
5. `asyncio`: 17 imports (async operations)
6. `services`: 16 imports (internal services)
7. `json`: 15 imports (data serialization)
8. `sqlalchemy`: 15 imports (ORM)

### Key Dependencies (from requirements.txt)
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `sqlalchemy`: Database ORM
- `redis`: Caching/pubsub
- `chromadb`: Vector database
- `openai`: AI API client
- `pandas`: Data analysis
- `numpy`: Numerical computing
- `yfinance`: Market data

## Issues Identified

### Critical Issues
1. **Monolithic server.py**: 2,554 LOC - violates single responsibility
2. **Missing tests**: No test coverage visible for core functionality
3. **Environment dependencies**: Requires OpenRouter API key to start
4. **No health checks**: Missing readiness/liveness probes

### Architecture Issues
1. **Tight coupling**: Server imports everything directly
2. **Mixed concerns**: Business logic mixed with API routing
3. **No contracts**: No OpenAPI spec or typed API clients
4. **Inconsistent error handling**: Mix of HTTP exceptions and custom responses

### Code Quality Issues
1. **Large files**: Multiple files >400 LOC
2. **Import cycles**: Potential circular dependencies
3. **Configuration scattering**: Settings spread across multiple files

## Next Steps (Phase 1)
1. Split server.py into focused modules
2. Create centralized settings management
3. Add proper project tooling (pyproject.toml, pre-commit)
4. Generate OpenAPI contract
5. Create typed FE client
