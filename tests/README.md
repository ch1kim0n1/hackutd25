# Unit and Integration Tests for APEX

Comprehensive test suite for the APEX multi-agent financial system.

## Test Structure

```
tests/
├── unit/                          # Unit tests for individual components
│   ├── test_base_agent.py         # BaseAgent class tests
│   ├── test_auth_api.py           # Authentication endpoints
│   ├── test_market_agent.py       # Market Agent functionality
│   ├── test_risk_agent.py         # Risk Agent & Monte Carlo simulations
│   ├── test_strategy_agent.py     # Strategy Agent & allocations
│   ├── test_executor_agent.py     # Executor Agent & trading
│   ├── test_api_endpoints.py      # FastAPI endpoint tests
│   └── __init__.py
├── integration/                   # Integration tests
│   ├── test_agent_integration.py  # Multi-agent workflows
│   ├── test_workflows.py          # End-to-end scenarios
│   └── __init__.py
├── conftest.py                    # Shared fixtures and configuration
└── README.md                       # This file
```

## Test Coverage

### Unit Tests

#### 1. **Base Agent Tests** (`test_base_agent.py`)
- Agent initialization
- Logging configuration
- Performance tracking
- Communication patterns
- Model configuration

#### 2. **Authentication Tests** (`test_auth_api.py`)
- User login/logout
- JWT token creation and validation
- Token refresh mechanism
- Token revocation/blacklist
- Password hashing and verification
- Protected endpoint access

#### 3. **Market Agent Tests** (`test_market_agent.py`)
- Market data scanning
- News aggregation from multiple sources
- Sentiment analysis
- Volatility tracking (VIX)
- Alert generation
- Web scraping
- Data caching

#### 4. **Risk Agent Tests** (`test_risk_agent.py`)
- Monte Carlo simulations
- Value at Risk (VaR) calculations
- Expected Shortfall (CVaR)
- Stress testing
- Risk constraint validation
- Strategy approval/rejection
- GPU acceleration
- Correlation analysis

#### 5. **Strategy Agent Tests** (`test_strategy_agent.py`)
- Portfolio allocation generation
- Trade recommendations
- Portfolio rebalancing
- Tax loss harvesting
- Risk-adjusted strategies
- Goal alignment
- Market condition adaptation
- Sector rotation
- Momentum strategies
- Value strategies

#### 6. **Executor Agent Tests** (`test_executor_agent.py`)
- Order validation
- Trade execution
- Paper trading mode
- Order tracking and status
- Partial fills
- Order cancellation
- Price slippage detection
- Commission calculations
- Error recovery

#### 7. **API Endpoints Tests** (`test_api_endpoints.py`)
- Portfolio endpoints (GET /portfolio)
- Trading endpoints (POST /trade/buy, POST /trade/sell, GET /trade/positions)
- Market data endpoints (GET /market/{symbol})
- Strategy endpoints (POST /strategy/run)
- Authentication flow
- Error handling and validation
- CORS configuration
- Rate limiting
- Response format validation

### Integration Tests

#### 1. **Agent Integration** (`test_agent_integration.py`)
- Agent-to-agent communication
- Message format validation
- Market → Strategy workflow
- Strategy → Risk workflow
- Risk → Executor workflow
- Explainer integration
- User agent intervention
- Full trade workflow
- Agent network initialization
- Concurrent agent processing
- War Room display
- WebSocket updates
- Multi-user scenarios

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/unit/test_market_agent.py
pytest tests/integration/test_agent_integration.py
```

### Run Specific Test Class
```bash
pytest tests/unit/test_auth_api.py::TestUserAuthentication
```

### Run Specific Test
```bash
pytest tests/unit/test_auth_api.py::TestUserAuthentication::test_login_successful
```

### Run with Coverage Report
```bash
pytest --cov=src/backend --cov-report=html
```

### Run Async Tests
```bash
pytest -m asyncio
```

### Run Integration Tests Only
```bash
pytest -m integration
```

### Run Unit Tests Only
```bash
pytest -m unit
```

### Run Tests with Verbose Output
```bash
pytest -vv
```

### Run Tests with Print Statements
```bash
pytest -s
```

## Test Fixtures

Common fixtures are defined in `conftest.py`:

- **event_loop**: Event loop for async tests
- **mock_agent_network**: Mock agent network
- **mock_user**: Mock user object
- **mock_portfolio**: Mock portfolio data
- **mock_market_data**: Mock market data
- **mock_strategy**: Mock trading strategy
- **mock_trade_execution**: Mock trade execution result
- **mock_alpaca_client**: Mock Alpaca broker client
- **mock_openrouter_client**: Mock OpenRouter LLM client
- **mock_database**: Mock database connection
- **env_vars**: Environment variables
- **mock_generator**: Utility for generating mock objects
- **mock_env_vars**: Environment variable mocking
- **mock_api_errors**: Common API error responses

### Using Fixtures

```python
def test_example(mock_portfolio, mock_user):
    """Test with fixtures."""
    assert mock_portfolio["user_id"] == mock_user["id"]
