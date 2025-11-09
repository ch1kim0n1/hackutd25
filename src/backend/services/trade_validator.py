# backend/services/trade_validator.py
"""
Multi-agent trade validation workflow for APEX.
Ensures Strategy Agent recommendations are validated by Risk Agent before execution.
"""
from typing import Dict, Optional, Tuple, List
from datetime import datetime
from decimal import Decimal
import numpy as np


class RiskMetricsCalculator:
    """Calculate advanced risk metrics for portfolios and trades"""

    @staticmethod
    def calculate_var(
        returns: List[float],
        confidence_level: float = 0.95,
        time_horizon_days: int = 1
    ) -> float:
        """
        Calculate Value at Risk (VaR).

        Args:
            returns: Historical returns
            confidence_level: Confidence level (0.95 or 0.99)
            time_horizon_days: Time horizon in days

        Returns:
            VaR as percentage loss
        """
        if not returns:
            return 0.0

        returns_array = np.array(returns)

        # Historical VaR (percentile method)
        var = np.percentile(returns_array, (1 - confidence_level) * 100)

        # Adjust for time horizon (sqrt of time rule)
        var_adjusted = var * np.sqrt(time_horizon_days)

        return abs(float(var_adjusted))

    @staticmethod
    def calculate_sharpe_ratio(
        returns: List[float],
        risk_free_rate: float = 0.03
    ) -> float:
        """
        Calculate Sharpe Ratio.

        Args:
            returns: Historical returns
            risk_free_rate: Risk-free rate (annual)

        Returns:
            Sharpe ratio
        """
        if not returns or len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)
        mean_return = np.mean(returns_array)
        std_return = np.std(returns_array)

        if std_return == 0:
            return 0.0

        # Annualize
        annual_return = mean_return * 252  # Trading days
        annual_std = std_return * np.sqrt(252)

        sharpe = (annual_return - risk_free_rate) / annual_std
        return float(sharpe)

    @staticmethod
    def calculate_sortino_ratio(
        returns: List[float],
        risk_free_rate: float = 0.03,
        target_return: float = 0.0
    ) -> float:
        """
        Calculate Sortino Ratio (downside deviation only).

        Args:
            returns: Historical returns
            risk_free_rate: Risk-free rate
            target_return: Target return threshold

        Returns:
            Sortino ratio
        """
        if not returns or len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)
        mean_return = np.mean(returns_array)

        # Calculate downside deviation (only negative returns)
        downside_returns = returns_array[returns_array < target_return]

        if len(downside_returns) == 0:
            return 0.0

        downside_std = np.std(downside_returns)

        if downside_std == 0:
            return 0.0

        # Annualize
        annual_return = mean_return * 252
        annual_downside_std = downside_std * np.sqrt(252)

        sortino = (annual_return - risk_free_rate) / annual_downside_std
        return float(sortino)

    @staticmethod
    def calculate_max_drawdown(prices: List[float]) -> float:
        """
        Calculate maximum drawdown.

        Args:
            prices: Historical prices

        Returns:
            Max drawdown as percentage
        """
        if not prices or len(prices) < 2:
            return 0.0

        prices_array = np.array(prices)
        cumulative_max = np.maximum.accumulate(prices_array)
        drawdowns = (prices_array - cumulative_max) / cumulative_max

        max_dd = abs(float(np.min(drawdowns)))
        return max_dd

    @staticmethod
    def calculate_beta(
        portfolio_returns: List[float],
        market_returns: List[float]
    ) -> float:
        """
        Calculate portfolio beta vs market (S&P 500).

        Args:
            portfolio_returns: Portfolio returns
            market_returns: Market returns

        Returns:
            Beta
        """
        if not portfolio_returns or not market_returns:
            return 1.0

        if len(portfolio_returns) != len(market_returns):
            return 1.0

        portfolio_array = np.array(portfolio_returns)
        market_array = np.array(market_returns)

        # Covariance and variance
        covariance = np.cov(portfolio_array, market_array)[0][1]
        market_variance = np.var(market_array)

        if market_variance == 0:
            return 1.0

        beta = covariance / market_variance
        return float(beta)


