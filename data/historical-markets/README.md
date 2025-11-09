# Historical Market Data

# Historical Market Data

This directory stores cached historical market data for crash scenarios.

## Available Scenarios

1. **2008 Financial Crisis** (2007-10-01 to 2009-03-31)
   - Subprime mortgage crisis
   - Great Recession
   - ~360 trading days

2. **2020 COVID-19 Crash** (2020-01-01 to 2020-12-31)
   - Pandemic-induced market crash
   - V-shaped recovery
   - ~252 trading days

3. **2022 Bear Market** (2021-12-01 to 2022-12-31)
   - Fed rate hikes
   - Inflation concerns
   - Tech stock correction

## Tracked Symbols

- **SPY**: S&P 500 ETF
- **QQQ**: NASDAQ-100 ETF
- **DIA**: Dow Jones ETF
- **IWM**: Russell 2000 ETF
- **TLT**: 20+ Year Treasury Bond ETF
- **GLD**: Gold ETF
- **VXX**: Volatility Index ETF
- **^VIX**: CBOE Volatility Index

## Usage

### Download Data

```bash
python src/backend/services/historical_data.py download
```

### View Statistics

```bash
python src/backend/services/historical_data.py
```

### Use in Code

```python
from services.historical_data import HistoricalDataLoader

loader = HistoricalDataLoader()

# Load scenario
data = loader.load_scenario("2008_crisis")

# Get returns for GPU backtesting
returns, symbols = loader.get_returns_matrix("2008_crisis")

# Get SPY benchmark for comparison
spy_benchmark = loader.get_spy_benchmark("2020_covid")
```

## Data Format

JSON files are structured as:

```json
{
  "scenario": {
    "name": "2008 Financial Crisis",
    "start": "2007-10-01",
    "end": "2009-03-31",
    "description": "..."
  },
  "symbols": {
    "SPY": {
      "description": "S&P 500 ETF",
      "dates": ["2007-10-01", "2007-10-02", ...],
      "open": [153.42, 152.80, ...],
      "high": [154.05, 153.71, ...],
      "low": [152.29, 150.00, ...],
      "close": [153.27, 150.48, ...],
      "volume": [157125900, 298710600, ...],
      "adj_close": [121.34, 119.15, ...]
    }
  }
}
```

## Cache Management

- Data is cached to avoid re-downloading
- Use `force_refresh=True` to re-download
- Cache location: `data/historical-markets/*.json`
- Total size: ~2-5 MB per scenario


**Contents:**
- 2008 financial crisis data
- 2020 market crash data
- VIX historical data
- S&P 500 benchmark data

**Status:** To be populated
