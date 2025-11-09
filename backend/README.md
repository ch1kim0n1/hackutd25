# APEX Backend

Multi-Agent Financial Operating System - Backend API

## Overview

The APEX backend provides a REST API and WebSocket endpoints for the multi-agent financial operating system. It orchestrates AI agents (Market, Strategy, Risk, Executor, Explainer, User) to provide intelligent investment assistance.

## Architecture

```
backend/
├── app/                    # Main application code
│   ├── core/              # Configuration, logging, database
│   ├── api/               # API routes and WebSocket endpoints
│   │   └── routes/        # Organized route modules
│   ├── services/          # Business logic and agent orchestration
│   ├── adapters/          # External integrations (Alpaca, Plaid, RAG)
│   ├── models/            # Database models
│   └── workers/           # Background job processing
├── tests/                 # Test suite
├── alembic/               # Database migrations
├── requirements.in        # Dependency specifications
├── pyproject.toml         # Python project configuration
├── Makefile               # Development commands
└── README.md             # This file
```

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Redis 7+

### Setup
```bash
# Install dependencies
make setup

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run database migrations
make db-upgrade

# Start development server
make run
```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`.

## Development

### Available Commands
```bash
make setup          # Full development setup
make run           # Start development server
make test          # Run test suite
make lint          # Run linters
make format        # Format code
make typecheck     # Run type checking
make db-upgrade    # Apply database migrations
```

### Code Quality
- **Linting**: Ruff (fast Python linter)
- **Formatting**: Black + isort
- **Type Checking**: MyPy with strict settings
- **Testing**: pytest with coverage reporting

### Project Structure Guidelines
- **File size**: ≤400 LOC per file
- **Function complexity**: ≤50 LOC, cyclomatic complexity <10
- **Import organization**: isort with black profile
- **Type hints**: 100% coverage required

## API Documentation

### REST Endpoints
- `GET /health` - Health check
- `GET /ready` - Readiness check
- `POST /api/auth/login` - User authentication
- `POST /api/orchestrator/start` - Start agent discussion
- `GET /api/portfolio` - Get portfolio data
- `POST /api/trade` - Execute trades

### WebSocket
- `ws://localhost:8000/ws/warroom` - Real-time agent communication

## Environment Configuration

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/apex

# Redis
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET_KEY=your-secret-key-here
OPENROUTER_API_KEY=sk-or-v1-...

# Trading (Alpaca)
ALPACA_API_KEY=your-alpaca-key
ALPACA_SECRET_KEY=your-alpaca-secret

# Optional: Banking (Plaid)
PLAID_CLIENT_ID=your-plaid-client-id
PLAID_SECRET=your-plaid-secret
```

## Deployment

### Docker
```bash
docker build -t apex-backend .
docker run -p 8000:8000 --env-file .env apex-backend
```

### Production
- Use `make run-prod` for production deployment
- Configure reverse proxy (nginx/Caddy)
- Set up proper logging and monitoring
- Use environment-specific configuration

## Testing

### Run Tests
```bash
make test          # Run all tests
make test-unit     # Unit tests only
make test-cov      # With coverage report
```

### Test Structure
```
tests/
├── unit/          # Unit tests
├── integration/   # Integration tests
└── conftest.py    # Test configuration
```

## Contributing

1. Follow the established patterns and guidelines
2. Write tests for new functionality
3. Ensure all checks pass: `make check-all`
4. Update documentation as needed

## License

MIT License - see LICENSE file for details.