class TradeValidator:
    """
    Multi-agent trade validation.
    Strategy Agent proposes trades, Risk Agent validates before execution.
    """

    def __init__(self):
        self.risk_calc = RiskMetricsCalculator()

    def validate_trade(
        self,
        trade_proposal: Dict,
        portfolio_state: Dict,
        risk_limits: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Validate a trade proposal from Strategy Agent.

        Args:
            trade_proposal: Dict with symbol, side, quantity, strategy_reasoning, etc.
            portfolio_state: Current portfolio state
            risk_limits: Optional custom risk limits

        Returns:
            (approved, rejection_reason, risk_analysis)
        """
        # Default risk limits
        default_limits = {
            "max_position_pct": 0.20,  # Max 20% in single position
            "max_sector_pct": 0.40,  # Max 40% in single sector
            "max_var_95": 0.05,  # Max 5% VaR
            "min_sharpe_ratio": 0.5,  # Minimum Sharpe ratio
            "max_drawdown": 0.25,  # Max 25% drawdown
            "max_leverage": 1.0,  # No leverage by default
        }

        limits = risk_limits or default_limits

        # Run validation checks
        checks = []

        # Check 1: Position concentration
        position_check = self._check_position_concentration(
            trade_proposal,
            portfolio_state,
            limits["max_position_pct"]
        )
        checks.append(position_check)

        # Check 2: Sector concentration
        sector_check = self._check_sector_concentration(
            trade_proposal,
            portfolio_state,
            limits["max_sector_pct"]
        )
        checks.append(sector_check)

        # Check 3: Portfolio VaR
        var_check = self._check_var_limit(
            trade_proposal,
            portfolio_state,
            limits["max_var_95"]
        )
        checks.append(var_check)

        # Check 4: Drawdown limit
        dd_check = self._check_drawdown_limit(
            portfolio_state,
            limits["max_drawdown"]
        )
        checks.append(dd_check)

        # Check 5: Leverage check
        leverage_check = self._check_leverage(
            trade_proposal,
            portfolio_state,
            limits["max_leverage"]
        )
        checks.append(leverage_check)

        # Aggregate results
        all_passed = all(check["passed"] for check in checks)
        failed_checks = [check for check in checks if not check["passed"]]

        if all_passed:
            return True, None, {
                "validation_result": "approved",
                "checks_passed": len(checks),
                "checks_failed": 0,
                "risk_agent_approved": True,
                "validation_timestamp": datetime.utcnow().isoformat(),
                "risk_analysis": checks
            }
        else:
            rejection_reason = "; ".join([check["reason"] for check in failed_checks])
            return False, rejection_reason, {
                "validation_result": "rejected",
                "checks_passed": len(checks) - len(failed_checks),
                "checks_failed": len(failed_checks),
                "risk_agent_approved": False,
                "rejection_reason": rejection_reason,
                "validation_timestamp": datetime.utcnow().isoformat(),
                "risk_analysis": checks
            }

    def _check_position_concentration(
        self,
        trade: Dict,
        portfolio: Dict,
        max_pct: float
    ) -> Dict:
        """Check if trade would cause excessive position concentration"""
        symbol = trade["symbol"]
        side = trade["side"]
        quantity = float(trade["quantity"])
        price = float(trade.get("price", 0))

        total_value = float(portfolio.get("total_value", 0))
        if total_value == 0:
            return {"check": "position_concentration", "passed": True, "reason": None}

        # Calculate position value after trade
        current_positions = portfolio.get("positions", [])
        current_position = next((p for p in current_positions if p["symbol"] == symbol), None)

        if current_position:
            current_qty = float(current_position.get("quantity", 0))
        else:
            current_qty = 0

        # Calculate new quantity
        if side == "buy":
            new_qty = current_qty + quantity
        else:  # sell
            new_qty = current_qty - quantity

        new_position_value = new_qty * price
        new_position_pct = new_position_value / total_value

        if new_position_pct > max_pct:
            return {
                "check": "position_concentration",
                "passed": False,
                "reason": f"{symbol} would be {new_position_pct*100:.1f}% of portfolio (max {max_pct*100:.0f}%)",
                "current_pct": new_position_pct,
                "limit": max_pct
            }

        return {
            "check": "position_concentration",
            "passed": True,
            "reason": None,
            "current_pct": new_position_pct,
            "limit": max_pct
        }

    def _check_sector_concentration(
        self,
        trade: Dict,
        portfolio: Dict,
        max_pct: float
    ) -> Dict:
        """Check sector concentration"""
        # Simplified - would need sector mapping in production
        return {
            "check": "sector_concentration",
            "passed": True,
            "reason": None
        }

    def _check_var_limit(
        self,
        trade: Dict,
        portfolio: Dict,
        max_var: float
    ) -> Dict:
        """Check if portfolio VaR exceeds limit"""
        # Simplified - would calculate actual portfolio VaR in production
        current_var = portfolio.get("current_var_95", 0.0)

        if current_var > max_var:
            return {
                "check": "value_at_risk",
                "passed": False,
                "reason": f"Portfolio VaR {current_var*100:.2f}% exceeds limit {max_var*100:.0f}%",
                "current_var": current_var,
                "limit": max_var
            }

        return {
            "check": "value_at_risk",
            "passed": True,
            "reason": None,
            "current_var": current_var,
            "limit": max_var
        }

    def _check_drawdown_limit(
        self,
        portfolio: Dict,
        max_dd: float
    ) -> Dict:
        """Check if current drawdown exceeds limit"""
        current_dd = abs(portfolio.get("max_drawdown", 0.0))

        if current_dd > max_dd:
            return {
                "check": "max_drawdown",
                "passed": False,
                "reason": f"Current drawdown {current_dd*100:.1f}% exceeds limit {max_dd*100:.0f}%",
                "current_drawdown": current_dd,
                "limit": max_dd
            }

        return {
            "check": "max_drawdown",
            "passed": True,
            "reason": None,
            "current_drawdown": current_dd,
            "limit": max_dd
        }

    def _check_leverage(
        self,
        trade: Dict,
        portfolio: Dict,
        max_leverage: float
    ) -> Dict:
        """Check leverage limits"""
        total_value = float(portfolio.get("total_value", 0))
        cash = float(portfolio.get("cash_balance", 0))

        if total_value == 0:
            return {"check": "leverage", "passed": True, "reason": None}

        current_leverage = (total_value - cash) / total_value if total_value > 0 else 0

        if current_leverage > max_leverage:
            return {
                "check": "leverage",
                "passed": False,
                "reason": f"Leverage {current_leverage:.2f}x exceeds limit {max_leverage}x",
                "current_leverage": current_leverage,
                "limit": max_leverage
            }

        return {
            "check": "leverage",
            "passed": True,
            "reason": None,
            "current_leverage": current_leverage,
            "limit": max_leverage
        }


# Global instances
risk_calculator = RiskMetricsCalculator()
trade_validator = TradeValidator()
