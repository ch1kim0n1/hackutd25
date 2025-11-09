# APEX: Multi-Agent Financial Operating System

[![CI Pipeline](https://github.com/your-org/apex/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/apex/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **Transparent Multi-Agent AI for Investment Management with Human-in-the-Loop Design**

APEX is a desktop AI financial operating system featuring **transparent multi-agent collaboration** for investment management, personal finance tracking, and real-time financial education. Unlike traditional robo-advisors that operate as black boxes, **APEX lets users observe and participate in AI agent discussions** via voice or text in a live "War Room" interface.

🎯 **The Problem**: 67% of Americans avoid investing due to lack of knowledge/confidence. Current solutions are either fully automated (opaque black boxes) or purely advisory (overwhelming information).

🚀 **The Solution**: APEX makes AI decision-making transparent and interactive, letting users learn from and influence agent discussions in real-time.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Architecture](#architecture)
- [Development Setup](#development-setup)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Demo Script](#demo-script)
- [Contributing](#contributing)
- [License](#license)

---

## Quick Start

### Prerequisites

- **Python 3.10+** (required)
- **Node.js 18+** (required)
- **PostgreSQL 14+** (optional, SQLite fallback available)
- **Redis 7+** (optional, demo works without it)

### Demo Mode (Recommended for First Look)

The easiest way to experience APEX is with our automated demo script:

```bash
# Windows
demo.bat

# OR manually with PowerShell
.\scripts\demo-setup.ps1
```

This will:
- ✅ Check your system for required tools
- ✅ Install Python and Node.js dependencies
- ✅ Start backend API server (port 8000)
- ✅ Start frontend dev server (port 5173)
- ✅ Open your browser to the demo
- ✅ Use SQLite database (no PostgreSQL required)
- ✅ Mock AI responses (no API keys needed)

### Full Development Setup

For development with real integrations:

```bash
# Clone the repository
git clone https://github.com/your-org/apex.git
cd apex

# Backend setup
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your OPENROUTER_API_KEY, ALPACA_API_KEY, etc.

# Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend setup (new terminal)
cd ../client/front
npm install
npm run dev

# Open APEX
# http://localhost:5173 (Frontend)
# http://localhost:8000/docs (API Docs)
```

# Visit http://localhost:5173
```

---

## Features

### 🤖 Multi-Agent Architecture

APEX employs **6 specialized AI agents** powered by NVIDIA Llama 3.1 Nemotron 70B:

| Agent | Role | Capabilities |
|-------|------|--------------|
| **Market Agent** 🔍 | Market Intelligence | News scraping, VIX tracking, sentiment analysis via Alpaca API |
| **Strategy Agent** 🧠 | Portfolio Optimization | Portfolio allocation, opportunity evaluation, parallel scenario planning |
| **Risk Agent** ⚠️ | Risk Management | Risk limits, Monte Carlo simulations, stress testing |
| **Executor Agent** ⚡ | Trade Execution | Alpaca API integration, order validation, error handling |
| **Explainer Agent** 💬 | Education & Translation | Plain English explanations, adaptive education (ELI5 to advanced) |
| **User Agent** 👤 | Human Participation | Voice/text input, decision override, approval workflows |

**🎯 Key Differentiator**: Unlike fully autonomous systems, APEX agents **pause when the user speaks**, incorporating human insights like *"I actually want lower risk here"* or *"You missed X important aspect of company Y"* into their decision-making.

### ✨ Core Features

#### Visual Agent War Room
- Live multi-agent conversation display
- Color-coded debate tracking
- Real-time consensus visualization
- WebSocket-powered updates

#### Voice Interaction
- Push-to-talk with instant transcription
- "Hold on" error correction mechanism
- Natural language command processing
- Voice-guided goal setting

#### Market Crash Simulator
- Time-compressed historical scenarios (2008, 2020)
- APEX vs buy-and-hold strategy comparison
- 100x speed simulation with GPU acceleration
- Visual performance attribution

#### Live Trading Integration
- Alpaca paper trading (safer default)
- Real-time order execution
- Position tracking & portfolio management
- Trade validation & risk checks

### 💰 Personal Finance Features

- **Plaid Integration**: Net worth tracking, cash flow analysis
- **AI Goal Planner**: Voice-guided financial goal setting with timeline projections
- **Smart Subscription Tracker**: Auto-detects recurring charges, identifies savings opportunities
- **Expense Categorization**: AI-powered categorization with peer benchmarking
- **Performance Dashboard**: Compare your returns vs S&P 500

### 📰 Market Intelligence

- Personalized news digest with portfolio impact assessment
- Top trending financial news with source links
- Search engine for stocks with RAG-powered analysis
- Historical event analysis (hover over time periods for agent insights)

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                   │
│  ┌───────────┐  ┌──────────┐  ┌─────────┐  ┌────────────────┐ │
│  │ Dashboard │  │ War Room │  │ Trading │  │ Personal       │ │
│  │           │  │ (Live)   │  │ View    │  │ Finance        │ │
│  └───────────┘  └──────────┘  └─────────┘  └────────────────┘ │
└───────────────────────────┬─────────────────────────────────────┘
                            │ WebSocket + REST
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                      │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐│
│  │ API Routes   │  │ Orchestrator  │  │ WebSocket Manager    ││
│  │ /api/v1/*    │  │ (Agent Coord) │  │ /ws/warroom          ││
│  └──────────────┘  └───────────────┘  └──────────────────────┘│
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    6 AI Agents                           │  │
│  │  Market │ Strategy │ Risk │ Executor │ Explainer │ User  │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │             Services & Adapters                          │  │
│  │  Alpaca │ Plaid │ RAG (ChromaDB) │ Voice │ News │ Auth   │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
        ┌──────────────┐        ┌──────────────┐
        │ PostgreSQL   │        │    Redis     │
        │ (Data Store) │        │ (Pub/Sub)    │
        └──────────────┘        └──────────────┘
                ▼
        ┌──────────────┐
        │  ChromaDB    │
        │ (Vector DB)  │
        └──────────────┘
```

### Tech Stack

**Backend**:
- FastAPI (async Python web framework)
- SQLAlchemy 2.0 (async ORM)
- Alembic (database migrations)
- Redis (pub/sub, caching)
- ChromaDB (vector store for RAG)
- PostgreSQL (primary database)

**Frontend**:
- React 18
- Vite 6 (build tool)
- TypeScript
- TailwindCSS 4
- HeroUI (component library)
- Recharts (data visualization)

**AI/ML**:
- OpenRouter API (NVIDIA Llama 3.1 Nemotron 70B)
- Anthropic Claude (optional)
- Sentence Transformers (embeddings)
- Faster Whisper (voice transcription)

**External APIs**:
- Alpaca Markets (trading)
- Plaid (banking/finance data)
- yFinance (market data)
- News RSS feeds

---

## Development Setup

### Backend Development

```bash
cd src/backend

# Install with development dependencies
make install-dev

# Or manually:
pip install -e ".[dev]"

# Optional: GPU support (requires CUDA 12.x)
pip install -r requirements-gpu.txt

# Optional: Voice features
pip install -r requirements-voice.txt

# Run linting and formatting
make lint       # Check code
make format     # Auto-fix code
make typecheck  # Run MyPy

# Run tests
make test                # All tests
make test-unit           # Unit tests only
make test-coverage       # With coverage report

# Database management
make db-upgrade          # Apply migrations
make db-migrate MSG="your message"  # Create new migration
make db-current          # Show current version

# Start development server
make run                 # Standard
make run-dev             # With debug logging

# Clean up generated files
make clean
```

### Frontend Development

```bash
cd client/front

# Install dependencies
npm install

# Start dev server (with hot reload)
npm run dev

# Build for production
npm run build

# Lint
npm run lint

# Type check
npm run type-check
```

### Environment Variables

Create a `.env` file in the project root:

```bash
# Copy template
cp .env.example .env
```

**Required Variables**:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://apex_user:apex_password@localhost:5432/apex_db

# Redis
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your_very_secure_secret_key_min_32_chars

# AI/LLM
OPENROUTER_API_KEY=your_openrouter_key_here

# Trading (Alpaca)
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key
ALPACA_PAPER_TRADING=true  # IMPORTANT: Use paper trading for safety
```

**Optional Variables**:
```bash
# Banking (Plaid)
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_ENABLED=false  # Uses mock data if false

# Features
ENABLE_GPU=false
VOICE_ENABLED=false
ENABLE_CRASH_SIMULATOR=true

# Environment
ENVIRONMENT=development
DEBUG=true
```

See `.env.example` for all available configuration options.

---

## Demo Script

The APEX demo script (`scripts/demo-setup.ps1`) automates the entire setup process for local development and demonstration:

### Demo Script Features

- 🔍 **System Check**: Validates Python, Node.js, and optional services (PostgreSQL, Redis)
- 📦 **Dependency Installation**: Automatically installs Python and Node.js packages
- 🗄️ **Database Setup**: Uses SQLite by default (PostgreSQL optional)
- 🚀 **Service Startup**: Starts backend and frontend servers
- 🌐 **Browser Launch**: Opens the application in your default browser
- 🧹 **Cleanup**: Removes temporary files and stops processes on exit

### Demo Script Usage

```powershell
# Start demo with all checks and setup
.\scripts\demo-setup.ps1

# Clean up previous demo and start fresh
.\scripts\demo-setup.ps1 -Clean

# Skip dependency installation (if already done)
.\scripts\demo-setup.ps1 -SkipBuild

# Run in headless mode (no interactive prompts)
.\scripts\demo-setup.ps1 -Headless
```

### Quick Demo Launcher

For Windows users, simply double-click `demo.bat` or run:

```cmd
demo.bat
```

### What the Demo Includes

The demo mode provides:

- ✅ **Mock AI Responses**: No API keys required
- ✅ **SQLite Database**: No PostgreSQL setup needed
- ✅ **Sample Data**: Pre-loaded with demo portfolios and market data
- ✅ **Limited Features**: Core functionality without external integrations
- ✅ **Auto-Configuration**: Environment variables set automatically

### Demo Limitations

- AI responses are simulated (static responses)
- Real-time market data is mocked
- Trading integration uses paper trading simulation
- Voice features are disabled
- Some advanced agent features are limited

---

## API Documentation

### Interactive API Docs

Once the backend is running, visit:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Key Endpoints

#### Health & Status

```bash
GET  /health              # Health check (200 if alive)
GET  /ready               # Readiness check (503 if not ready)
GET  /                    # Server info
GET  /api/status          # Orchestrator status
```

#### Authentication

```bash
POST /auth/login          # Login (returns JWT)
POST /auth/refresh        # Refresh token
POST /auth/logout         # Logout
GET  /auth/me             # Get current user
```

#### Orchestrator

```bash
POST /orchestrator/start  # Start agent discussion
POST /orchestrator/stop   # Stop agents
POST /orchestrator/pause  # Pause execution
POST /orchestrator/resume # Resume execution
POST /user-input          # Submit user input to agents
```

#### Trading & Portfolio

```bash
GET  /api/portfolio       # Get portfolio summary
GET  /api/account         # Get account details
GET  /api/positions       # Get current positions
GET  /api/orders          # Get order history
POST /api/orders          # Place new order
```

#### WebSocket

```
ws://localhost:8000/ws/warroom  # Real-time agent messages
```

---

## Testing

### Backend Tests

```bash
cd src/backend

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_market_agent.py

# Run specific test
pytest tests/unit/test_market_agent.py::test_agent_initialization

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# View coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

### Frontend Tests

```bash
cd client/front

# Run tests (when implemented)
npm test

# Run with coverage
npm run test:coverage
```

### CI Pipeline

The project uses GitHub Actions for automated testing. See `.github/workflows/ci.yml`.

**CI Checks**:
- ✅ Code linting (Ruff)
- ✅ Code formatting (Black)
- ✅ Type checking (MyPy)
- ✅ Unit tests
- ✅ Integration tests
- ✅ Docker build
- ✅ Frontend build
- ✅ Smoke tests

---

## Project Structure

```
apex/
├── .devcontainer/          # VS Code dev container config
├── .github/workflows/      # CI/CD pipelines
├── client/front/           # Frontend React app
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API clients
│   │   └── lib/            # Utilities
│   ├── package.json
│   └── vite.config.ts
├── src/backend/            # Backend Python app
│   ├── agents/             # AI agent implementations
│   ├── api/                # FastAPI route handlers
│   ├── core/               # Core config (settings.py)
│   ├── models/             # SQLAlchemy models
│   ├── services/           # Business logic & external integrations
│   ├── middleware/         # Auth, logging, etc.
│   ├── alembic/            # Database migrations
│   ├── tests/              # Test suite
│   ├── server.py           # Main FastAPI application
│   ├── orchestrator.py     # Agent coordination
│   ├── pyproject.toml      # Python project config
│   ├── Makefile            # Development commands
│   └── requirements.txt    # Python dependencies
├── data/                   # Data files (historical markets, mocks)
├── docs/                   # Documentation
├── docker-compose.yml      # Docker services
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── MIGRATION_NOTES.md      # Refactor migration guide
└── README.md               # This file
```

---

## Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes**
4. **Run quality checks**:
   ```bash
   cd src/backend
   make format    # Auto-format code
   make lint      # Check linting
   make typecheck # Type checking
   make test      # Run tests
   ```
5. **Commit your changes**: `git commit -m 'Add some feature'`
6. **Push to the branch**: `git push origin feature/your-feature`
7. **Open a Pull Request**

### Code Style

- **Python**: Black (100 char line length), Ruff linter, MyPy type hints
- **TypeScript**: ESLint, Prettier
- **Commits**: Conventional commits format preferred

### Testing Requirements

- All new features must include tests
- Maintain >80% test coverage for new code
- Integration tests for API endpoints
- Unit tests for business logic

---

## Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'core'"**
```bash
cd src/backend
pip install -e .
```

**"Alembic can't connect to database"**
```bash
# Ensure DATABASE_URL is set in .env
export DATABASE_URL=postgresql+asyncpg://apex_user:apex_password@localhost:5432/apex_db
alembic upgrade head
```

**"Frontend can't connect to backend"**
```bash
# Check backend is running on port 8000
curl http://localhost:8000/health

# Check VITE_API_BASE_URL in frontend .env
# Should be: VITE_API_BASE_URL=http://localhost:8000
```

**"Redis connection failed"**
```bash
# Check Redis is running
redis-cli ping  # Should return "PONG"

# Or start with Docker
docker-compose up redis -d
```

**"GPU dependencies fail to install"**
```bash
# Skip GPU dependencies if you don't have CUDA
pip install -e .  # Core only
# Don't run: pip install -r requirements-gpu.txt
```

For more issues, check [MIGRATION_NOTES.md](./MIGRATION_NOTES.md) or [open an issue](https://github.com/your-org/apex/issues).

---

## Roadmap

- [x] Phase 1: Core multi-agent system
- [x] Phase 2: Visual War Room interface
- [x] Phase 3: Voice interaction system
- [x] Phase 4: Market crash simulator
- [x] Phase 5: Plaid integration
- [ ] Phase 6: Mobile app (React Native)
- [ ] Phase 7: Advanced RAG with financial reports
- [ ] Phase 8: Social trading features
- [ ] Phase 9: Tax optimization agent
- [ ] Phase 10: Institutional client features

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **NVIDIA** for Llama 3.1 Nemotron 70B model via OpenRouter
- **Alpaca Markets** for paper trading API
- **Plaid** for financial data connectivity
- **HackUTD 25** for the hackathon opportunity

---

## Contact

- **GitHub**: [github.com/your-org/apex](https://github.com/your-org/apex)
- **Discord**: [Join our community](https://discord.gg/your-invite)
- **Email**: apex-support@example.com

---

**Made with ❤️ at HackUTD 25**

*Democratizing investment knowledge through transparent AI*
