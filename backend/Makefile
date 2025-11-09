# =============================================================================
# APEX Backend - Development Makefile
# =============================================================================

.PHONY: help setup install install-dev lint lint-fix typecheck test test-cov test-unit test-integration run run-dev clean build docker-build docker-run migrate migrate-create db-upgrade db-downgrade db-current shell format check-all ci

# Default target
help: ## Show this help message
	@echo "APEX Backend Development Commands"
	@echo "================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# Setup & Installation
# =============================================================================

setup: ## Full development setup (install deps, setup pre-commit, create env file)
	@echo "🚀 Setting up APEX Backend development environment..."
	@make install-dev
	@make install-pre-commit
	@make create-env-example
	@echo "✅ Setup complete! Run 'make run' to start the server."

install: ## Install production dependencies
	@echo "📦 Installing production dependencies..."
	pip install -e .

install-dev: ## Install development dependencies
	@echo "📦 Installing development dependencies..."
	pip install -e ".[dev]"

install-pre-commit: ## Install pre-commit hooks
	@echo "🔧 Installing pre-commit hooks..."
	pre-commit install --install-hooks

create-env-example: ## Create .env.example from settings
	@echo "📝 Creating .env.example..."
	python -c "
	from app.core.settings import Settings
	import json
	settings = Settings()
	# Get all fields from the model
	fields = {}
	for field_name, field_info in settings.__fields__.items():
		default = getattr(settings, field_name, None)
		description = field_info.field_info.description or ''
		if isinstance(default, (list, dict)):
			default = json.dumps(default)
		elif isinstance(default, bool):
			default = str(default).lower()
		else:
			default = str(default)
		fields[field_name] = f'# {description}\n{field_name}={default}'
	# Write to .env.example
	with open('.env.example', 'w') as f:
		f.write('# APEX Backend Environment Configuration\n')
		f.write('# Copy this file to .env and update values\n\n')
		for field_name, content in fields.items():
			f.write(f'{content}\n\n')
	"

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linting (ruff)
	@echo "🔍 Running linter..."
	ruff check app/

lint-fix: ## Auto-fix linting issues
	@echo "🔧 Auto-fixing linting issues..."
	ruff check --fix app/

format: ## Format code (black + isort)
	@echo "💅 Formatting code..."
	black app/
	isort app/

typecheck: ## Run type checking (mypy)
	@echo "🔍 Running type checker..."
	mypy app/

check-all: ## Run all quality checks
	@echo "🔍 Running all quality checks..."
	@make format
	@make lint
	@make typecheck
	@echo "✅ All checks passed!"

fix: ## Auto-fix all auto-fixable issues
	@echo "🔧 Auto-fixing all issues..."
	@make format
	@make lint-fix

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "🧪 Running all tests..."
	pytest

test-cov: ## Run tests with coverage
	@echo "🧪 Running tests with coverage..."
	pytest --cov=app --cov-report=html --cov-report=term-missing

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	pytest -m "not integration and not slow"

test-integration: ## Run integration tests only
	@echo "🧪 Running integration tests..."
	pytest -m integration

test-slow: ## Run slow tests
	@echo "🧪 Running slow tests..."
	pytest -m slow

# =============================================================================
# Running
# =============================================================================

run: ## Run the FastAPI server
	@echo "🚀 Starting FastAPI server..."
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-dev: ## Run server with debug logging
	@echo "🚀 Starting FastAPI server (debug mode)..."
	APP_ENV=development uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

run-prod: ## Run server in production mode
	@echo "🚀 Starting FastAPI server (production)..."
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

shell: ## Start Python shell with app context
	@echo "🐍 Starting Python shell..."
	python -c "
	import IPython
	from app.core.settings import settings
	print('APEX Backend Shell')
	print('Settings loaded:', settings.APP_NAME)
	print('Environment:', settings.ENVIRONMENT)
	IPython.embed()
	"

# =============================================================================
# Database
# =============================================================================

migrate: ## Create new database migration
	@echo "🗃️ Creating new migration..."
	@if [ -z "$(MSG)" ]; then \
		echo "Usage: make migrate MSG='your migration message'"; \
		exit 1; \
	fi
	alembic revision --autogenerate -m "$(MSG)"

db-upgrade: ## Upgrade database to latest migration
	@echo "⬆️ Upgrading database..."
	alembic upgrade head

db-downgrade: ## Downgrade database by one revision
	@echo "⬇️ Downgrading database..."
	alembic downgrade -1

db-current: ## Show current database revision
	@echo "📍 Current database revision:"
	alembic current

db-reset: ## Reset database (WARNING: destroys data!)
	@echo "💥 Resetting database (this will destroy all data!)..."
	@echo "Waiting 5 seconds... Press Ctrl+C to cancel"
	@sleep 5
	alembic downgrade base
	alembic upgrade head

# =============================================================================
# Docker
# =============================================================================

docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t apex-backend .

docker-run: ## Run Docker container
	@echo "🐳 Running Docker container..."
	docker run -p 8000:8000 --env-file .env apex-backend

docker-dev: ## Run Docker container in development mode
	@echo "🐳 Running Docker container (dev mode)..."
	docker run -p 8000:8000 -v $(PWD):/app --env-file .env apex-backend

# =============================================================================
# Maintenance
# =============================================================================

clean: ## Clean up generated files
	@echo "🧹 Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -rf dist/ build/

clean-all: clean ## Clean everything including dependencies
	@echo "🧹 Cleaning everything..."
	rm -rf .venv/
	rm -rf node_modules/

# =============================================================================
# CI/CD
# =============================================================================

ci: ## Run CI pipeline locally
	@echo "🔄 Running CI pipeline..."
	@make check-all
	@make test-cov
	@make build
	@echo "✅ CI pipeline passed!"

# =============================================================================
# Utilities
# =============================================================================

deps: ## Show dependency tree
	@echo "📦 Dependency tree:"
	pipdeptree

deps-outdated: ## Show outdated dependencies
	@echo "📦 Outdated dependencies:"
	pip list --outdated

deps-update: ## Update dependencies
	@echo "📦 Updating dependencies..."
	pip install --upgrade -e ".[dev]"

# =============================================================================
# Development Helpers
# =============================================================================

seed-db: ## Seed database with test data
	@echo "🌱 Seeding database..."
	python -c "from app.services.seed_data import seed_test_data; import asyncio; asyncio.run(seed_test_data())"

validate-config: ## Validate configuration
	@echo "⚙️ Validating configuration..."
	python -c "from app.core.settings import validate_settings; validate_settings(); print('✅ Configuration is valid')"

logs: ## Show recent application logs
	@echo "📋 Recent logs:"
	tail -f logs/app.log 2>/dev/null || echo "No log file found. Logs are written to stdout in development."

# =============================================================================
# Build & Distribution
# =============================================================================

build: ## Build distribution packages
	@echo "📦 Building distribution..."
	python -m build

publish-test: ## Publish to TestPyPI
	@echo "📤 Publishing to TestPyPI..."
	python -m twine upload --repository testpypi dist/*

publish: ## Publish to PyPI
	@echo "📤 Publishing to PyPI..."
	python -m twine upload dist/*

# =============================================================================
# Environment Info
# =============================================================================

info: ## Show environment information
	@echo "ℹ️ Environment Information:"
	@echo "Python: $$(python --version)"
	@echo "Pip: $$(pip --version)"
	@echo "Project: $$(python -c 'from app.core.settings import settings; print(settings.APP_NAME, settings.APP_VERSION)')"
	@echo "Environment: $$(python -c 'from app.core.settings import settings; print(settings.ENVIRONMENT)')"
