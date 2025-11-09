# APEX Quick Start Guide (Post-Refactor)

> **Status**: Refactored & Ready for Development ✅
>
> **Last Updated**: January 2025

This guide gets you up and running with the newly refactored APEX codebase in **under 10 minutes**.

---

## 🚀 Fastest Way to Start

### Option 1: Docker (Zero Setup - Recommended)

```bash
# 1. Clone the repo (if you haven't already)
git clone <your-repo-url>
cd hackutd25

# 2. Set up environment
cp .env.example .env
# Edit .env and add your API keys:
# - OPENROUTER_API_KEY (required)
# - ALPACA_API_KEY (required)
# - ALPACA_SECRET_KEY (required)

# 3. Start everything
docker-compose up

# Done! 🎉
# - Frontend: http://localhost:5173
# - Backend: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Option 2: Local Development (Full Control)

```bash
# 1. Start databases with Docker
docker-compose up postgres redis -d

# 2. Backend setup
cd src/backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -e ".[dev]"

# 3. Configure environment
cd ../..
cp .env.example .env
# Edit .env with your API keys

# 4. Run migrations
cd src/backend
alembic upgrade head

# 5. Start backend
make run
# Or: uvicorn server:app --reload

# 6. Frontend setup (new terminal)
cd client/front
npm install
npm run dev

# Done! 🎉
# - Frontend: http://localhost:5173
# - Backend: http://localhost:8000
```

---

## 🔑 Required Environment Variables

Add these to your `.env` file:

```bash
# Core
DATABASE_URL=postgresql+asyncpg://apex_user:apex_password@localhost:5432/apex_db
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your_secure_random_string_min_32_characters

# AI (Required)
OPENROUTER_API_KEY=sk-or-v1-xxxxx  # Get from https://openrouter.ai

# Trading (Required)
ALPACA_API_KEY=PKxxxxx             # Get from https://alpaca.markets
ALPACA_SECRET_KEY=xxxxx
ALPACA_PAPER_TRADING=true          # IMPORTANT: Keep as true for safety!

# Optional
PLAID_ENABLED=false                 # Set to true if you have Plaid credentials
ENABLE_GPU=false                    # Set to true if you have CUDA
VOICE_ENABLED=false                 # Set to true to enable voice features
```

---

## 🧪 Verify Your Setup

### Test Backend

```bash
# Health check
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}

# API docs
open http://localhost:8000/docs  # Mac
start http://localhost:8000/docs # Windows

# WebSocket (War Room)
# Open: ws://localhost:8000/ws/warroom in a WebSocket client
```

### Test Frontend

```bash
# Visit http://localhost:5173
# Should see the APEX landing page

# Check routes:
# - http://localhost:5173/dashboard
# - http://localhost:5173/market
# - http://localhost:5173/asset/AAPL
```

---

## 🛠️ Development Workflow

### Backend Development

```bash
cd src/backend

# Format code (auto-fix)
make format

# Lint code
make lint

# Type check
make typecheck

# Run tests
make test

# Run tests with coverage
make test-coverage

# Start dev server
make run

# All-in-one quality check
make quality

# See all commands
make help
```

### Frontend Development

```bash
cd client/front

# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Lint (if configured)
npm run lint

# Type check (if configured)
npm run type-check
```

### Database Management

```bash
cd src/backend

# Apply migrations
make db-upgrade

# Create new migration
make db-migrate MSG="add user preferences table"

# Check current version
make db-current

# See migration history
make db-history
```

---

## 📁 Project Structure (Post-Refactor)

```
hackutd25/
├── .devcontainer/              # VS Code dev container
├── .github/workflows/          # CI/CD (GitHub Actions)
├── client/front/               # ✅ Frontend (Vite + React + TS)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── lib/
│   └── package.json
├── src/backend/                # ✅ Backend (FastAPI + Python)
│   ├── agents/                 # 🔄 Agent files (FIXED - names now match classes)
│   ├── api/                    # API route handlers
│   ├── core/                   # ✨ NEW: Centralized settings
│   ├── models/                 # Database models
│   ├── services/               # Business logic & integrations
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Test suite
│   ├── server.py               # Main FastAPI app
│   ├── orchestrator.py         # Agent coordination
│   ├── pyproject.toml          # ✨ NEW: Python project config
│   ├── Makefile                # ✨ NEW: Developer commands
│   └── requirements*.txt       # ✨ SPLIT: Core, GPU, Voice
├── docker-compose.yml          # ✨ NEW: Full stack Docker
├── .env.example                # Environment template
├── .gitignore                  # ✨ NEW: Prevent secrets leak
├── README.md                   # ✨ UPDATED: Comprehensive docs
├── MIGRATION_NOTES.md          # ✨ NEW: Migration guide
├── REFACTOR_SUMMARY.md         # ✨ NEW: What was changed
└── QUICK_START.md              # This file
```

### Key Changes from Pre-Refactor

✅ **Fixed**: Agent file naming (market_agent.py now has MarketAgent class)
✅ **Fixed**: Startup scripts now work (correct paths)
✅ **Added**: Centralized settings in `core/settings.py`
✅ **Added**: Health endpoints (`/health`, `/ready`)
✅ **Added**: Docker & dev container support
✅ **Added**: CI/CD pipeline
✅ **Added**: Comprehensive documentation
✅ **Security**: No more hardcoded credentials

---

## 🐛 Common Issues & Fixes

### "Module 'core' not found"

```bash
cd src/backend
pip install -e .
```

### "Alembic can't connect to database"

```bash
# Make sure DATABASE_URL is in .env
echo $DATABASE_URL  # Should show the connection string

