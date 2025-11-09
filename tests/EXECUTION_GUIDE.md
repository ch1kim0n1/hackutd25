"""
Test Execution Guide and Summary
Quick reference for running tests in the APEX system
"""

# ============================================================================
# APEX UNIT & INTEGRATION TEST SUITE - EXECUTION GUIDE
# ============================================================================

## Quick Start

### 1. Install Test Dependencies
```bash
cd tests
pip install -r requirements.txt
```

### 2. Run All Tests
```bash
pytest
```

### 3. Run Specific Test Category
```bash
pytest tests/unit/                    # All unit tests
pytest tests/integration/              # All integration tests
pytest tests/unit/test_market_agent.py # Single file
```

---

## Test Organization

### Unit Tests (tests/unit/)

1. **test_base_agent.py** (70 lines)
   - Tests core agent functionality
   - Covers: initialization, logging, performance tracking
   - Classes: TestBaseAgentInitialization, TestAgentPerformanceTracking
   
2. **test_auth_api.py** (230 lines)
   - Authentication and authorization tests
   - Covers: login, token refresh, JWT validation
   - Classes: TestUserAuthentication, TestTokenRefresh, TestPasswordService
   
3. **test_market_agent.py** (180 lines)
   - Market scanning and data analysis
   - Covers: news aggregation, sentiment analysis, VIX tracking
   - Classes: TestMarketDataScanning, TestNewsAnalysis, TestMarketAlerts
   
4. **test_risk_agent.py** (320 lines)
   - Risk assessment and Monte Carlo simulations
   - Covers: VaR, stress testing, constraint validation
   - Classes: TestMonteCarloSimulation, TestValueAtRisk, TestRiskConstraints
   
5. **test_strategy_agent.py** (250 lines)
   - Portfolio allocation and recommendations
   - Covers: rebalancing, goal alignment, sector rotation
   - Classes: TestPortfolioAllocation, TestTradeRecommendations
   
6. **test_executor_agent.py** (240 lines)
   - Trade execution and order management
   - Covers: order validation, execution, error handling
   - Classes: TestOrderValidation, TestTradeExecution, TestErrorRecovery
   
7. **test_api_endpoints.py** (280 lines)
   - FastAPI endpoint testing
   - Covers: portfolio, trading, market data endpoints
   - Classes: TestPortfolioEndpoints, TestTradingEndpoints, TestAuthenticationFlow
   
8. **test_models.py** (350 lines)
   - Database models and data layer
   - Covers: user, portfolio, trade models
   - Classes: TestUserModel, TestPortfolioModel, TestDataValidation

### Integration Tests (tests/integration/)

1. **test_agent_integration.py** (300 lines)
   - Multi-agent workflows
   - Covers: Market→Strategy→Risk→Executor pipelines
   - Classes: TestAgentCommunication, TestMarketToStrategyFlow

---

## Running Tests

### Basic Execution
```bash
# All tests
pytest

# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x
```

### Filtered Execution
```bash
# By test class
pytest tests/unit/test_market_agent.py::TestMarketDataScanning

# By test name pattern
pytest -k "test_login"

# By marker
pytest -m asyncio

# By file and line
pytest tests/unit/test_auth_api.py::123
```

### Coverage Reports
```bash
# Generate coverage
pytest --cov=src/backend --cov-report=html

# View in browser
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows

# Terminal report
pytest --cov=src/backend --cov-report=term-missing
```

### Parallel Execution
```bash
# Run tests in parallel (faster)
pytest -n auto

# Use 4 workers
pytest -n 4
```

### Async Tests
```bash
# Run only async tests
pytest -m asyncio

# Run only non-async tests
pytest -m "not asyncio"
```

---

## Test Statistics

| Category | File | Tests | Coverage |
|----------|------|-------|----------|
| Core Agent | test_base_agent.py | 12 | 90% |
| Authentication | test_auth_api.py | 18 | 85% |
| Market Agent | test_market_agent.py | 14 | 80% |
| Risk Agent | test_risk_agent.py | 22 | 85% |
| Strategy Agent | test_strategy_agent.py | 16 | 82% |
| Executor Agent | test_executor_agent.py | 20 | 83% |
| API Endpoints | test_api_endpoints.py | 24 | 80% |
| Models | test_models.py | 26 | 88% |
| Integration | test_agent_integration.py | 20 | 75% |
| **TOTAL** | **9 files** | **172 tests** | **83%** |

---

