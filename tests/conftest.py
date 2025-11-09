"""
Pytest configuration and fixtures.
Provides common test setup, mocks, and utilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any
import os
import sys

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'backend'))


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_agent_network():
    """Provide mock agent network."""
    network = AsyncMock()
    network.publish = AsyncMock()
    network.subscribe = AsyncMock()
    network.initialize = AsyncMock()
    network.listen = AsyncMock()
    return network


@pytest.fixture
def mock_user():
    """Provide mock user object."""
    return {
        "id": "user_123",
        "username": "testuser",
        "email": "test@example.com",
        "created_at": datetime.now()
    }


@pytest.fixture
def mock_portfolio():
    """Provide mock portfolio."""
    return {
        "user_id": "user_123",
        "total_value": 100000,
        "cash": 20000,
        "positions": {
            "SPY": {"shares": 100, "avg_cost": 450.00, "value": 50000},
            "AAPL": {"shares": 50, "avg_cost": 150.00, "value": 7500},
            "TLT": {"shares": 50, "avg_cost": 80.00, "value": 4000}
        }
    }


@pytest.fixture
def mock_market_data():
    """Provide mock market data."""
    return {
        "timestamp": datetime.now().isoformat(),
        "vix": 15.5,
        "trend": "bullish",
        "sector_performance": {
            "Technology": 0.025,
            "Healthcare": 0.010,
            "Energy": -0.015
        },
        "top_gainers": [
            {"symbol": "NVDA", "change": 0.045},
            {"symbol": "MSFT", "change": 0.035}
        ],
        "top_losers": [
            {"symbol": "XOM", "change": -0.020}
        ]
    }


@pytest.fixture
def mock_strategy():
    """Provide mock strategy."""
    return {
        "strategy_id": "strategy_123",
        "type": "rebalancing",
        "allocations": {
            "SPY": 0.60,
            "TLT": 0.30,
            "GLD": 0.10
        },
        "trades": [
            {"symbol": "SPY", "qty": 50, "side": "buy", "price": 450.00},
            {"symbol": "AAPL", "qty": 25, "side": "sell", "price": 150.00}
        ]
    }


@pytest.fixture
def mock_trade_execution():
    """Provide mock trade execution result."""
    return {
        "order_id": "order_12345",
        "symbol": "SPY",
        "qty": 50,
        "side": "buy",
        "status": "filled",
        "filled_qty": 50,
        "avg_fill_price": 450.25,
        "commission": 0,
        "execution_time": datetime.now().isoformat()
    }


@pytest.fixture
def mock_alpaca_client():
    """Provide mock Alpaca trading client."""
    client = AsyncMock()
    client.submit_order = AsyncMock()
    client.get_positions = AsyncMock(return_value=[])
    client.get_account = AsyncMock(return_value={
        "cash": 20000,
        "portfolio_value": 100000,
        "buying_power": 80000
    })
    return client


@pytest.fixture
def mock_openrouter_client():
    """Provide mock OpenRouter LLM client."""
    client = Mock()
    client.chat.completions.create = Mock(return_value=Mock(
        choices=[Mock(message=Mock(content='{"response": "test"}'))]
    ))
    return client


@pytest.fixture
def mock_database():
    """Provide mock database."""
    db = AsyncMock()
    db.query = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def env_vars():
    """Provide environment variables."""
    return {
        "JWT_SECRET_KEY": "test_secret_key_123",
        "ALPACA_API_KEY": "test_alpaca_key",
        "ALPACA_SECRET_KEY": "test_alpaca_secret",
        "OPENROUTER_API_KEY": "test_openrouter_key",
        "DATABASE_URL": "sqlite:///test.db",
        "LOG_LEVEL": "DEBUG"
    }


# Test markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async (deselect with '-m \"not asyncio\"')"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )


# Logging configuration
@pytest.fixture
def caplog_clear(caplog):
    """Clear logs before test."""
    caplog.clear()
    return caplog


# Mocking utilities
class MockGenerator:
    """Utility for generating mock objects."""
    
    @staticmethod
    def user(user_id: str = "user_123", **kwargs) -> Dict[str, Any]:
        """Generate mock user."""
        user = {
            "id": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "created_at": datetime.now()
        }
        user.update(kwargs)
        return user
    
    @staticmethod
    def portfolio(user_id: str = "user_123", **kwargs) -> Dict[str, Any]:
        """Generate mock portfolio."""
        portfolio = {
            "user_id": user_id,
            "total_value": 100000,
            "cash": 20000,
            "positions": {}
        }
        portfolio.update(kwargs)
        return portfolio
    
    @staticmethod
    def trade(symbol: str = "SPY", qty: int = 100, **kwargs) -> Dict[str, Any]:
        """Generate mock trade."""
        trade = {
            "symbol": symbol,
            "qty": qty,
            "side": "buy",
            "price": 450.00,
            "status": "pending"
        }
        trade.update(kwargs)
        return trade


@pytest.fixture
def mock_generator():
    """Provide mock generator."""
    return MockGenerator()


# Test context managers
@pytest.fixture
def mock_env_vars(monkeypatch, env_vars):
    """Mock environment variables."""
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


@pytest.fixture
def mock_api_errors():
    """Provide mock API errors."""
    from fastapi import HTTPException, status
    
    return {
        "unauthorized": HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        ),
        "forbidden": HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        ),
        "not_found": HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        ),
        "bad_request": HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad request"
        )
    }


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
