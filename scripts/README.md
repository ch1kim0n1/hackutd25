# Scripts

Utility scripts for development and deployment.

## Stock Analysis Script

A Python tool that fetches historical stock prices and sends analysis data to AI agents for evaluation.

### Features

- 📊 Fetches 2-month stock performance data from Yahoo Finance
- 🗓️ Automatically handles market closures (weekends & holidays)
- 📈 Calculates performance metrics (absolute & percentage change)
- 🤖 Integrates with AI agent system for multi-agent analysis
- 💾 Saves analysis requests for agent processing

### Installation

Install Python dependencies:
```bash
pip install -r scripts/requirements.txt
```

### Usage

Run the script:
```bash
python scripts/stock_analysis.py
```

The script will prompt you for:
1. **Stock Symbol** (e.g., AAPL, TSLA, SPY, GOOGL)
2. **End Date** in YYYY-MM-DD format

It will then:
- Calculate the start date (2 months before end date)
- Fetch closing prices for both dates
- Handle market closures automatically
- Display performance metrics
- Send data to AI agents for analysis

### Example

```
Enter stock symbol (e.g., AAPL, TSLA, SPY): AAPL
✓ Selected stock: AAPL

Enter end date (YYYY-MM-DD): 2024-11-08
✓ End date: 2024-11-08

✓ Start date (2 months prior): 2024-09-08

Fetching stock data from Yahoo Finance...
------------------------------------------------------------
✓ Start Date: 2024-09-06
  Closing Price: $220.82

✓ End Date: 2024-11-08
  Closing Price: $226.47

------------------------------------------------------------
PERFORMANCE SUMMARY
------------------------------------------------------------
Absolute Change: $5.65
Percent Change: 2.56%
📈 Stock is UP over the 2-month period
```

### AI Agent Integration

The script sends stock analysis data to the AI agent orchestrator for multi-agent evaluation:
- **Market Agent**: Analyzes market sentiment and trends
- **Strategy Agent**: Evaluates investment opportunity
- **Risk Agent**: Assesses risk factors and volatility
- **Explainer Agent**: Provides user-friendly explanation

Output is saved to: `data/mock-data/stock_analysis_[SYMBOL]_[TIMESTAMP].json`

### Popular Stock Symbols

- **AAPL** - Apple Inc.
- **TSLA** - Tesla Inc.
- **SPY** - S&P 500 ETF
- **GOOGL** - Alphabet Inc.
- **MSFT** - Microsoft Corporation
- **AMZN** - Amazon.com Inc.
- **NVDA** - NVIDIA Corporation
- **META** - Meta Platforms Inc.

---

## Other Scripts

**Contents:**
- Setup and installation scripts
- Database migration scripts
- Build and deployment scripts
- Testing automation

**Status:** To be created
