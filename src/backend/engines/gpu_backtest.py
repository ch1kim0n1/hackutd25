import cupy as cp
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
import asyncio
from datetime import datetime

class GPUBacktester:
    """
    GPU-accelerated backtesting engine using NVIDIA CUDA.
    Critical for the Market Crash Simulator feature - can simulate
    2008, 2020 scenarios at 100x speed as mentioned in refined README.
    """
    def __init__(self):
        self.gpu_available = cp.cuda.is_available()
        self.max_strategies = 500 
    
    def batch_backtest(
        self,
        strategies: List[Dict],
        market_data: np.ndarray,
        num_simulations: int = 1000
    ) -> List[Dict]:
        """
        Test multiple strategies in parallel on GPU.
        This powers the crash simulator for historical scenario comparison.
        """
        if not self.gpu_available:
            return self.cpu_fallback(strategies, market_data)
        
        market_data_gpu = cp.array(market_data)
        results = []
        
        for strategy in strategies:
            returns = self.simulate_strategy_gpu(
                strategy,
                market_data_gpu,
                num_simulations
            )
            
            sharpe = self.calculate_sharpe_gpu(returns)
            max_drawdown = self.calculate_max_drawdown_gpu(returns)
            var_95 = cp.percentile(returns, 5)
            
            results.append({
                "strategy_id": strategy.get("id", "unknown"),
                "strategy_name": strategy.get("name", "Unnamed"),
                "sharpe_ratio": float(cp.asnumpy(sharpe)),
                "max_drawdown": float(cp.asnumpy(max_drawdown)),
                "var_95": float(cp.asnumpy(var_95)),
                "annual_return": float(cp.asnumpy(cp.mean(returns)) * 252),
                "volatility": float(cp.asnumpy(cp.std(returns)) * cp.sqrt(252)),
                "simulations": num_simulations
            })
        
        return results
    
    def simulate_strategy_gpu(
        self,
        strategy: Dict,
        market_data_gpu: cp.ndarray,
        num_sims: int
    ) -> cp.ndarray:
        """
        GPU-accelerated Monte Carlo simulation for portfolio paths.
        """
        allocation = np.array(list(strategy["allocation"].values())) / 100
        weights_gpu = cp.array(allocation)
        
        mean_returns_gpu = cp.mean(market_data_gpu, axis=0)
        cov_matrix_gpu = cp.cov(market_data_gpu.T)
        
        n_days = 252
        scenarios_gpu = cp.random.multivariate_normal(
            mean_returns_gpu,
            cov_matrix_gpu,
            size=(num_sims, n_days)
        )
        
        portfolio_returns = cp.dot(scenarios_gpu, weights_gpu)
        
        return portfolio_returns
    
    def calculate_sharpe_gpu(self, returns: cp.ndarray) -> cp.ndarray:
        """Calculate Sharpe ratio on GPU."""
        risk_free_rate = 0.02
        daily_rf_rate = risk_free_rate / 252
        
        mean_return = cp.mean(returns, axis=1)
        std_return = cp.std(returns, axis=1, ddof=1)
        
        sharpe = (mean_return - daily_rf_rate) / std_return
        return sharpe * cp.sqrt(252)
    
    def calculate_max_drawdown_gpu(self, returns: cp.ndarray) -> cp.ndarray:
        """Calculate maximum drawdown on GPU."""
        cumulative_returns = cp.cumprod(1 + returns, axis=1)
        running_max = cp.maximum.accumulate(cumulative_returns, axis=1)
        drawdown_percent = (cumulative_returns / running_max - 1)
        
        return cp.min(drawdown_percent, axis=1)
    
    def cpu_fallback(
        self,
        strategies: List[Dict],
        market_data: np.ndarray
    ) -> List[Dict]:
        """CPU fallback when GPU not available."""
        results = []
        batch_size = min(10, len(strategies))
        
        for strategy in strategies[:batch_size]:
            returns = self.simulate_strategy_cpu(strategy, market_data)
            
            sharpe = np.mean(returns) / (np.std(returns) or 0.0001) * np.sqrt(252)
            max_dd = np.max(np.maximum.accumulate(np.cumprod(1 + returns)) / np.cumprod(1 + returns) - 1)
            var_95 = np.percentile(returns, 5)
            
            results.append({
                "strategy_id": strategy.get("id", "unknown"),
                "strategy_name": strategy.get("name", "Unnamed"),
                "sharpe_ratio": sharpe,
                "max_drawdown": max_dd,
                "var_95": var_95,
                "annual_return": np.mean(returns) * 252,
                "volatility": np.std(returns) * np.sqrt(252),
                "simulations": 1
            })
        
        return results
    
    def simulate_strategy_cpu(self, strategy: Dict, market_data: np.ndarray) -> np.ndarray:
        """CPU fallback simulation."""
        allocation = np.array(list(strategy["allocation"].values())) / 100
        returns = np.average(market_data, axis=1, weights=allocation)
        return returns
    
    async def simulate_crash_scenario(
        self,
        strategy: Dict,
        scenario: str = "2008_financial_crisis"
    ) -> Dict:
        """
        NEW: Simulate specific historical crash scenarios.
        Powers the Market Crash Simulator feature from refined README.
        """
        crash_scenarios = {
            "2008_financial_crisis": {
                "duration_days": 252,
                "market_drop": -0.37,
                "volatility_spike": 3.5,
                "name": "2008 Financial Crisis"
            },
            "2020_covid_crash": {
                "duration_days": 60,
                "market_drop": -0.34,
                "volatility_spike": 4.2,
                "name": "2020 COVID Crash"
            },
            "2022_bear_market": {
                "duration_days": 180,
                "market_drop": -0.18,
                "volatility_spike": 1.8,
                "name": "2022 Bear Market"
            }
        }
        
        scenario_data = crash_scenarios.get(scenario, crash_scenarios["2008_financial_crisis"])
        
        # Generate synthetic crash data
        crash_returns = self.generate_crash_data(
            scenario_data["duration_days"],
            scenario_data["market_drop"],
            scenario_data["volatility_spike"]
        )
        
        # Simulate strategy performance
        allocation = np.array(list(strategy["allocation"].values())) / 100
        portfolio_returns = crash_returns @ allocation
        
        cumulative_return = (1 + portfolio_returns).prod() - 1
        max_drawdown = np.min(np.minimum.accumulate(portfolio_returns))
        
        return {
            "scenario": scenario_data["name"],
            "strategy_return": float(cumulative_return),
            "market_return": float(scenario_data["market_drop"]),
            "outperformance": float(cumulative_return - scenario_data["market_drop"]),
            "max_drawdown": float(max_drawdown),
            "recovery_days": int(self.estimate_recovery_days(portfolio_returns))
        }
    
    def generate_crash_data(
        self,
        days: int,
        total_drop: float,
        volatility_multiplier: float
    ) -> np.ndarray:
        """Generate synthetic crash scenario data."""
        np.random.seed(42)
        base_volatility = 0.01
        
        # Create downtrend with high volatility
        trend = np.linspace(0, total_drop, days)
        noise = np.random.randn(days, 4) * base_volatility * volatility_multiplier
        
        crash_returns = trend[:, np.newaxis] + noise
        return crash_returns
    
    def estimate_recovery_days(self, returns: np.ndarray) -> int:
        """Estimate recovery time in trading days."""
        cumulative = np.cumprod(1 + returns)
        peak = cumulative[0]
        
        for i, val in enumerate(cumulative):
            if val >= peak:
                return i
        
        return len(returns)

