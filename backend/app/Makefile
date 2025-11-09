.PHONY: help setup install install-dev install-gpu install-voice lint format typecheck test test-unit test-integration test-coverage run run-dev db-upgrade db-downgrade db-migrate clean docker-build docker-up docker-down

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python
PIP := pip
PYTEST := pytest
UVICORN := uvicorn
ALEMBIC := alembic
BLACK := black
RUFF := ruff
ISORT := isort
MYPY := mypy

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(CYAN)APEX Backend - Makefile Commands$(NC)"
	@echo "$(CYAN)================================$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ============================================================================
# Setup & Installation
# ============================================================================

setup: ## Full setup: create venv, install deps, setup pre-commit
	@echo "$(CYAN)Setting up development environment...$(NC)"
	$(PYTHON) -m venv venv
	@echo "$(GREEN)✓ Virtual environment created$(NC)"
	@echo "$(YELLOW)Activate with: venv\\Scripts\\activate (Windows) or source venv/bin/activate (Unix)$(NC)"
	@echo "$(YELLOW)Then run: make install-dev$(NC)"

install: ## Install core dependencies
	@echo "$(CYAN)Installing core dependencies...$(NC)"
	$(PIP) install -e .
	@echo "$(GREEN)✓ Core dependencies installed$(NC)"

install-dev: ## Install development dependencies
	@echo "$(CYAN)Installing development dependencies...$(NC)"
	$(PIP) install -e ".[dev]"
	@echo "$(GREEN)✓ Development dependencies installed$(NC)"

install-gpu: ## Install GPU dependencies (CUDA required)
	@echo "$(CYAN)Installing GPU dependencies...$(NC)"
	$(PIP) install -e ".[gpu]"
	@echo "$(GREEN)✓ GPU dependencies installed$(NC)"

install-voice: ## Install voice processing dependencies
	@echo "$(CYAN)Installing voice dependencies...$(NC)"
	$(PIP) install -e ".[voice]"
	@echo "$(GREEN)✓ Voice dependencies installed$(NC)"

install-all: install install-dev install-gpu install-voice ## Install all dependencies

# ============================================================================
# Code Quality
# ============================================================================

lint: ## Run linters (ruff)
	@echo "$(CYAN)Running linter...$(NC)"
	$(RUFF) check .
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: ## Format code with black and isort
	@echo "$(CYAN)Formatting code...$(NC)"
	$(BLACK) .
	$(ISORT) .
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check code formatting without modifying
	@echo "$(CYAN)Checking code format...$(NC)"
	$(BLACK) --check .
	$(ISORT) --check-only .
	@echo "$(GREEN)✓ Format check complete$(NC)"

typecheck: ## Run type checker (mypy)
	@echo "$(CYAN)Running type checker...$(NC)"
	$(MYPY) .
	@echo "$(GREEN)✓ Type checking complete$(NC)"

fix: format lint ## Auto-fix code issues (format + lint)
	@echo "$(GREEN)✓ All fixes applied$(NC)"

quality: format-check lint typecheck ## Run all quality checks (CI mode)
	@echo "$(GREEN)✓ All quality checks passed$(NC)"

# ============================================================================
# Testing
# ============================================================================

test: ## Run all tests
	@echo "$(CYAN)Running tests...$(NC)"
	$(PYTEST) -v
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-unit: ## Run unit tests only
	@echo "$(CYAN)Running unit tests...$(NC)"
	$(PYTEST) -v -m "unit or not integration"
	@echo "$(GREEN)✓ Unit tests complete$(NC)"

test-integration: ## Run integration tests only
	@echo "$(CYAN)Running integration tests...$(NC)"
	$(PYTEST) -v -m integration
	@echo "$(GREEN)✓ Integration tests complete$(NC)"

test-coverage: ## Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	$(PYTEST) --cov=. --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Coverage report generated at htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode
	$(PYTEST) -v -f

test-fast: ## Run tests excluding slow tests
	$(PYTEST) -v -m "not slow"

# ============================================================================
# Development Server
# ============================================================================

