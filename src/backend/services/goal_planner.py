# backend/services/goal_planner.py
"""
Goal Planning service for APEX.
Handles compound interest calculations, scenario projections, and goal validation.
"""
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
import numpy as np


class GoalPlanner:
    """
    Financial goal planning with compound interest calculations and Monte Carlo simulations.
    """

    def __init__(self):
        """Initialize goal planner"""
        pass

    def calculate_compound_interest(
        self,
        principal: float,
        monthly_contribution: float,
        annual_return: float,
        years: int,
        compounding_frequency: str = "monthly"
    ) -> Dict[str, float]:
        """
        Calculate compound interest with regular contributions.

        Formula: FV = P(1 + r/n)^(nt) + PMT × [((1 + r/n)^(nt) - 1) / (r/n)]

        Args:
            principal: Initial investment
            monthly_contribution: Monthly contribution amount
            annual_return: Expected annual return (e.g., 0.07 for 7%)
            years: Investment period in years
            compounding_frequency: How often interest compounds

        Returns:
            Dict with future_value, total_contributed, total_interest
        """
        # Convert compounding frequency to periods per year
        periods_per_year = {
            "monthly": 12,
            "quarterly": 4,
            "annually": 1,
            "daily": 365
        }
        n = periods_per_year.get(compounding_frequency, 12)

        # Rate per period
        r = annual_return / n

        # Total periods
        t = years * n

        # Future value of principal
        fv_principal = principal * ((1 + r) ** t)

        # Future value of contributions (annuity)
        if monthly_contribution > 0:
            # Convert monthly to per-period contribution
            if compounding_frequency == "monthly":
                pmt = monthly_contribution
            else:
                # Adjust contribution to match compounding frequency
                pmt = monthly_contribution * (12 / n)

            fv_contributions = pmt * (((1 + r) ** t - 1) / r)
        else:
            fv_contributions = 0

        future_value = fv_principal + fv_contributions
        total_contributed = principal + (monthly_contribution * 12 * years)
        total_interest = future_value - total_contributed

        return {
            "future_value": round(future_value, 2),
            "total_contributed": round(total_contributed, 2),
            "total_interest": round(total_interest, 2),
            "principal_growth": round(fv_principal - principal, 2),
            "contribution_growth": round(fv_contributions, 2)
        }

    def calculate_required_monthly_contribution(
        self,
        target_amount: float,
        initial_investment: float,
        annual_return: float,
        years: int
    ) -> float:
        """
        Calculate required monthly contribution to reach a goal.

        Args:
            target_amount: Target future value
            initial_investment: Starting amount
            annual_return: Expected annual return
            years: Time horizon in years

        Returns:
            Required monthly contribution
        """
        n = 12  # Monthly compounding
        r = annual_return / n
        t = years * n

        # Future value of initial investment
        fv_principal = initial_investment * ((1 + r) ** t)

        # Remaining amount needed from contributions
        remaining = target_amount - fv_principal

        if remaining <= 0:
            return 0  # Initial investment is enough

        # Solve for PMT in annuity formula
        # remaining = PMT × [((1 + r)^t - 1) / r]
        monthly_contribution = remaining * r / (((1 + r) ** t) - 1)

        return round(monthly_contribution, 2)

    def generate_scenarios(
        self,
        principal: float,
        monthly_contribution: float,
        years: int,
        conservative_return: float = 0.05,
        moderate_return: float = 0.07,
        aggressive_return: float = 0.10
    ) -> Dict[str, Dict]:
        """
        Generate three scenarios: conservative, moderate, aggressive.

        Args:
            principal: Initial investment
            monthly_contribution: Monthly contributions
            years: Time horizon
            conservative_return: Conservative annual return assumption
            moderate_return: Moderate annual return assumption
            aggressive_return: Aggressive annual return assumption

        Returns:
            Dict with three scenario projections
        """
        scenarios = {}

        scenarios["conservative"] = self.calculate_compound_interest(
            principal, monthly_contribution, conservative_return, years
        )

        scenarios["moderate"] = self.calculate_compound_interest(
            principal, monthly_contribution, moderate_return, years
        )

        scenarios["aggressive"] = self.calculate_compound_interest(
            principal, monthly_contribution, aggressive_return, years
        )

        return scenarios

    def monte_carlo_simulation(
        self,
        principal: float,
        monthly_contribution: float,
        years: int,
        expected_return: float = 0.07,
        volatility: float = 0.15,
        num_simulations: int = 10000
    ) -> Dict[str, float]:
        """
        Run Monte Carlo simulation to estimate probability of reaching goal.

        Args:
            principal: Initial investment
            monthly_contribution: Monthly contributions
            years: Time horizon
            expected_return: Expected annual return
            volatility: Annual volatility (standard deviation)
            num_simulations: Number of simulation runs

        Returns:
            Dict with percentile outcomes
        """
        months = years * 12
        monthly_return = expected_return / 12
        monthly_volatility = volatility / math.sqrt(12)

        # Run simulations
        final_values = []

        for _ in range(num_simulations):
            portfolio_value = principal

            for month in range(months):
                # Random return for this month (log-normal distribution)
                random_return = np.random.normal(monthly_return, monthly_volatility)

                # Apply return
                portfolio_value = portfolio_value * (1 + random_return)

                # Add contribution
                portfolio_value += monthly_contribution

            final_values.append(portfolio_value)

        # Calculate percentiles
        final_values = np.array(final_values)

        return {
            "p10": round(np.percentile(final_values, 10), 2),  # 10th percentile (worst case)
            "p25": round(np.percentile(final_values, 25), 2),  # 25th percentile
            "p50": round(np.percentile(final_values, 50), 2),  # Median
            "p75": round(np.percentile(final_values, 75), 2),  # 75th percentile
            "p90": round(np.percentile(final_values, 90), 2),  # 90th percentile (best case)
            "mean": round(np.mean(final_values), 2),
            "std": round(np.std(final_values), 2)
        }

    def calculate_success_probability(
        self,
        target_amount: float,
        principal: float,
        monthly_contribution: float,
        years: int,
        expected_return: float = 0.07,
        volatility: float = 0.15,
        num_simulations: int = 10000
    ) -> float:
        """
        Calculate probability of reaching goal using Monte Carlo simulation.

        Args:
            target_amount: Target future value
            principal: Initial investment
            monthly_contribution: Monthly contributions
            years: Time horizon
            expected_return: Expected annual return
            volatility: Annual volatility
            num_simulations: Number of simulations

        Returns:
            Probability (0-1) of reaching or exceeding target
        """
        months = years * 12
        monthly_return = expected_return / 12
        monthly_volatility = volatility / math.sqrt(12)

        successes = 0

        for _ in range(num_simulations):
            portfolio_value = principal

            for month in range(months):
                random_return = np.random.normal(monthly_return, monthly_volatility)
                portfolio_value = portfolio_value * (1 + random_return)
                portfolio_value += monthly_contribution

            if portfolio_value >= target_amount:
                successes += 1

        return round(successes / num_simulations, 4)

    def generate_milestones(
        self,
        target_amount: float,
        years: int,
        num_milestones: int = 5
    ) -> List[Dict]:
        """
        Generate intermediate milestones for a goal.

        Args:
            target_amount: Final target
            years: Time horizon
            num_milestones: Number of milestones to create

        Returns:
            List of milestone dicts
        """
        milestones = []
        years_per_milestone = years / num_milestones

        for i in range(1, num_milestones + 1):
            milestone_years = years_per_milestone * i
            milestone_amount = (target_amount / num_milestones) * i
            milestone_date = date.today().replace(
                year=date.today().year + int(milestone_years)
            )

            milestones.append({
                "milestone_number": i,
                "target_amount": round(milestone_amount, 2),
                "target_date": milestone_date.isoformat(),
                "years_from_now": milestone_years,
                "achieved": False
            })

        return milestones

    def calculate_inflation_adjusted_target(
        self,
        target_amount: float,
        years: int,
        inflation_rate: float = 0.03
    ) -> float:
        """
        Adjust target for inflation.

        Args:
            target_amount: Target in today's dollars
            years: Years until goal
            inflation_rate: Annual inflation rate (e.g., 0.03 for 3%)

        Returns:
            Inflation-adjusted target
        """
        adjusted_target = target_amount * ((1 + inflation_rate) ** years)
        return round(adjusted_target, 2)

    def calculate_time_to_goal(
        self,
        target_amount: float,
        principal: float,
        monthly_contribution: float,
        annual_return: float
    ) -> float:
        """
        Calculate years needed to reach goal.

        Args:
            target_amount: Target future value
            principal: Initial investment
            monthly_contribution: Monthly contributions
            annual_return: Expected annual return

        Returns:
            Years to reach goal
        """
        if monthly_contribution == 0:
            # Simple compound interest formula
            if principal == 0:
                return float('inf')
            years = math.log(target_amount / principal) / math.log(1 + annual_return)
            return round(years, 2)

        # With contributions, solve iteratively
        r = annual_return / 12
        current_value = principal
        months = 0
        max_months = 1200  # 100 years max

        while current_value < target_amount and months < max_months:
            current_value = current_value * (1 + r) + monthly_contribution
            months += 1

        return round(months / 12, 2)

    def analyze_goal(
        self,
        goal_data: Dict
    ) -> Dict:
        """
        Comprehensive goal analysis with all calculations.

        Args:
            goal_data: Dict with target_amount, initial_investment, monthly_contribution,
                       years_to_goal, expected_return, etc.

        Returns:
            Complete goal analysis
        """
        target = goal_data['target_amount']
        principal = goal_data.get('initial_investment', 0)
        monthly = goal_data.get('monthly_contribution', 0)
        years = goal_data.get('years_to_goal', 10)
        expected_return = goal_data.get('expected_return', 0.07)
        volatility = goal_data.get('volatility', 0.15)

        # Generate scenarios
        scenarios = self.generate_scenarios(
            principal,
            monthly,
            years,
            conservative_return=goal_data.get('conservative_return', 0.05),
            moderate_return=expected_return,
            aggressive_return=goal_data.get('aggressive_return', 0.10)
        )

        # Monte Carlo simulation
        mc_results = self.monte_carlo_simulation(
            principal, monthly, years, expected_return, volatility
        )

        # Success probability
        success_prob = self.calculate_success_probability(
            target, principal, monthly, years, expected_return, volatility
        )

        # Required monthly contribution
        required_monthly = self.calculate_required_monthly_contribution(
            target, principal, expected_return, years
        )

        # Milestones
        milestones = self.generate_milestones(target, years)

        # Inflation adjustment
        inflation_adjusted = self.calculate_inflation_adjusted_target(target, years)

        return {
            "scenarios": scenarios,
            "monte_carlo": mc_results,
            "success_probability": success_prob,
            "required_monthly_contribution": required_monthly,
            "current_monthly_contribution": monthly,
            "contribution_gap": round(required_monthly - monthly, 2),
            "milestones": milestones,
            "inflation_adjusted_target": inflation_adjusted,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }


# Global instance
goal_planner = GoalPlanner()
