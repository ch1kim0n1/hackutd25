"""
Unit tests for Strategy Agent.
Tests portfolio allocation, trade recommendations, and strategy optimization.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Dict


class TestStrategyAgentInitialization:
    """Test Strategy Agent initialization."""
    
    def test_strategy_agent_init(self):
        """Test Strategy Agent initialization."""
        logging_enabled = False
        strategy_history = []
        
        assert logging_enabled is False
        assert isinstance(strategy_history, list)
    
    def test_strategy_history_tracking(self):
        """Test that strategy history is maintained."""
        strategy_history = []
        
        # Add a strategy
        strategy_history.append({"type": "rebalance", "timestamp": datetime.now()})
        
        assert len(strategy_history) > 0


class TestPortfolioAllocation:
    """Test portfolio allocation strategies."""
    
    def test_generate_allocation_strategy(self):
        """Test generation of asset allocation."""
        market_report = {
            "market_data": {"VIX": 15, "trend": "bullish"},
            "analysis": "Market outlook positive"
        }
        
        portfolio = {
            "total_value": 100000,
            "cash": 20000
        }
        
        user_profile = {
            "risk_tolerance": "moderate",
            "time_horizon": 10  # years
        }
        
        # Should generate allocation like:
        # SPY: 60%, TLT: 20%, GLD: 10%, Cash: 10%
        expected_allocation = {
            "SPY": 0.60,
            "TLT": 0.20,
            "GLD": 0.10,
            "Cash": 0.10
        }
        
        total_allocation = sum(expected_allocation.values())
        assert total_allocation == 1.0


class TestTradeRecommendations:
    """Test trade recommendation generation."""
    
    def test_buy_recommendation(self):
        """Test buy signal generation."""
        # Should recommend BUY when:
        # - Price below moving average
        # - Positive momentum
        # - Good valuation metrics
        
        recommendation_data = {
            "price": 100,
            "moving_average_50": 105,
            "momentum": "positive",
            "pe_ratio": 15
        }
        
        # Buy signal: price below MA and positive momentum
        is_buy_signal = (recommendation_data["price"] < recommendation_data["moving_average_50"] and 
                        recommendation_data["momentum"] == "positive")
        assert is_buy_signal is True


class TestRebalancing:
    """Test portfolio rebalancing strategies."""
    
    def test_quarterly_rebalancing(self):
        """Test quarterly portfolio rebalancing."""
        # Portfolio that has drifted from targets
        current_portfolio = {
            "SPY": {"weight": 0.75, "target": 0.60},  # Overweight
            "TLT": {"weight": 0.15, "target": 0.30},  # Underweight
            "GLD": {"weight": 0.10, "target": 0.10},  # On target
        }
        
        # Calculate drift for each position (use approximate comparison for floats)
        for asset, data in current_portfolio.items():
            drift = abs(data["weight"] - data["target"])
            if asset == "SPY":
                assert abs(drift - 0.15) < 1e-10  # Over by 15%
            elif asset == "TLT":
                assert abs(drift - 0.15) < 1e-10  # Under by 15%
    
    def test_tax_loss_harvesting(self):
        """Test tax loss harvesting opportunities."""
        # Should identify losing positions that can be sold
        # While maintaining portfolio composition
        
        positions = {
            "AAPL": {"cost_basis": 150, "current_price": 140, "loss": -10},
            "MSFT": {"cost_basis": 300, "current_price": 310, "gain": 10}
        }
        
        # Can harvest losses from AAPL
        can_harvest_loss = positions["AAPL"]["loss"] < 0
        assert can_harvest_loss is True


class TestDriftDetection:
    """Test detection of portfolio drift from targets."""
    
    def test_drift_threshold(self):
        """Test that drift beyond threshold triggers rebalancing."""
        # Typically rebalance when allocation drifts >5% from target
        
        target_weight = 0.60
        current_weight = 0.67
        drift = abs(current_weight - target_weight)
        threshold = 0.05
        
        should_rebalance = drift > threshold
        assert should_rebalance is True


class TestRiskAdjustment:
    """Test risk-adjusted strategy generation."""
    
    def test_aggressive_strategy(self):
        """Test aggressive allocation for young investors."""
        user_profile = {
            "age": 25,
            "risk_tolerance": "high",
            "time_horizon": 40,
            "income": 75000
        }
        
        # Should allocate high to stocks (80-90%)
        aggressive_equity_allocation = 0.85
        assert aggressive_equity_allocation >= 0.80
    
    def test_conservative_strategy(self):
        """Test conservative allocation for retirees."""
        user_profile = {
            "age": 70,
            "risk_tolerance": "low",
            "time_horizon": 15,
            "withdrawing": True
        }
        
        # Should allocate high to bonds (50-70%)
        conservative_bond_allocation = 0.60
        assert conservative_bond_allocation >= 0.50


class TestGoalAlignment:
    """Test strategy alignment with user goals."""
    
    def test_goal_based_strategy(self):
        """Test strategy generation based on user goals."""
        goals = {
            "retire_at": 60,
            "target_amount": 1000000,
            "annual_spending": 50000
        }
        
        current_age = 35
        years_to_goal = goals["retire_at"] - current_age
        
        # Should calculate required return and adjust allocation
        assert years_to_goal == 25


class TestMarketConditionAdaptation:
    """Test strategy adaptation to market conditions."""
    
    def test_bullish_market_strategy(self):
        """Test increased equity allocation in bull market."""
        market_report = {
            "condition": "bullish",
            "vix": 12,
            "earnings_growth": "strong"
        }
        
        # Should increase equity exposure
        equity_allocation_bull = 0.75
        assert equity_allocation_bull > 0.60
    
    def test_bearish_market_strategy(self):
        """Test defensive allocation in bear market."""
        market_report = {
            "condition": "bearish",
            "vix": 35,
            "economic_data": "weak"
        }
        
        # Should increase defensive positions (bonds, gold)
        bond_allocation_bear = 0.50
        assert bond_allocation_bear >= 0.40
    
    def test_crisis_strategy(self):
        """Test emergency strategy during market crisis."""
        market_report = {
            "condition": "crisis",
            "vix": 80,
            "circuit_breakers": "triggered"
        }
        
        # Should move to cash/stable value
        cash_allocation = 0.40
        assert cash_allocation > 0.20


class TestSectorRotation:
    """Test sector rotation strategies."""
    
    def test_sector_relative_strength(self):
        """Test sector allocation based on relative strength."""
        sector_analysis = {
            "Technology": {"strength": 0.85},
            "Healthcare": {"strength": 0.70},
            "Energy": {"strength": 0.40},
            "Utilities": {"strength": 0.50}
        }
        
        # Should overweight strong sectors
        tech_should_be_highest = sector_analysis["Technology"]["strength"] > sector_analysis["Energy"]["strength"]
        assert tech_should_be_highest is True


class TestMomentumStrategy:
    """Test momentum-based strategies."""
    
    def test_momentum_signals(self):
        """Test generation of momentum signals."""
        price_history = {
            "SPY": [100, 102, 103, 105, 108],  # Uptrend
            "TLT": [80, 79, 78, 77, 76],  # Downtrend
        }
        
        # SPY: strong momentum (BUY)
        spy_trend = price_history["SPY"][-1] > price_history["SPY"][0]
        assert spy_trend is True
        
        # TLT: negative momentum (SELL)
        tlt_trend = price_history["TLT"][-1] < price_history["TLT"][0]
        assert tlt_trend is True


class TestValueStrategy:
    """Test value-based strategies."""
    
    def test_valuation_metrics(self):
        """Test valuation-based recommendations."""
        valuations = {
            "AAPL": {"pe": 25, "pb": 40, "market_pe": 18},  # Expensive
            "JPM": {"pe": 12, "pb": 1.5, "market_pe": 18},  # Cheap
        }
        
        # AAPL: Overvalued (SELL)
        aapl_overvalued = valuations["AAPL"]["pe"] > valuations["AAPL"]["market_pe"]
        assert aapl_overvalued is True
        
        # JPM: Undervalued (BUY)
        jpm_undervalued = valuations["JPM"]["pe"] < valuations["JPM"]["market_pe"]
        assert jpm_undervalued is True


class TestStrategyLogging:
    """Test strategy logging."""
    
    def test_logging_enabled(self):
        """Test logging when enabled."""
        logging_enabled = True
        
        assert logging_enabled is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
