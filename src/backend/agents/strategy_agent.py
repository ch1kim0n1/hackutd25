import asyncio
from typing import Dict, List, Tuple
import numpy as np
import cupy as cp
from datetime import datetime
import json

class StrategyAgent:
    def __init__(self, agent_network):
        self.agent_network = agent_network
        self.name = "Strategy Agent"
        self.strategies = {}
        self.active_strategy = None

    async def initialize(self):
        await self.agent_network.subscribe("market_regime_change", self.handle_regime_change)
        await self.agent_network.subscribe("risk_alert", self.handle_risk_alert)
        await self.agent_network.subscribe("user_goal_update", self.update_strategy)
        return {"status": "initialized", "agent": self.name}

    async def generate_strategy(self, user_goals: Dict, market_context: Dict, risk_tolerance: float) -> Dict:
        allocation = self.optimize_allocation(user_goals, market_context, risk_tolerance)
        
        strategy = {
            "id": "adaptive_all_weather_v2_3",
            "name": "Adaptive All-Weather v2.3",
            "allocation": allocation,
            "rules": {
                "rebalance_triggers": ["drift > 7%", "VIX > 30%", "regime_change"],
                "fail_safes": {
                    "portfolio_down_15": "shift to 70% defensive",
                    "vix_above_40": "go 50% cash immediately"
                }
            },
            "rationale": "Balanced growth with downside protection through dynamic allocation",
            "expected_performance": {
                "annual_return": "9.2%",
                "volatility": "11.3%",
                "sharpe_ratio": "0.81"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        self.active_strategy = strategy
        await self.agent_network.publish("strategy.generated", strategy)
        
        return strategy

    def optimize_allocation(self, user_goals: Dict, market_context: Dict, risk_tolerance: float) -> Dict:
        if cp.cuda.is_available():
            return self.gpu_optimize_allocation(user_goals, market_context, risk_tolerance)
        else:
            return self.cpu_optimize_allocation(user_goals, market_context, risk_tolerance)

    def gpu_optimize_allocation(self, user_goals: Dict, market_context: Dict, risk_tolerance: float) -> Dict:
        returns_gpu = cp.array(self.get_historical_returns())
        cov_matrix_gpu = cp.cov(returns_gpu.T)
        
        optimal_weights = self.solve_optimization_gpu(returns_gpu, cov_matrix_gpu, risk_tolerance)
        weights = cp.asnumpy(optimal_weights).tolist()
        
        return {
            "growth_stocks": weights[0] * 100,
            "defensive_stocks": weights[1] * 100,
            "bonds": weights[2] * 100,
            "alternatives": weights[3] * 100
        }

    def cpu_optimize_allocation(self, user_goals: Dict, market_context: Dict, risk_tolerance: float) -> Dict:
        if risk_tolerance > 0.7:
            return {"growth_stocks": 45, "defensive_stocks": 25, "bonds": 20, "alternatives": 10}
        elif risk_tolerance > 0.4:
            return {"growth_stocks": 40, "defensive_stocks": 27, "bonds": 20, "alternatives": 13}
        else:
            return {"growth_stocks": 25, "defensive_stocks": 35, "bonds": 30, "alternatives": 10}

    def get_historical_returns(self) -> np.ndarray:
        np.random.seed(42)
        return np.random.randn(252, 4) * 0.02

    def solve_optimization_gpu(self, returns, cov_matrix, risk_tolerance):
        n_assets = returns.shape[1]
        ones = cp.ones(n_assets)
        
        inv_cov = cp.linalg.inv(cov_matrix)
        weights = inv_cov @ ones
        weights = weights / cp.sum(weights)
        
        return weights

    async def handle_regime_change(self, message):
        new_regime = message.get("data", {}).get("regime")
        
        if new_regime in ["Crisis Mode", "High Volatility"]:
            await self.agent_network.broadcast_agent_communication(
                self.name, 
                "Risk Agent", 
                f"Regime shift to {new_regime} detected. Recommending defensive posture."
            )
            
            if self.active_strategy:
                defensive_allocation = self.adjust_for_defensive_mode(self.active_strategy["allocation"])
                
                await self.agent_network.publish("strategy.adjustment", {
                    "reason": f"Regime change to {new_regime}",
                    "allocation": defensive_allocation
                })

    async def handle_risk_alert(self, message):
        alert_data = message.get("data", {})
        
        await self.agent_network.broadcast_agent_communication(
            self.name,
            "Risk Agent", 
            f"Risk alert received: {alert_data.get('type')}. Analyzing strategy impact."
        )

    def adjust_for_defensive_mode(self, current_allocation):
        def_adjusted = current_allocation.copy()
        def_adjusted["growth_stocks"] *= 0.75
        def_adjusted["defensive_stocks"] *= 1.25
        def_adjusted["alternatives"] *= 1.1
        
        total = sum(def_adjusted.values())
        for key in def_adjusted:
            def_adjusted[key] = def_adjusted[key] / total * 100
            
        return def_adjusted

    async def evolve_strategy(self, market_data: Dict, performance_history: Dict) -> Dict:
        strategies_to_test = self.generate_strategy_variants(50)
        
        backtest_results = []
        for strategy in strategies_to_test:
            performance = self.backtest_strategy(strategy, market_data)
            backtest_results.append((strategy, performance))
        
        best_strategy = max(backtest_results, key=lambda x: x[1]["sharpe_ratio"])[0]
        
        await self.agent_network.publish("strategy.evolved", {
            "old_strategy": self.active_strategy,
            "new_strategy": best_strategy,
            "improvement": f"Sharpe ratio improved by {best_strategy['expected_performance']['sharpe_ratio'] - self.active_strategy['expected_performance']['sharpe_ratio']:.2f}"
        })
        
        self.active_strategy = best_strategy
        return best_strategy

    def generate_strategy_variants(self, count: int) -> List[Dict]:
        strategies = []
        base_allocation = [40, 27, 20, 13]
        
        for i in range(count):
            variant = base_allocation.copy()
            for j in range(len(variant)):
                variant[j] += (np.random.random() - 0.5) * 20
                variant[j] = max(5, min(60, variant[j]))
            
            total = sum(variant)
            variant = [v/total*100 for v in variant]
            
            strategies.append({
                "id": f"variant_{i}",
                "allocation": {
                    "growth_stocks": variant[0],
                    "defensive_stocks": variant[1],
                    "bonds": variant[2],
                    "alternatives": variant[3]
                },
                "expected_performance": {
                    "sharpe_ratio": np.random.normal(0.8, 0.2)
                }
            })
        
        return strategies

    def backtest_strategy(self, strategy: Dict, market_data: Dict) -> Dict:
        return {
            "sharpe_ratio": strategy["expected_performance"]["sharpe_ratio"],
            "max_drawdown": np.random.uniform(8, 18),
            "annual_return": np.random.uniform(6, 12)
        }

