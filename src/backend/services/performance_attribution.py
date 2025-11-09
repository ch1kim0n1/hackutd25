# backend/services/performance_attribution.py
"""
Performance attribution engine for APEX.
Breaks down portfolio returns into components: asset allocation, security selection, and timing.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import numpy as np


class PerformanceAttributionEngine:
    """
    Calculate performance attribution to understand what drives returns.

    Attribution components:
    1. Asset Allocation - Returns from sector/asset class weights
    2. Security Selection - Returns from picking specific stocks within sectors
    3. Timing - Returns from buying/selling at opportune times
    """

    def __init__(self):
        pass

    def calculate_attribution(
        self,
        portfolio_return: float,
        benchmark_return: float,
        portfolio_weights: Dict[str, float],
        benchmark_weights: Dict[str, float],
        sector_returns: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate Brinson attribution (asset allocation vs security selection).

        Args:
            portfolio_return: Total portfolio return
            benchmark_return: Benchmark return (e.g., S&P 500)
            portfolio_weights: Sector weights in portfolio
            benchmark_weights: Sector weights in benchmark
            sector_returns: Returns by sector

        Returns:
            Dict with allocation_effect, selection_effect, interaction_effect
        """
        allocation_effect = 0.0
        selection_effect = 0.0
        interaction_effect = 0.0

        # Get all sectors
        all_sectors = set(portfolio_weights.keys()) | set(benchmark_weights.keys())

        for sector in all_sectors:
            wp = portfolio_weights.get(sector, 0.0)  # Portfolio weight
            wb = benchmark_weights.get(sector, 0.0)  # Benchmark weight
            rs = sector_returns.get(sector, 0.0)  # Sector return

            # Allocation effect: (Portfolio weight - Benchmark weight) × (Sector return - Benchmark return)
            allocation_effect += (wp - wb) * (rs - benchmark_return)

            # Selection effect: Benchmark weight × (Portfolio return in sector - Sector return)
            # Simplified: assuming portfolio return in sector ≈ sector return for now
            # In production, would track actual returns per sector in portfolio

            # Interaction effect: (Portfolio weight - Benchmark weight) × (Portfolio return - Sector return)
            # Simplified for now

        return {
            "total_return": portfolio_return,
            "benchmark_return": benchmark_return,
            "excess_return": portfolio_return - benchmark_return,
            "allocation_effect": allocation_effect,
            "selection_effect": selection_effect,
            "interaction_effect": interaction_effect,
            "explained_return": allocation_effect + selection_effect + interaction_effect
        }

    def calculate_holdings_based_attribution(
        self,
        start_holdings: List[Dict],
        end_holdings: List[Dict],
        start_date: date,
        end_date: date
    ) -> Dict[str, float]:
        """
        Calculate attribution based on holdings changes.

        Args:
            start_holdings: Holdings at period start
            end_holdings: Holdings at period end
            start_date: Period start
            end_date: Period end

        Returns:
            Attribution breakdown
        """
        # Calculate total return
        start_value = sum(h['market_value'] for h in start_holdings)
        end_value = sum(h['market_value'] for h in end_holdings)

        if start_value == 0:
            return {}

        total_return = (end_value - start_value) / start_value

        # Group by sector
        start_sectors = self._group_by_sector(start_holdings)
        end_sectors = self._group_by_sector(end_holdings)

        # Calculate sector contributions
        sector_contributions = {}
        for sector in set(start_sectors.keys()) | set(end_sectors.keys()):
            start_sector_value = start_sectors.get(sector, 0)
            end_sector_value = end_sectors.get(sector, 0)

            if start_sector_value > 0:
                sector_return = (end_sector_value - start_sector_value) / start_sector_value
                weight = start_sector_value / start_value
                contribution = sector_return * weight
                sector_contributions[sector] = contribution

        return {
            "total_return": total_return,
            "sector_contributions": sector_contributions,
            "top_contributing_sector": max(sector_contributions.items(), key=lambda x: x[1])[0] if sector_contributions else None,
            "bottom_contributing_sector": min(sector_contributions.items(), key=lambda x: x[1])[0] if sector_contributions else None,
        }

    def calculate_agent_attribution(
        self,
        trades: List[Dict],
        period_start: date,
        period_end: date
    ) -> Dict[str, Dict]:
        """
        Attribute returns to specific agent decisions.

        Args:
            trades: List of trades with agent attribution
            period_start: Start date
            period_end: End date

        Returns:
            Dict mapping agent names to their contribution
        """
        agent_contributions = {}

        for trade in trades:
            # Skip trades outside period
            trade_date = datetime.fromisoformat(trade['filled_at']).date() if trade.get('filled_at') else None
            if not trade_date or trade_date < period_start or trade_date > period_end:
                continue

            agent = trade.get('strategy_agent_id', 'unknown')

            # Calculate trade P&L
            if trade['status'] == 'filled':
                # Simplified P&L calculation
                qty = float(trade.get('filled_quantity', 0))
                fill_price = float(trade.get('filled_avg_price', 0))
                current_price = float(trade.get('current_price', fill_price))  # Would need to fetch

                if trade['side'] == 'buy':
                    pnl = qty * (current_price - fill_price)
                else:  # sell
                    pnl = qty * (fill_price - current_price)

                # Add to agent's contribution
                if agent not in agent_contributions:
                    agent_contributions[agent] = {
                        "total_pnl": 0,
                        "trade_count": 0,
                        "winning_trades": 0,
                        "losing_trades": 0
                    }

                agent_contributions[agent]["total_pnl"] += pnl
                agent_contributions[agent]["trade_count"] += 1

                if pnl > 0:
                    agent_contributions[agent]["winning_trades"] += 1
                else:
                    agent_contributions[agent]["losing_trades"] += 1

        # Calculate win rates
        for agent, stats in agent_contributions.items():
            total_trades = stats["trade_count"]
            stats["win_rate"] = stats["winning_trades"] / total_trades if total_trades > 0 else 0

        return agent_contributions

    def calculate_timing_attribution(
        self,
        trades: List[Dict],
        benchmark_prices: Dict[date, float]
    ) -> float:
        """
        Calculate timing attribution (buying low, selling high).

        Args:
            trades: List of trades
            benchmark_prices: Dict mapping dates to benchmark prices

        Returns:
            Timing effect as percentage
        """
        # Simplified timing analysis
        # Compare trade prices to average prices over period

        if not trades:
            return 0.0

        avg_benchmark = sum(benchmark_prices.values()) / len(benchmark_prices)

        good_timing = 0
        bad_timing = 0

        for trade in trades:
            if trade['status'] != 'filled':
                continue

            trade_date = datetime.fromisoformat(trade['filled_at']).date() if trade.get('filled_at') else None
            if not trade_date or trade_date not in benchmark_prices:
                continue

            benchmark_on_trade_date = benchmark_prices[trade_date]

            # Buy when benchmark is below average = good timing
            # Sell when benchmark is above average = good timing
            if trade['side'] == 'buy':
                if benchmark_on_trade_date < avg_benchmark:
                    good_timing += 1
                else:
                    bad_timing += 1
            else:  # sell
                if benchmark_on_trade_date > avg_benchmark:
                    good_timing += 1
                else:
                    bad_timing += 1

        total_trades = good_timing + bad_timing
        if total_trades == 0:
            return 0.0

        timing_score = (good_timing - bad_timing) / total_trades
        return timing_score

    def generate_performance_report(
        self,
        portfolio_id: str,
        period_start: date,
        period_end: date,
        portfolio_data: Dict,
        trades: List[Dict],
        benchmark_data: Dict
    ) -> Dict:
        """
        Generate comprehensive performance report.

        Args:
            portfolio_id: Portfolio identifier
            period_start: Report start date
            period_end: Report end date
            portfolio_data: Portfolio metrics
            trades: Trade history
            benchmark_data: Benchmark comparison data

        Returns:
            Complete performance report
        """
        # Calculate returns
        start_value = float(portfolio_data.get('start_value', 0))
        end_value = float(portfolio_data.get('end_value', 0))
        portfolio_return = (end_value - start_value) / start_value if start_value > 0 else 0

        benchmark_return = float(benchmark_data.get('return', 0))

        # Agent attribution
        agent_attr = self.calculate_agent_attribution(trades, period_start, period_end)

        # Calculate metrics
        sharpe = portfolio_data.get('sharpe_ratio', 0)
        max_dd = portfolio_data.get('max_drawdown', 0)
        volatility = portfolio_data.get('volatility', 0)

        # Top/bottom performers
        positions = portfolio_data.get('positions', [])
        if positions:
            sorted_positions = sorted(positions, key=lambda x: x.get('unrealized_pl_pct', 0), reverse=True)
            top_performers = sorted_positions[:5]
            bottom_performers = sorted_positions[-5:]
        else:
            top_performers = []
            bottom_performers = []

        return {
            "portfolio_id": portfolio_id,
            "period": {
                "start_date": period_start.isoformat(),
                "end_date": period_end.isoformat(),
                "days": (period_end - period_start).days
            },
            "returns": {
                "portfolio_return": portfolio_return,
                "benchmark_return": benchmark_return,
                "excess_return": portfolio_return - benchmark_return,
                "annualized_return": portfolio_return * (365 / (period_end - period_start).days)
            },
            "risk_metrics": {
                "sharpe_ratio": sharpe,
                "max_drawdown": max_dd,
                "volatility": volatility
            },
            "agent_attribution": agent_attr,
            "top_performers": [
                {
                    "symbol": p['symbol'],
                    "return_pct": p.get('unrealized_pl_pct', 0),
                    "contribution": p.get('unrealized_pl', 0)
                }
                for p in top_performers
            ],
            "bottom_performers": [
                {
                    "symbol": p['symbol'],
                    "return_pct": p.get('unrealized_pl_pct', 0),
                    "contribution": p.get('unrealized_pl', 0)
                }
                for p in bottom_performers
            ],
            "generated_at": datetime.utcnow().isoformat()
        }

    def _group_by_sector(self, holdings: List[Dict]) -> Dict[str, float]:
        """Group holdings by sector and sum values"""
        sectors = {}
        for holding in holdings:
            sector = holding.get('sector', 'Other')
            value = holding.get('market_value', 0)
            sectors[sector] = sectors.get(sector, 0) + value
        return sectors


# Global instance
performance_attribution = PerformanceAttributionEngine()
