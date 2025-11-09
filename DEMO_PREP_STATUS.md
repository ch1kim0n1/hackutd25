# APEX Demo Preparation Status

**Target**: Single-command local demo (no Docker)
**Status**: Phase A Complete, Phases B-F In Progress

---

## ✅ Phase A: Environment & One-Command Run (COMPLETE)

### Created Files

1. **`.env.example`** (root) - Unified environment configuration
   - All vars prefixed with `BACKEND_` or `VITE_`
   - Mock/disabled defaults for all external APIs
   - SQLite database for zero-config demo

2. **`scripts/setup.ps1`** - Windows PowerShell setup
   - Python 3.10+ version check
   - Node.js 18+ version check
   - Creates venv + installs deps
   - Creates .env from template
   - Runs migrations

3. **`scripts/setup.sh`** - macOS/Linux Bash setup
   - Same functionality as PowerShell version

4. **`scripts/run.ps1`** - Windows start script
   - Starts backend on :8000
   - Starts frontend on :5173
   - Shows all URLs
   - Ctrl+C cleanup

5. **`scripts/run.sh`** - macOS/Linux start script
   - Same functionality as PowerShell version

6. **`Makefile`** (root) - Cross-platform orchestration
   - `make setup` - Run setup script
   - `make run` - Start both services
   - `make smoke` - Run smoke tests (TBD)
   - `make clean` - Clean all artifacts

7. **`.nvmrc`** - Node version pinning (18.18.0)

8. **`src/backend/core/settings.py`** - Updated
   - Changed `env_prefix = "BACKEND_"`
   - Loads `.env` from root directory
   - All settings now use BACKEND_ prefix

### How to Use

```bash
# Windows
.\scripts\setup.ps1
.\scripts\run.ps1

# macOS/Linux
chmod +x scripts/*.sh
./scripts/setup.sh
./scripts/run.sh

# Or use Makefile (cross-platform)
make setup
make run
```

---

## 🚧 Phase B: Data, Migrations, and Mocks (IN PROGRESS)

### Created Files

1. **`scripts/dev_seed.py`** - Demo data seeder
   - Creates demo user (demo@apex.local / demo123)
   - Seeds portfolio with 4 positions (SPY, AAPL, MSFT, NVDA)
   - Adds 3 historical trades
   - Creates 3 financial goals
   - Run with: `python scripts/dev_seed.py`

### TODO

- [ ] Create mock Alpaca adapter (`src/backend/services/mock_alpaca.py`)
- [ ] Create mock OpenRouter adapter (`src/backend/services/mock_llm.py`)
- [ ] Update settings to auto-detect mock mode when API keys = "mock_disabled"
- [ ] Add `make seed` command to run dev_seed.py
- [ ] Test SQLite migrations work correctly

---

## ⏳ Phase C: Ruthless Prune & Slim Build (PENDING)

### Files to Remove/Archive

**Dead Code**:
- `src/backend/api/app.py` (duplicate API entry point)
- `src/backend/services/plaid_integration.py` (use plaid_service.py)
- `src/backend/services/news_search.py` (use news_aggregator.py)
- `src/backend/services/alpaca.py` (use integrations/alpaca_broker.py)
- `src/backend/utils/config.py` (empty)
- `src/backend/utils/logger.py` (empty)

**Old Docs**:
- Move `MIGRATION_NOTES.md` → `archive/`
- Move `REFACTOR_SUMMARY.md` → `archive/`
- Move `STATUS.md` → `archive/`
- Keep only: `README.md`, `DEMO_GUIDE.md`, `RUNBOOK.md`

**Standalone Scripts**:
- Move `orchestration_demo_live.py` → `archive/demos/`
- Move `orchestration_tests_standalone.py` → `archive/demos/`

**Duplicate Directories**:
- Remove `frontend/` (use `client/front/`)
- Remove `electron/` at root (use `client/electron/`)

### TODO

- [ ] Run `make clean` to remove caches
- [ ] Delete/archive files listed above
- [ ] Run linters and fix all errors
- [ ] Remove all TODO/WIP comments
- [ ] Create `archive/` directory for old docs