run: ## Run development server
	@echo "$(CYAN)Starting APEX Backend...$(NC)"
	@echo "$(YELLOW)Server will be available at http://localhost:8000$(NC)"
	@echo "$(YELLOW)API docs at http://localhost:8000/docs$(NC)"
	$(UVICORN) server:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run production server (no reload)
	@echo "$(CYAN)Starting APEX Backend (production mode)...$(NC)"
	$(UVICORN) server:app --host 0.0.0.0 --port 8000 --workers 4

run-dev: ## Run with debug logging
	@echo "$(CYAN)Starting APEX Backend (debug mode)...$(NC)"
	DEBUG=1 LOG_LEVEL=DEBUG $(UVICORN) server:app --reload --host 0.0.0.0 --port 8000

# ============================================================================
# Database Management
# ============================================================================

db-upgrade: ## Apply database migrations
	@echo "$(CYAN)Applying database migrations...$(NC)"
	$(ALEMBIC) upgrade head
	@echo "$(GREEN)✓ Database upgraded$(NC)"

db-downgrade: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	$(ALEMBIC) downgrade -1
	@echo "$(GREEN)✓ Database downgraded$(NC)"

db-migrate: ## Create new migration (usage: make db-migrate MSG="description")
	@echo "$(CYAN)Creating new migration...$(NC)"
	$(ALEMBIC) revision --autogenerate -m "$(MSG)"
	@echo "$(GREEN)✓ Migration created$(NC)"

db-history: ## Show migration history
	$(ALEMBIC) history

db-current: ## Show current migration
	$(ALEMBIC) current

db-reset: ## Reset database (WARNING: destroys data)
	@echo "$(RED)WARNING: This will destroy all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(ALEMBIC) downgrade base; \
		$(ALEMBIC) upgrade head; \
		echo "$(GREEN)✓ Database reset$(NC)"; \
	fi

# ============================================================================
# Docker
# ============================================================================

docker-build: ## Build Docker image
	@echo "$(CYAN)Building Docker image...$(NC)"
	docker build -t apex-backend:latest .
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-up: ## Start Docker containers
	@echo "$(CYAN)Starting Docker containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Containers started$(NC)"

docker-down: ## Stop Docker containers
	@echo "$(CYAN)Stopping Docker containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Containers stopped$(NC)"

docker-logs: ## Show Docker logs
	docker-compose logs -f

docker-shell: ## Open shell in backend container
	docker-compose exec backend /bin/bash

# ============================================================================
# Utilities
# ============================================================================

clean: ## Clean up generated files
	@echo "$(CYAN)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

deps-update: ## Update dependencies
	@echo "$(CYAN)Updating dependencies...$(NC)"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e ".[dev]" --upgrade
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

deps-list: ## List installed dependencies
	$(PIP) list

env-check: ## Check environment variables
	@echo "$(CYAN)Checking environment configuration...$(NC)"
	@$(PYTHON) -c "from core.settings import settings, validate_settings; validate_settings(); print('✓ Configuration valid')" || echo "$(RED)✗ Configuration invalid$(NC)"

seed-data: ## Seed database with test data
	@echo "$(CYAN)Seeding database...$(NC)"
	$(PYTHON) -c "from services.seed_data import seed_test_data; import asyncio; asyncio.run(seed_test_data())"
	@echo "$(GREEN)✓ Database seeded$(NC)"

shell: ## Start Python interactive shell with app context
	@echo "$(CYAN)Starting Python shell...$(NC)"
	$(PYTHON) -i -c "from core.settings import settings; from services.postgres_db import Base; print('Settings and Base imported')"

# ============================================================================
# CI/CD Helpers
# ============================================================================

ci: quality test ## Run full CI pipeline (lint, typecheck, test)
	@echo "$(GREEN)✓ CI pipeline complete$(NC)"

ci-quick: lint test-fast ## Run quick CI checks
	@echo "$(GREEN)✓ Quick CI complete$(NC)"

pre-commit: format lint ## Run pre-commit checks
	@echo "$(GREEN)✓ Pre-commit checks passed$(NC)"