```

## Mock Objects

### MockGenerator Utility

```python
def test_with_generator(mock_generator):
    """Using mock generator."""
    user = mock_generator.user(user_id="custom_123")
    portfolio = mock_generator.portfolio(total_value=500000)
    trade = mock_generator.trade(symbol="AAPL", qty=50)
```

## Test Markers

Use pytest markers to organize and filter tests:

```bash
# Run async tests
pytest -m asyncio

# Run integration tests
pytest -m integration

# Run market data tests
pytest -m market_data

# Run trading tests
pytest -m trading

# Run agent tests
pytest -m agents
```

## Best Practices

### 1. Isolation
- Each test should be independent
- Use fixtures for setup and teardown
- Mock external dependencies

### 2. Naming
- Test names should describe what is being tested
- Use descriptive class names
- Use `test_` prefix for all test functions

### 3. Async Tests
- Use `@pytest.mark.asyncio` decorator
- Use `AsyncMock` for mocking async functions
- Use `await` when calling async functions

### 4. Assertions
- Use clear, specific assertions
- Use pytest built-in assertions
- Avoid multiple assertions per test (one assertion focus)

### 5. Mocking
- Mock external services (APIs, databases)
- Use `unittest.mock.patch` for patching
- Use fixtures for common mocks

## Example Tests

### Simple Unit Test
```python
def test_agent_initialization(mock_agent_network):
    """Test agent initializes correctly."""
    from backend.core.base_agent import BaseAgent
    
    agent = BaseAgent(
        agent_type=AgentType.MARKET,
        agent_network=mock_agent_network,
        api_key="test_key"
    )
    
    assert agent.name == "Market Agent"
    assert agent.execution_count == 0
```

### Async Test
```python
@pytest.mark.asyncio
async def test_login_successful(mock_user_dao):
    """Test user login."""
    from backend.api.auth import login_user
    
    result = await login_user("testuser", "password")
    
    assert "access_token" in result
    assert result["token_type"] == "bearer"
```

### Integration Test
```python
@pytest.mark.asyncio
async def test_market_to_strategy_workflow(mock_agent_network):
    """Test market to strategy workflow."""
    # Market Agent scans
    market_data = await market_agent.scan_market()
    
    # Strategy Agent receives and processes
    strategy = await strategy_agent.generate_strategy(market_data)
    
    assert strategy["status"] == "generated"
```

## Coverage Goals

- **Overall Coverage**: >80%
- **Core Modules**: >90%
- **API Layer**: >85%
- **Agent Logic**: >85%

Check coverage with:
```bash
pytest --cov=src/backend --cov-report=term-missing
```

## CI/CD Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run tests
  run: pytest --cov=src/backend --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### Import Errors
- Ensure `conftest.py` is in the `tests/` directory
- Check that paths in `sys.path.insert()` are correct

### Async Test Issues
- Install `pytest-asyncio`: `pip install pytest-asyncio`
- Use `@pytest.mark.asyncio` decorator
- Use `event_loop` fixture for complex async setups

### Mock Issues
- Use `AsyncMock` for async functions
- Use `patch` from `unittest.mock`
- Check mock call assertions with `.assert_called()`

## Dependencies

Test dependencies are in `tests/requirements.txt`:

```
pytest>=7.0
pytest-asyncio>=0.20
pytest-cov>=4.0
pytest-mock>=3.10
```

Install with:
```bash
pip install -r tests/requirements.txt
```

## Contributing Tests

When adding new features:

1. Write unit tests for new components
2. Write integration tests for workflows
3. Ensure >80% coverage
4. Run full test suite before committing
5. Update this README with new test descriptions

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
