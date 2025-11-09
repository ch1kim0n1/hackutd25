import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import asyncio
try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    cp = np

class CrashScenarioEngine:
    def __init__(self, historical_data_loader):
        self.loader = historical_data_loader
        self.gpu_available = GPU_AVAILABLE
        self.current_scenario = None
        self.simulation_speed = 100
        self.is_running = False
        
    def load_scenario(self, scenario_name: str) -> Dict:
        data = self.loader.load_scenario(scenario_name)
        returns_matrix, symbols = self.loader.get_returns_matrix(scenario_name)
        spy_benchmark = self.loader.get_spy_benchmark(scenario_name)
        
        self.current_scenario = {
            'name': scenario_name,
            'data': data,
            'returns': returns_matrix,
            'symbols': symbols,
            'spy_benchmark': spy_benchmark,
            'current_day': 0,
            'total_days': len(returns_matrix)
        }
        
        return self.current_scenario
    
    def get_buy_and_hold_performance(self, initial_capital: float = 100000) -> pd.DataFrame:
        if not self.current_scenario:
            raise ValueError("No scenario loaded")
        
        spy = self.current_scenario['spy_benchmark'].copy()
        spy['Portfolio_Value'] = initial_capital * (1 + spy['Cumulative_Return'])
        spy['Strategy'] = 'Buy & Hold SPY'
        return spy[['Date', 'Portfolio_Value', 'Strategy']]
    
    def simulate_apex_strategy(
        self, 
        initial_capital: float = 100000,
        risk_tolerance: str = 'moderate'
    ) -> pd.DataFrame:
        if not self.current_scenario:
            raise ValueError("No scenario loaded")
        
        returns = self.current_scenario['returns']
        dates = pd.to_datetime(self.current_scenario['spy_benchmark']['Date'])
        
        portfolio_values = [initial_capital]
        allocations = []
        
        for day in range(len(returns)):
            if day == 0:
                allocation = self._get_initial_allocation(risk_tolerance)
            else:
                recent_vol = np.std(returns[max(0, day-20):day], axis=0)
                allocation = self._rebalance_on_volatility(recent_vol, risk_tolerance)
            
            allocations.append(allocation)
            
            if day < len(returns) - 1:
                daily_return = np.dot(allocation, returns[day])
                new_value = portfolio_values[-1] * (1 + daily_return)
                portfolio_values.append(new_value)
        
        return pd.DataFrame({
            'Date': dates[:len(portfolio_values)],
            'Portfolio_Value': portfolio_values,
            'Strategy': 'APEX Multi-Agent'
        })
    
    def _get_initial_allocation(self, risk_tolerance: str) -> np.ndarray:
        num_assets = len(self.current_scenario['symbols'])
        
        if risk_tolerance == 'conservative':
            weights = np.array([0.3, 0.2, 0.1, 0.1, 0.2, 0.1, 0.0])[:num_assets]
        elif risk_tolerance == 'aggressive':
            weights = np.array([0.5, 0.3, 0.1, 0.05, 0.05, 0.0, 0.0])[:num_assets]
        else:
            weights = np.array([0.4, 0.25, 0.15, 0.1, 0.1, 0.0, 0.0])[:num_assets]
        
        return weights / weights.sum()
    
    def _rebalance_on_volatility(self, volatilities: np.ndarray, risk_tolerance: str) -> np.ndarray:
        if np.mean(volatilities) > 0.03:
            safe_weight = 0.4 if risk_tolerance == 'conservative' else 0.3
            weights = np.ones(len(volatilities)) * ((1 - safe_weight) / (len(volatilities) - 1))
            weights[-2] = safe_weight
        else:
            weights = self._get_initial_allocation(risk_tolerance)
        
        return weights / weights.sum()
    
    async def run_simulation(
        self, 
        speed_multiplier: int = 100,
        message_callback = None
    ) -> Dict:
        if not self.current_scenario:
            raise ValueError("No scenario loaded")
        
        self.is_running = True
        self.simulation_speed = speed_multiplier
        
        delay = 0.1 / speed_multiplier
        total_days = self.current_scenario['total_days']
        
        apex_performance = self.simulate_apex_strategy()
        buy_hold_performance = self.get_buy_and_hold_performance()
        
        for day in range(total_days):
            if not self.is_running:
                break
            
            current_date = apex_performance.iloc[day]['Date']
            apex_value = apex_performance.iloc[day]['Portfolio_Value']
            buy_hold_value = buy_hold_performance.iloc[day]['Portfolio_Value']
            
            if message_callback and day % 5 == 0:
                await message_callback({
                    'day': day,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'apex_value': apex_value,
                    'buy_hold_value': buy_hold_value,
                    'apex_return': ((apex_value / 100000) - 1) * 100,
                    'buy_hold_return': ((buy_hold_value / 100000) - 1) * 100
                })
            
            await asyncio.sleep(delay)
        
        return {
            'apex_final': apex_performance.iloc[-1]['Portfolio_Value'],
            'buy_hold_final': buy_hold_performance.iloc[-1]['Portfolio_Value'],
            'apex_return': ((apex_performance.iloc[-1]['Portfolio_Value'] / 100000) - 1) * 100,
            'buy_hold_return': ((buy_hold_performance.iloc[-1]['Portfolio_Value'] / 100000) - 1) * 100,
            'outperformance': ((apex_performance.iloc[-1]['Portfolio_Value'] - buy_hold_performance.iloc[-1]['Portfolio_Value']) / 100000) * 100
        }
    
    def stop_simulation(self):
        self.is_running = False
    
    def get_comparison_data(self) -> Dict:
        if not self.current_scenario:
            return {}
        
        apex = self.simulate_apex_strategy()
        buy_hold = self.get_buy_and_hold_performance()
        
        return {
            'dates': apex['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'apex_values': apex['Portfolio_Value'].tolist(),
            'buy_hold_values': buy_hold['Portfolio_Value'].tolist(),
            'apex_final_return': ((apex.iloc[-1]['Portfolio_Value'] / 100000) - 1) * 100,
            'buy_hold_final_return': ((buy_hold.iloc[-1]['Portfolio_Value'] / 100000) - 1) * 100
        }