---

## ⏳ Phase D: Demo Script & Smoke Tests (PENDING)

### Files to Create

1. **`client/front/src/pages/Demo.tsx`** - Demo page
   - Simple UI showing FE ⇄ BE integration
   - "Run Demo" button that calls:
     - `GET /health` (backend health)
     - `GET /api/portfolio` (real data)
     - Shows success/error states
   - "Replay" button to reset and rerun

2. **`scripts/smoke.ps1`** / **`scripts/smoke.sh`** - Smoke tests
   - Backend: `curl http://localhost:8000/health`
   - Backend: `curl http://localhost:8000/api/status`
   - Frontend: Playwright test (load /demo, wait for success)
   - Screenshot to `artifacts/smoke.png`

3. **`DEMO_GUIDE.md`** - 2-3 minute demo script
   - Start services: `make run`
   - Navigate to: http://localhost:5173/demo
   - Click "Run Demo"
   - Show success states
   - Show error handling (optional)

### TODO

- [ ] Create Demo.tsx page
- [ ] Add /demo route to React Router
- [ ] Create smoke test scripts
- [ ] Install Playwright for E2E tests
- [ ] Create artifacts/ directory
- [ ] Write DEMO_GUIDE.md

---

## ⏳ Phase E: One-Page README & Runbook (PENDING)

### Files to Create

1. **`README.md`** (replace current) - Short & sharp
   - What is APEX (2-3 lines)
   - Prerequisites (Python 3.10+, Node 18+)
   - Quick start (3 commands)
   - Demo URL
   - Troubleshooting (5-8 bullets)

2. **`RUNBOOK.md`** - Detailed operations guide
   - Fresh machine setup
   - How to switch live ↔ mock adapters
   - How to reseed data
   - How to reset database
   - Known limitations
   - Common issues & fixes

### TODO

- [ ] Write concise README.md
- [ ] Write comprehensive RUNBOOK.md
- [ ] Update .env.example with clear comments
- [ ] Test instructions on clean machine

---

## ⏳ Phase F: Quality Gates (PENDING)

### Checklist

- [ ] `make setup` works on macOS/Windows/Linux
- [ ] `make run` boots both services
- [ ] Frontend loads at http://localhost:5173
- [ ] Backend responds at http://localhost:8000/health
- [ ] Demo page works at http://localhost:5173/demo
- [ ] `make smoke` passes all tests
- [ ] No unused dependencies
- [ ] No dead files
- [ ] No commented-out code blocks
- [ ] No TODO comments left
- [ ] `make lint` passes
- [ ] `make test` passes
- [ ] Repo size reasonable (<50MB)
- [ ] Docs are minimal and accurate

---

## Current Working State

**What Works**:
✅ One-command setup (`make setup`)
✅ Unified .env configuration
✅ Cross-platform setup scripts (Windows/macOS/Linux)
✅ Backend settings use BACKEND_ prefix
✅ Node version pinned (.nvmrc)
✅ Demo data seeder script

**What's Next**:
🚧 Create mock adapters for external APIs
🚧 Create demo page in frontend
🚧 Create smoke test scripts
🚧 Remove dead code and docs
🚧 Write final README and RUNBOOK

---

## Estimated Time to Complete

- Phase B (Mocks): 1-2 hours
- Phase C (Prune): 1 hour
- Phase D (Demo): 2-3 hours
- Phase E (Docs): 1 hour
- Phase F (QA): 1 hour

**Total**: 6-8 hours remaining

---

## How to Continue

1. **Complete Phase B**: Create mock adapters and test SQLite
2. **Execute Phase C**: Delete all unused files (see list above)
3. **Build Phase D**: Create Demo.tsx and smoke tests
4. **Write Phase E**: Create final README.md and RUNBOOK.md
5. **Verify Phase F**: Test on fresh machine, fix all quality gates

---

**Next Command to Run**:
```bash
make setup  # Test the setup process
```

Then check if backend starts with SQLite:
```bash
cd src/backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn server:app --reload
```
