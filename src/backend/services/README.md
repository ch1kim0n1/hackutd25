# APEX Backend Services

Shared services used across the backend.

## Available Services

### `historical_data.py`
Historical market data loader for crash simulations.

**Usage**:
```python
from services.historical_data import HistoricalDataLoader

loader = HistoricalDataLoader()
data = loader.load_scenario("2008_crisis")
```

### Future Services

- `voice.py` - Voice recognition and TTS
- `personal_finance.py` - Plaid integration
- `news_search.py` - Market news aggregation
- `db.py` - Database utilities
- `jwt_service.py` - Authentication
