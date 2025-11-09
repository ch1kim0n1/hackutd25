.PHONY: help setup run smoke clean test lint

# Detect OS
ifeq ($(OS),Windows_NT)
    SCRIPT_EXT := .ps1
    SCRIPT_CMD := powershell -ExecutionPolicy Bypass -File
else
    SCRIPT_EXT := .sh
    SCRIPT_CMD := bash
endif

help: ## Show this help message
	@echo "APEX Demo - Available Commands"
	@echo "==============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Setup local environment (Python venv + Node modules)
	@echo "Running setup script..."
	@$(SCRIPT_CMD) scripts/setup$(SCRIPT_EXT)

run: ## Start backend + frontend (one command)
	@echo "Starting demo services..."
	@$(SCRIPT_CMD) scripts/run$(SCRIPT_EXT)

smoke: ## Run smoke tests (backend + frontend health checks)
	@echo "Running smoke tests..."
	@$(SCRIPT_CMD) scripts/smoke$(SCRIPT_EXT)

clean: ## Clean up generated files and caches
	@echo "Cleaning up..."
	@rm -rf src/backend/venv src/backend/__pycache__ src/backend/.pytest_cache
	@rm -rf client/front/node_modules client/front/dist client/front/.vite
	@rm -rf data/*.db
	@echo "✓ Cleanup complete"

test: ## Run backend tests
	@echo "Running tests..."
	@cd src/backend && source venv/bin/activate && pytest -v

lint: ## Run linters (backend + frontend)
	@echo "Running linters..."
	@cd src/backend && source venv/bin/activate && ruff check . && black --check .
	@cd client/front && npm run lint || true