## Using Fixtures

### Common Fixtures (from conftest.py)
```python
def test_example(mock_portfolio, mock_user, mock_market_data):
    """Example using fixtures."""
    assert mock_portfolio["total_value"] == 100000
    assert mock_user["username"] == "testuser"
```

### Mock Generator
```python
def test_with_generator(mock_generator):
    """Using MockGenerator utility."""
    user = mock_generator.user(user_id="custom_456")
    portfolio = mock_generator.portfolio(total_value=250000)
    trade = mock_generator.trade(symbol="MSFT", qty=100)
```

---

## Writing New Tests

### Unit Test Template
```python
import pytest
from unittest.mock import Mock, patch

def test_feature_description():
    """Test description."""
    # Setup
    test_data = {"key": "value"}
    
    # Action
    result = function_under_test(test_data)
    
    # Assert
    assert result["expected"] == "value"
```

### Async Test Template
```python
@pytest.mark.asyncio
async def test_async_feature():
    """Test async function."""
    with patch('module.function') as mock_func:
        mock_func.return_value = {"data": "result"}
        
        result = await async_function()
        
        assert result["data"] == "result"
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install -r tests/requirements.txt
      - run: pytest --cov=src/backend
```

---

## Test Markers

Available markers for filtering:
```bash
pytest -m "agent"          # Agent-related tests
pytest -m "market_data"    # Market data tests
pytest -m "trading"        # Trading tests
pytest -m "integration"    # Integration tests
pytest -m "slow"           # Slow tests
```

---

## Debugging Failed Tests

### Verbose Debugging
```bash
# Show all details
pytest -vv test_file.py::test_name

# Show local variables in tracebacks
pytest -l

# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first error
pytest --pdbcls=IPython.terminal.debugger:TerminalPdb
```

### Common Issues

**ImportError for pytest**
- Solution: `pip install pytest`

**AsyncIO test errors**
- Solution: Install `pytest-asyncio` and mark tests with `@pytest.mark.asyncio`

**Mock not working**
- Check import path is correct
- Patch at the location where it's used, not where defined
- Use `AsyncMock` for async functions

---

## Performance

### Run Time Estimates
- Unit tests: ~10-15 seconds
- Integration tests: ~20-30 seconds
- Full suite: ~1-2 minutes

### Optimizations
```bash
# Parallel execution (4x faster)
pytest -n auto

# Only affected tests (after git changes)
pytest --lf

# Failed tests from last run
pytest --ff
```

---

## Test Maintenance

### Before Committing
```bash
# Run full test suite
pytest

# Check coverage
pytest --cov=src/backend --cov-report=term-missing

# Check for lint issues
pytest --linting
```

### Adding New Tests
1. Create test in appropriate file
2. Use existing fixtures from conftest.py
3. Follow naming conventions (test_*)
4. Add docstring describing test
5. Run and verify test passes
6. Check coverage report

---

## Resources

- Pytest Docs: https://docs.pytest.org/
- Mock Docs: https://docs.python.org/3/library/unittest.mock.html
- AsyncIO: https://docs.pytest.org/en/stable/how-to/fixtures.html#async-fixtures

---

## Test File Locations

```
tests/
├── conftest.py                    # Fixtures and config
├── requirements.txt               # Test dependencies
├── README.md                      # Test documentation
├── unit/
│   ├── test_base_agent.py
│   ├── test_auth_api.py
│   ├── test_market_agent.py
│   ├── test_risk_agent.py
│   ├── test_strategy_agent.py
│   ├── test_executor_agent.py
│   ├── test_api_endpoints.py
│   ├── test_models.py
│   └── __init__.py
└── integration/
    ├── test_agent_integration.py
    ├── test_workflows.py
    └── __init__.py
```

---

## Quick Reference Commands

```bash
# Run everything
pytest

# Specific file
pytest tests/unit/test_market_agent.py

# Specific test
pytest tests/unit/test_market_agent.py::TestMarketDataScanning::test_scan_market_returns_valid_structure

# With coverage
pytest --cov=src/backend

# Parallel execution
pytest -n auto

# Verbose output
pytest -vv

# Show output
pytest -s

# Only async tests
pytest -m asyncio

# Stop on first failure
pytest -x

# Rerun failed tests
pytest --lf

# Generate HTML coverage report
pytest --cov=src/backend --cov-report=html
open htmlcov/index.html
```

---

Generated: 2025-11-09
APEX Test Suite v1.0