# Or set it manually
export DATABASE_URL="postgresql+asyncpg://apex_user:apex_password@localhost:5432/apex_db"
alembic upgrade head
```

### "Frontend can't connect to backend"

```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS origins in .env
# Should include: http://localhost:5173
```

### "Redis connection failed"

```bash
# Start Redis with Docker
docker-compose up redis -d

# Or check if Redis is running
redis-cli ping  # Should return "PONG"
```

### "GPU dependencies fail"

```bash
# Don't install GPU dependencies if you don't have CUDA
pip install -e .  # Core only
# Skip: pip install -r requirements-gpu.txt
```

---

## 🎯 What to Work On Next

### Recommended Next Steps

1. **Test the refactored code**: Make sure everything starts correctly
2. **Run the quality checks**: `make format && make lint && make test`
3. **Review MIGRATION_NOTES.md**: Understand what changed
4. **Start building features**: The infrastructure is ready!

### Ready for Development

The following are now **production-ready**:

✅ Health monitoring (`/health`, `/ready`)
✅ Centralized configuration (all settings in one place)
✅ Docker setup (one-command startup)
✅ CI/CD pipeline (automated testing on every commit)
✅ Development tools (Makefile, linting, formatting)
✅ Documentation (README, migration notes)

### Future Work (Deferred from Refactor)

These are **nice-to-haves** that can be done incrementally:

- [ ] Phase 3: Generate TypeScript API client from OpenAPI
- [ ] Phase 3: Add backend proxy for Alpaca (remove frontend direct calls)
- [ ] Phase 4: Consolidate duplicate services
- [ ] Phase 4: Reorganize agents into `app/services/agents/`
- [ ] Phase 5: Add more tests (contract tests, E2E with Playwright)

---

## 💡 Development Tips

### Use the Makefile

```bash
cd src/backend
make help  # See all available commands
```

The most useful ones:
- `make run` - Start dev server
- `make format` - Auto-format all code
- `make test` - Run tests
- `make db-upgrade` - Apply DB migrations
- `make clean` - Clean up generated files

### Use VS Code Dev Container

1. Install "Remote - Containers" extension
2. Press F1 → "Reopen in Container"
3. Everything is pre-configured!

### Use Docker for Quick Testing

```bash
# Start full stack
docker-compose up

# Start just databases
docker-compose up postgres redis -d

# View logs
docker-compose logs -f backend

# Stop everything
docker-compose down
```

---

## 📚 Additional Resources

- **Full Documentation**: [README.md](./README.md)
- **Migration Guide**: [MIGRATION_NOTES.md](./MIGRATION_NOTES.md)
- **Refactor Summary**: [REFACTOR_SUMMARY.md](./REFACTOR_SUMMARY.md)
- **API Docs** (when running): http://localhost:8000/docs
- **Original Project Brief**: See top of old README.md

---

## 🆘 Getting Help

### In this Repo

1. Check [README.md](./README.md) for detailed docs
2. Check [MIGRATION_NOTES.md](./MIGRATION_NOTES.md) for migration issues
3. Check [REFACTOR_SUMMARY.md](./REFACTOR_SUMMARY.md) for what changed

### External Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **React Docs**: https://react.dev
- **Vite Docs**: https://vitejs.dev
- **Docker Docs**: https://docs.docker.com

---

## ✅ Quick Checklist

Before you start developing, make sure:

- [ ] I have Python 3.10+ installed (or using Docker)
- [ ] I have Node.js 18+ installed (or using Docker)
- [ ] I have created `.env` from `.env.example`
- [ ] I have added my OPENROUTER_API_KEY to `.env`
- [ ] I have added my ALPACA_API_KEY and ALPACA_SECRET_KEY to `.env`
- [ ] I can access http://localhost:8000/health (backend)
- [ ] I can access http://localhost:5173 (frontend)
- [ ] I have read the MIGRATION_NOTES.md

---

**Happy Coding! 🚀**

*The refactor is complete, and the codebase is ready for development.*
