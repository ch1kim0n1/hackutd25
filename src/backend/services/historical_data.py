"""
Historical Market Data Loader
Loads and formats crisis data for GPU backtester and crash simulator.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import os
import json
from pathlib import Path


class HistoricalDataLoader:
    """
    Loads historical market data for crash scenarios.
    Supports 2008 Financial Crisis and 2020 COVID Crash.
    """
    
    def __init__(self, cache_dir: str = "../../data/historical-markets"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Crisis periods
        self.scenarios = {
            "2008_crisis": {
                "name": "2008 Financial Crisis",
                "start": "2007-10-01",
                "end": "2009-03-31",
                "description": "Subprime mortgage crisis and Great Recession"
            },
            "2020_covid": {
                "name": "2020 COVID-19 Crash",
                "start": "2020-01-01",
                "end": "2020-12-31",
                "description": "COVID-19 pandemic market crash and recovery"
            },
            "2022_bear": {
                "name": "2022 Bear Market",
                "start": "2021-12-01",
                "end": "2022-12-31",
                "description": "Fed rate hikes and inflation concerns"
            }
        }
        
        # Symbols to track
        self.symbols = {
            "SPY": "S&P 500 ETF",
            "QQQ": "NASDAQ-100 ETF",
            "DIA": "Dow Jones ETF",
            "IWM": "Russell 2000 ETF",
            "TLT": "20+ Year Treasury Bond ETF",
            "GLD": "Gold ETF",
            "VXX": "Volatility Index ETF",
            "^VIX": "CBOE Volatility Index"
        }
    
    def load_scenario(self, scenario_name: str, force_refresh: bool = False) -> Dict:
        """
        Load complete scenario data.
        
        Args:
            scenario_name: "2008_crisis", "2020_covid", or "2022_bear"
            force_refresh: Re-download even if cached
            
        Returns:
            Dict with scenario metadata and OHLCV data for all symbols
        """
        if scenario_name not in self.scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}. Choose from {list(self.scenarios.keys())}")
        
        scenario = self.scenarios[scenario_name]
        cache_file = self.cache_dir / f"{scenario_name}.json"
        
        # Load from cache if exists and not forcing refresh
        if cache_file.exists() and not force_refresh:
            print(f"📂 Loading {scenario['name']} from cache...")
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        # Download data
        print(f"📥 Downloading {scenario['name']} data...")
        data = {
            "scenario": scenario,
            "symbols": {},
            "downloaded_at": datetime.now().isoformat()
        }
        
        for symbol, description in self.symbols.items():
            try:
                print(f"  Fetching {symbol}...")
                df = yf.download(
                    symbol,
                    start=scenario["start"],
                    end=scenario["end"],
                    progress=False
                )
                
                if df.empty:
                    print(f"  ⚠️  No data for {symbol}")
                    continue
                
                # Convert to dict format
                data["symbols"][symbol] = {
                    "description": description,
                    "dates": df.index.strftime('%Y-%m-%d').tolist(),
                    "open": df['Open'].tolist(),
                    "high": df['High'].tolist(),
                    "low": df['Low'].tolist(),
                    "close": df['Close'].tolist(),
                    "volume": df['Volume'].tolist(),
                    "adj_close": df['Adj Close'].tolist() if 'Adj Close' in df.columns else df['Close'].tolist()
                }
                
            except Exception as e:
                print(f"  ❌ Error fetching {symbol}: {e}")
        
        # Save to cache
        print(f"💾 Saving to cache: {cache_file}")
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    
    def get_returns_matrix(self, scenario_name: str) -> np.ndarray:
        """
        Get daily returns matrix for GPU backtesting.
        
        Returns:
            numpy array of shape (days, num_symbols) with daily returns
        """
        data = self.load_scenario(scenario_name)
        
        symbols_data = []
        symbol_names = []
        
        for symbol, info in data["symbols"].items():
            if symbol == "^VIX":  # Skip VIX for returns calculation
                continue
            
            closes = np.array(info["adj_close"])
            returns = np.diff(closes) / closes[:-1]  # Daily returns
            symbols_data.append(returns)
            symbol_names.append(symbol)
        
        # Align all to same length (some may have missing days)
        min_length = min(len(r) for r in symbols_data)
        aligned = np.array([r[:min_length] for r in symbols_data]).T
        
        print(f"📊 Returns matrix shape: {aligned.shape} ({min_length} days, {len(symbol_names)} symbols)")
        print(f"   Symbols: {symbol_names}")
        
        return aligned, symbol_names
    
    def get_spy_benchmark(self, scenario_name: str) -> pd.DataFrame:
        """
        Get SPY (S&P 500) data for buy-and-hold comparison.
        
        Returns:
            DataFrame with Date, Close, and Cumulative Return
        """
        data = self.load_scenario(scenario_name)
        
        if "SPY" not in data["symbols"]:
            raise ValueError("SPY data not available")
        
        spy = data["symbols"]["SPY"]
        df = pd.DataFrame({
            "Date": pd.to_datetime(spy["dates"]),
            "Close": spy["adj_close"]
        })
        
        # Calculate cumulative returns
        df["Daily_Return"] = df["Close"].pct_change()
        df["Cumulative_Return"] = (1 + df["Daily_Return"]).cumprod() - 1
        
        return df
    
    def download_all_scenarios(self):
        """Download all predefined scenarios."""
        print("🚀 Downloading all historical crash scenarios...\n")
        
        for scenario_name in self.scenarios.keys():
            try:
                self.load_scenario(scenario_name, force_refresh=True)
                print(f"✅ {scenario_name} complete\n")
            except Exception as e:
                print(f"❌ {scenario_name} failed: {e}\n")
        
        print("🎉 All scenarios downloaded!")
    
    def get_scenario_stats(self, scenario_name: str) -> Dict:
        """
        Get summary statistics for a scenario.
        
        Returns:
            Dict with max drawdown, volatility, recovery time, etc.
        """
        spy_data = self.get_spy_benchmark(scenario_name)
        
        # Calculate statistics
        cumulative = spy_data["Cumulative_Return"].values
        daily_returns = spy_data["Daily_Return"].dropna().values
        
        # Maximum drawdown
        running_max = np.maximum.accumulate(cumulative + 1)
        drawdown = (cumulative + 1 - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Find drawdown dates
        max_dd_idx = drawdown.argmin()
        max_dd_date = spy_data.iloc[max_dd_idx]["Date"]
        
        # Volatility (annualized)
        volatility = daily_returns.std() * np.sqrt(252)
        
        # Final return
        final_return = cumulative[-1]
        
        return {
            "scenario": self.scenarios[scenario_name]["name"],
            "period": f"{self.scenarios[scenario_name]['start']} to {self.scenarios[scenario_name]['end']}",
            "max_drawdown": f"{max_drawdown:.2%}",
            "max_drawdown_date": max_dd_date.strftime('%Y-%m-%d'),
            "volatility_annualized": f"{volatility:.2%}",
            "total_return": f"{final_return:.2%}",
            "num_trading_days": len(spy_data)
        }


# CLI for testing
if __name__ == "__main__":
    import sys
    
    loader = HistoricalDataLoader()
    
    if len(sys.argv) > 1 and sys.argv[1] == "download":
        # Download all scenarios
        loader.download_all_scenarios()
    else:
        # Show stats for all scenarios
        print("\n📊 HISTORICAL CRASH SCENARIOS\n")
        for scenario_name in loader.scenarios.keys():
            try:
                stats = loader.get_scenario_stats(scenario_name)
                print(f"{stats['scenario']}")
                print(f"  Period: {stats['period']}")
                print(f"  Max Drawdown: {stats['max_drawdown']} on {stats['max_drawdown_date']}")
                print(f"  Volatility: {stats['volatility_annualized']}")
                print(f"  Total Return: {stats['total_return']}")
                print(f"  Trading Days: {stats['num_trading_days']}\n")
            except Exception as e:
                print(f"❌ {scenario_name}: {e}\n")
