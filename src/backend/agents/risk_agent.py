"""
APEX Risk Agent
Validates strategies using Monte Carlo simulations and enforces risk constraints.
Uses GPU-accelerated simulations to assess portfolio risk in real-time.
"""

from openai import OpenAI
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    print("⚠️  CuPy not available - falling back to NumPy (CPU). Install cupy for GPU acceleration.")


class RiskAgent:
    """
    Risk assessment and validation agent for APEX multi-agent system.
    
    Responsibilities:
    - Run Monte Carlo simulations to assess portfolio risk
    - Validate Strategy Agent recommendations against risk constraints
    - Calculate probability of meeting user goals
    - Identify potential portfolio vulnerabilities
    - Approve or reject proposed trades
    - Suggest risk-adjusted alternatives if needed
    """
    
    def __init__(
        self,
        openrouter_api_key: str,
        enable_logging: bool = True,
        model: str = "nvidia/llama-3.1-nemotron-70b-instruct",
        use_gpu: bool = True,
        num_simulations: int = 10000
    ):
        """
        Initialize Risk Agent.
        
        Args:
            openrouter_api_key: API key from openrouter.ai
            enable_logging: Print status messages
            model: NVIDIA model to use (same as other agents)
            use_gpu: Use GPU acceleration if available (much faster)
            num_simulations: Number of Monte Carlo simulations to run
        """
        # Initialize OpenRouter client
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )
        
        self.model = model
        self.logging_enabled = enable_logging
        self.num_simulations = num_simulations
        
        # Determine if we can use GPU
        self.use_gpu = use_gpu and GPU_AVAILABLE
        self.np = cp if self.use_gpu else np
        
        # Historical market statistics (these should ideally be updated from real data)
        # These are approximate long-term statistics
        self.market_stats = self._get_default_market_stats()
        
        self.log(f"✅ Risk Agent initialized with {self._get_model_name()}")
        self.log(f"🖥️  Computing: {'GPU (CuPy)' if self.use_gpu else 'CPU (NumPy)'}")
        self.log(f"🎲 Simulations per analysis: {num_simulations:,}")
    
    def _get_model_name(self) -> str:
        """Get human-readable model name"""
        if '70b' in self.model.lower():
            return "NVIDIA Nemotron 70B"
        elif '49b' in self.model.lower():
            return "NVIDIA Nemotron 49B"
        elif '9b' in self.model.lower():
            return "NVIDIA Nemotron 9B"
        return self.model
    
    def log(self, message: str):
        """Print status message if logging enabled"""
        if self.logging_enabled:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ⚠️  Risk Agent: {message}")
    
    # ========================================
    # MARKET STATISTICS
    # ========================================
    
    def _get_default_market_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get historical statistics for different asset classes.
        
        These are approximate long-term averages.
        In production, these would be calculated from real historical data.
        
        Returns:
            Dict mapping asset symbols to {'mean_return', 'volatility'}
        """
        return {
            # US Equities
            'SPY': {'mean_return': 0.10, 'volatility': 0.18},      # S&P 500
            'QQQ': {'mean_return': 0.12, 'volatility': 0.22},      # Nasdaq (higher risk/return)
            'IWM': {'mean_return': 0.09, 'volatility': 0.21},      # Small cap
            'VTI': {'mean_return': 0.10, 'volatility': 0.18},      # Total market
            'VOO': {'mean_return': 0.10, 'volatility': 0.18},      # S&P 500
            
            # Bonds
            'TLT': {'mean_return': 0.04, 'volatility': 0.14},      # Long-term Treasury
            'IEF': {'mean_return': 0.03, 'volatility': 0.08},      # Medium-term Treasury
            'AGG': {'mean_return': 0.03, 'volatility': 0.05},      # Aggregate bonds
            'BND': {'mean_return': 0.03, 'volatility': 0.05},      # Total bond
            'LQD': {'mean_return': 0.04, 'volatility': 0.08},      # Corporate bonds
            
            # Commodities
            'GLD': {'mean_return': 0.05, 'volatility': 0.16},      # Gold
            'SLV': {'mean_return': 0.04, 'volatility': 0.25},      # Silver
            'DBC': {'mean_return': 0.02, 'volatility': 0.20},      # Commodities
            'USO': {'mean_return': 0.01, 'volatility': 0.35},      # Oil (very volatile)
            
            # International
            'VEA': {'mean_return': 0.07, 'volatility': 0.17},      # Developed markets
            'VWO': {'mean_return': 0.08, 'volatility': 0.23},      # Emerging markets
            'EFA': {'mean_return': 0.07, 'volatility': 0.17},      # EAFE
            
            # Real Estate
            'VNQ': {'mean_return': 0.09, 'volatility': 0.20},      # US REIT
            'IYR': {'mean_return': 0.09, 'volatility': 0.21},      # Real estate
            
            # Individual stocks (more volatile than diversified ETFs)
            'AAPL': {'mean_return': 0.25, 'volatility': 0.35},     # High growth, high volatility
            'MSFT': {'mean_return': 0.22, 'volatility': 0.32},
            'GOOGL': {'mean_return': 0.20, 'volatility': 0.30},
            'TSLA': {'mean_return': 0.30, 'volatility': 0.60},     # Very high volatility
            'NVDA': {'mean_return': 0.35, 'volatility': 0.55},     # Tech growth stock
            
            # Cash (risk-free)
            'cash': {'mean_return': 0.03, 'volatility': 0.00}      # Cash has no volatility
        }
    
    def update_market_stats(self, symbol: str, mean_return: float, volatility: float):
        """
        Update statistics for a specific asset (useful for custom assets).
        
        Args:
            symbol: Asset ticker symbol
            mean_return: Annual expected return (e.g., 0.10 for 10%)
            volatility: Annual volatility/standard deviation (e.g., 0.18 for 18%)
        """
        self.market_stats[symbol] = {
            'mean_return': mean_return,
            'volatility': volatility
        }
        self.log(f"📊 Updated stats for {symbol}: {mean_return*100:.1f}% return, {volatility*100:.1f}% volatility")
    
    # ========================================
    # MONTE CARLO SIMULATION
    # ========================================
    
    def run_monte_carlo(
        self,
        portfolio_allocation: Dict[str, float],
        initial_value: float,
        time_horizon_years: float = 1.0
    ) -> Dict:
        """
        Run Monte Carlo simulation on a portfolio allocation.
        
        This is the core risk assessment engine.
        
        Args:
            portfolio_allocation: Dict of {symbol: weight}
                Example: {'SPY': 0.60, 'TLT': 0.30, 'GLD': 0.10}
            initial_value: Starting portfolio value in dollars
            time_horizon_years: How many years to simulate (default 1 year)
        
        Returns:
            {
                'median_outcome': 105000,           # Median final value
                'percentile_5': 85000,              # Worst 5% (95% chance better)
                'percentile_95': 125000,            # Best 5% (5% chance better)
                'mean_outcome': 108000,             # Average outcome
                'std_outcome': 18000,               # Standard deviation
                'max_drawdown': 0.15,               # Worst intra-period loss
                'prob_loss': 0.23,                  # Probability of losing money
                'prob_gain_10pct': 0.65,            # Probability of 10%+ gain
                'sharpe_ratio': 0.56,               # Risk-adjusted return
                'var_95': 0.12,                     # Value at Risk (95% confidence)
                'all_outcomes': [array of results]  # For visualization
            }
        """
        self.log(f"🎲 Running {self.num_simulations:,} Monte Carlo simulations...")
        
        # Calculate portfolio statistics from weighted assets
        portfolio_stats = self._calculate_portfolio_stats(portfolio_allocation)
        
        # Number of trading days
        trading_days = int(time_horizon_years * 252)
        
        # Convert annual stats to daily
        daily_return = portfolio_stats['mean_return'] / 252
        daily_volatility = portfolio_stats['volatility'] / np.sqrt(252)
        
        # Generate random returns for all simulations
        # Shape: (num_simulations, trading_days)
        random_returns = self.np.random.normal(
            loc=daily_return,
            scale=daily_volatility,
            size=(self.num_simulations, trading_days)
        )
        
        # Calculate cumulative returns (compound daily returns)
        # Add 1 to returns, take cumulative product, multiply by initial value
        price_paths = initial_value * self.np.cumprod(1 + random_returns, axis=1)
        
        # Final values (last day of each simulation)
        final_values = price_paths[:, -1]
        
        # Convert back to numpy if using GPU
        if self.use_gpu:
            final_values_cpu = cp.asnumpy(final_values)
            price_paths_cpu = cp.asnumpy(price_paths)
        else:
            final_values_cpu = final_values
            price_paths_cpu = price_paths
        
        # Calculate statistics
        median_outcome = float(np.median(final_values_cpu))
        percentile_5 = float(np.percentile(final_values_cpu, 5))
        percentile_95 = float(np.percentile(final_values_cpu, 95))
        mean_outcome = float(np.mean(final_values_cpu))
        std_outcome = float(np.std(final_values_cpu))
        
        # Calculate max drawdown (worst peak-to-trough decline)
        max_drawdown = self._calculate_max_drawdown(price_paths_cpu, initial_value)
        
        # Probability of losing money
        prob_loss = float(np.mean(final_values_cpu < initial_value))
        
        # Probability of 10%+ gain
        prob_gain_10pct = float(np.mean(final_values_cpu >= initial_value * 1.10))
        
        # Sharpe ratio (risk-adjusted return)
        returns_pct = (final_values_cpu / initial_value) - 1
        sharpe_ratio = float(np.mean(returns_pct) / np.std(returns_pct)) if np.std(returns_pct) > 0 else 0
        
        # Value at Risk (95% confidence - worst 5% outcome)
        var_95 = float((initial_value - percentile_5) / initial_value)
        
        self.log(f"✅ Simulation complete: Median outcome ${median_outcome:,.0f}")
        
        return {
            'median_outcome': median_outcome,
            'percentile_5': percentile_5,
            'percentile_95': percentile_95,
            'mean_outcome': mean_outcome,
            'std_outcome': std_outcome,
            'max_drawdown': max_drawdown,
            'prob_loss': prob_loss,
            'prob_gain_10pct': prob_gain_10pct,
            'sharpe_ratio': sharpe_ratio,
            'var_95': var_95,
            'all_outcomes': final_values_cpu,  # For visualization/further analysis
            'simulation_params': {
                'num_simulations': self.num_simulations,
                'time_horizon_years': time_horizon_years,
                'initial_value': initial_value,
                'portfolio_mean_return': portfolio_stats['mean_return'],
                'portfolio_volatility': portfolio_stats['volatility']
            }
        }
    
    def _calculate_portfolio_stats(self, allocation: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate portfolio-level statistics from individual asset allocations.
        
        For simplicity, this assumes assets are uncorrelated.
        In production, you'd use a correlation matrix.
        
        Args:
            allocation: Dict of {symbol: weight}
        
        Returns:
            {'mean_return': 0.085, 'volatility': 0.142}
        """
        portfolio_return = 0.0
        portfolio_variance = 0.0
        
        for symbol, weight in allocation.items():
            if symbol == 'cash':
                symbol = 'cash'
            
            # Get stats for this asset (or use default if unknown)
            if symbol in self.market_stats:
                stats = self.market_stats[symbol]
            else:
                # Unknown asset - use conservative estimate
                self.log(f"⚠️  No stats for {symbol}, using default (10% return, 20% vol)")
                stats = {'mean_return': 0.10, 'volatility': 0.20}
            
            # Weighted return
            portfolio_return += weight * stats['mean_return']
            
            # Weighted variance (simplified - assumes no correlation)
            portfolio_variance += (weight ** 2) * (stats['volatility'] ** 2)
        
        # Portfolio volatility is sqrt of variance
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        return {
            'mean_return': portfolio_return,
            'volatility': portfolio_volatility
        }
    
    def _calculate_max_drawdown(self, price_paths: np.ndarray, initial_value: float) -> float:
        """
        Calculate maximum drawdown across all simulation paths.
        
        Max drawdown = worst peak-to-trough decline
        
        Args:
            price_paths: Array of shape (num_simulations, num_days)
            initial_value: Starting portfolio value
        
        Returns:
            Maximum drawdown as fraction (e.g., 0.25 = 25% max loss)
        """
        # Calculate running maximum for each path
        cumulative_max = np.maximum.accumulate(price_paths, axis=1)
        
        # Calculate drawdown at each point
        drawdowns = (cumulative_max - price_paths) / cumulative_max
        
        # Find worst drawdown across all paths and times
        max_drawdown = float(np.max(drawdowns))
        
        return max_drawdown
    
    # ========================================
    # STRATEGY VALIDATION
    # ========================================
    
    def validate_strategy(
        self,
        strategy: Dict,
        current_portfolio: Dict,
        user_profile: Dict,
        market_report: Dict,
        risk_constraints: Optional[Dict] = None
    ) -> Dict:
        """
        Validate a strategy from Strategy Agent using Monte Carlo analysis.
        
        Args:
            strategy: Output from StrategyAgent.generate_strategy()
            current_portfolio: Current portfolio state
            user_profile: User preferences
            market_report: Market conditions
            risk_constraints: Risk limits to enforce
        
        Returns:
            {
                'approved': True/False,
                'risk_analysis': {...Monte Carlo results...},
                'violations': [...list of constraint violations...],
                'concerns': [...list of risk concerns...],
                'recommendation': "APPROVE" / "MODIFY" / "REJECT",
                'suggested_modifications': [...if not approved...],
                'explanation': "Detailed reasoning...",
                'confidence': 0.85
            }
        """
        self.log("🔍 Validating strategy with Monte Carlo analysis...")
        
        # Run Monte Carlo on proposed allocation
        target_allocation = strategy['target_allocation']
        portfolio_value = current_portfolio['total_value']
        
        risk_analysis = self.run_monte_carlo(
            portfolio_allocation=target_allocation,
            initial_value=portfolio_value,
            time_horizon_years=self._get_time_horizon_years(user_profile)
        )
        
        # Check for constraint violations
        violations = self._check_constraint_violations(
            strategy=strategy,
            risk_analysis=risk_analysis,
            risk_constraints=risk_constraints,
            user_profile=user_profile
        )
        
        # Identify risk concerns
        concerns = self._identify_risk_concerns(
            risk_analysis=risk_analysis,
            market_report=market_report,
            user_profile=user_profile
        )
        
        # Determine recommendation
        if len(violations) == 0 and len(concerns) == 0:
            recommendation = "APPROVE"
            approved = True
        elif len(violations) == 0 and len(concerns) <= 2:
            recommendation = "APPROVE_WITH_CAUTION"
            approved = True
        elif len(violations) <= 1:
            recommendation = "MODIFY"
            approved = False
        else:
            recommendation = "REJECT"
            approved = False
        
        # Get AI explanation
        explanation = self._generate_risk_explanation(
            strategy=strategy,
            risk_analysis=risk_analysis,
            violations=violations,
            concerns=concerns,
            recommendation=recommendation,
            user_profile=user_profile
        )
        
        # Generate modifications if needed
        suggested_modifications = []
        if not approved:
            suggested_modifications = self._suggest_modifications(
                strategy=strategy,
                violations=violations,
                concerns=concerns,
                risk_analysis=risk_analysis
            )
        
        result = {
            'approved': approved,
            'recommendation': recommendation,
            'risk_analysis': risk_analysis,
            'violations': violations,
            'concerns': concerns,
            'suggested_modifications': suggested_modifications,
            'explanation': explanation,
            'confidence': 0.85 if len(violations) == 0 else 0.65,
            'timestamp': datetime.now()
        }
        
        self.log(f"{'✅ APPROVED' if approved else '❌ NOT APPROVED'}: {recommendation}")
        return result
    
    def _get_time_horizon_years(self, user_profile: Dict) -> float:
        """Convert user time horizon to years for simulation"""
        horizon = user_profile.get('time_horizon', 'long-term').lower()
        
        horizon_map = {
            'short-term': 1.0,
            'short term': 1.0,
            'medium-term': 3.0,
            'medium term': 3.0,
            'long-term': 10.0,
            'long term': 10.0
        }
        
        return horizon_map.get(horizon, 5.0)
    
    def _check_constraint_violations(
        self,
        strategy: Dict,
        risk_analysis: Dict,
        risk_constraints: Optional[Dict],
        user_profile: Dict
    ) -> List[str]:
        """
        Check if strategy violates any risk constraints.
        
        Returns list of violation descriptions.
        """
        violations = []
        
        if not risk_constraints:
            return violations
        
        # Check max position size
        if 'max_position_size' in risk_constraints:
            max_allowed = risk_constraints['max_position_size']
            for symbol, weight in strategy['target_allocation'].items():
                if symbol != 'cash' and weight > max_allowed:
                    violations.append(
                        f"Position size violation: {symbol} at {weight*100:.1f}% exceeds max {max_allowed*100:.1f}%"
                    )
        
        # Check max drawdown
        if 'max_drawdown_limit' in risk_constraints:
            max_allowed_dd = risk_constraints['max_drawdown_limit']
            simulated_dd = risk_analysis['max_drawdown']
            if simulated_dd > max_allowed_dd:
                violations.append(
                    f"Max drawdown violation: Simulated {simulated_dd*100:.1f}% exceeds limit {max_allowed_dd*100:.1f}%"
                )
        
        # Check min cash reserve
        if 'min_cash_reserve' in risk_constraints:
            min_cash = risk_constraints['min_cash_reserve']
            actual_cash = strategy['target_allocation'].get('cash', 0)
            if actual_cash < min_cash:
                violations.append(
                    f"Cash reserve violation: {actual_cash*100:.1f}% below minimum {min_cash*100:.1f}%"
                )
        
        # Check Value at Risk
        if 'max_var_95' in risk_constraints:
            max_var = risk_constraints['max_var_95']
            if risk_analysis['var_95'] > max_var:
                violations.append(
                    f"VaR violation: 95% VaR of {risk_analysis['var_95']*100:.1f}% exceeds max {max_var*100:.1f}%"
                )
        
        return violations
    
    def _identify_risk_concerns(
        self,
        risk_analysis: Dict,
        market_report: Dict,
        user_profile: Dict
    ) -> List[str]:
        """
        Identify potential risk concerns (not violations, but warnings).
        """
        concerns = []
        
        # High probability of loss
        if risk_analysis['prob_loss'] > 0.35:
            concerns.append(
                f"High loss probability: {risk_analysis['prob_loss']*100:.1f}% chance of losing money"
            )
        
        # Low Sharpe ratio (poor risk-adjusted returns)
        if risk_analysis['sharpe_ratio'] < 0.5:
            concerns.append(
                f"Low Sharpe ratio: {risk_analysis['sharpe_ratio']:.2f} suggests poor risk-adjusted returns"
            )
        
        # High VIX and risky allocation
        market_vix = market_report['market_data'].get('vix', 15)
        if market_vix > 25 and risk_analysis['volatility'] > 0.20:
            concerns.append(
                f"Risky timing: VIX at {market_vix:.1f} suggests caution, but portfolio volatility is {risk_analysis['simulation_params']['portfolio_volatility']*100:.1f}%"
            )
        
        # Risk tolerance mismatch
        risk_tolerance = user_profile.get('risk_tolerance', 'moderate').lower()
        portfolio_vol = risk_analysis['simulation_params']['portfolio_volatility']
        
        if risk_tolerance == 'conservative' and portfolio_vol > 0.12:
            concerns.append(
                f"Risk mismatch: Conservative investor with {portfolio_vol*100:.1f}% volatility portfolio"
            )
        elif risk_tolerance == 'moderate' and portfolio_vol > 0.18:
            concerns.append(
                f"Risk mismatch: Moderate investor with {portfolio_vol*100:.1f}% volatility portfolio"
            )
        
        return concerns
    
    def _suggest_modifications(
        self,
        strategy: Dict,
        violations: List[str],
        concerns: List[str],
        risk_analysis: Dict
    ) -> List[str]:
        """
        Suggest specific modifications to fix violations/concerns.
        """
        modifications = []
        
        for violation in violations:
            if "Position size violation" in violation:
                # Extract symbol from violation message
                symbol = violation.split(":")[1].split("at")[0].strip()
                modifications.append(f"Reduce {symbol} allocation to meet position size limit")
            
            elif "Max drawdown violation" in violation:
                modifications.append("Increase bond/cash allocation to reduce drawdown risk")
            
            elif "Cash reserve violation" in violation:
                modifications.append("Reduce equity positions to maintain minimum cash reserve")
            
            elif "VaR violation" in violation:
                modifications.append("Shift to lower-volatility assets to reduce Value at Risk")
        
        for concern in concerns:
            if "High loss probability" in concern:
                modifications.append("Consider more defensive positioning given loss probability")
            
            elif "Low Sharpe ratio" in concern:
                modifications.append("Improve risk-adjusted returns by diversifying or reducing volatility")
            
            elif "Risky timing" in concern:
                modifications.append("Wait for VIX to decline below 20 before increasing risk")
        
        return modifications
    
    # ========================================
    # AI EXPLANATION GENERATION
    # ========================================
    
    def _generate_risk_explanation(
        self,
        strategy: Dict,
        risk_analysis: Dict,
        violations: List[str],
        concerns: List[str],
        recommendation: str,
        user_profile: Dict
    ) -> str:
        """
        Use NVIDIA AI to generate human-readable risk assessment.
        """
        # Build prompt
        prompt = self._build_risk_explanation_prompt(
            strategy, risk_analysis, violations, concerns, recommendation, user_profile
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are the Risk Agent in APEX. Explain risk analysis in clear, educational terms. Help users understand the safety and potential downsides of their investment strategy."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.6,
                extra_headers={
                    "HTTP-Referer": "https://apex-financial.com",
                    "X-Title": "APEX Risk Agent"
                }
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.log(f"❌ Error generating explanation: {e}")
            return self._generate_fallback_explanation(recommendation, risk_analysis)
    
    def _build_risk_explanation_prompt(
        self,
        strategy: Dict,
        risk_analysis: Dict,
        violations: List[str],
        concerns: List[str],
        recommendation: str,
        user_profile: Dict
    ) -> str:
        """Build prompt for risk explanation"""
        
        violations_text = "\n".join(violations) if violations else "None"
        concerns_text = "\n".join(concerns) if concerns else "None"
        
        prompt = f"""You are the Risk Agent. You just ran {risk_analysis['simulation_params']['num_simulations']:,} Monte Carlo simulations on a proposed investment strategy.

**PROPOSED STRATEGY:**
{strategy['strategy_summary']}

**MONTE CARLO SIMULATION RESULTS:**
- Median Outcome: ${risk_analysis['median_outcome']:,.0f}
- Best Case (95th percentile): ${risk_analysis['percentile_95']:,.0f}
- Worst Case (5th percentile): ${risk_analysis['percentile_5']:,.0f}
- Maximum Drawdown: {risk_analysis['max_drawdown']*100:.1f}%
- Probability of Loss: {risk_analysis['prob_loss']*100:.1f}%
- Probability of 10%+ Gain: {risk_analysis['prob_gain_10pct']*100:.1f}%
- Sharpe Ratio: {risk_analysis['sharpe_ratio']:.2f}
- Value at Risk (95%): {risk_analysis['var_95']*100:.1f}%

**CONSTRAINT VIOLATIONS:**
{violations_text}

**RISK CONCERNS:**
{concerns_text}

**YOUR RECOMMENDATION:**
{recommendation}

**USER PROFILE:**
- Risk Tolerance: {user_profile.get('risk_tolerance', 'moderate').title()}
- Experience Level: {user_profile.get('experience_level', 'beginner').title()}

**YOUR TASK:**
Explain your risk assessment in 2-3 paragraphs for this user:

1. Start with your verdict: {recommendation}
2. Explain WHAT the Monte Carlo simulation found (in plain English)
3. Explain WHY you reached this recommendation
4. If there are violations or concerns, explain them clearly
5. Help the user understand the risk/reward tradeoff

Keep it educational and supportive. Use analogies if helpful."""

        return prompt
    
    def _generate_fallback_explanation(self, recommendation: str, risk_analysis: Dict) -> str:
        """Fallback explanation if AI fails"""
        return f"""**{recommendation}**

Based on {risk_analysis['simulation_params']['num_simulations']:,} Monte Carlo simulations:

The median outcome shows your portfolio reaching ${risk_analysis['median_outcome']:,.0f}. However, there's a {risk_analysis['prob_loss']*100:.0f}% chance of losing money, and in the worst 5% of scenarios, you could see your portfolio drop to ${risk_analysis['percentile_5']:,.0f}.

The maximum simulated drawdown is {risk_analysis['max_drawdown']*100:.1f}%, meaning your portfolio could temporarily lose that much value during market downturns.

Recommendation: {recommendation.replace('_', ' ')}"""
    
    # ========================================
    # DISPLAY FORMATTING
    # ========================================
    
    def get_validation_summary(self, validation: Dict) -> str:
        """
        Format validation results for display.
        """
        risk = validation['risk_analysis']
        
        # Approval emoji
        approval_emoji = "✅" if validation['approved'] else "❌"
        
        output = f"""
╔════════════════════════════════════════════════╗
║      ⚠️  RISK AGENT VALIDATION REPORT         ║
╚════════════════════════════════════════════════╝

⏰ Analyzed: {validation['timestamp'].strftime('%I:%M:%S %p')}
🤖 AI Model: {self._get_model_name()}
🎲 Simulations: {risk['simulation_params']['num_simulations']:,}

{approval_emoji} RECOMMENDATION: {validation['recommendation'].replace('_', ' ')}

📊 MONTE CARLO RESULTS:
   Portfolio Value (Initial): ${risk['simulation_params']['initial_value']:,.0f}
   
   Expected Outcomes (after {risk['simulation_params']['time_horizon_years']:.0f} year{'s' if risk['simulation_params']['time_horizon_years'] != 1 else ''}):
   • Median:     ${risk['median_outcome']:,.0f}
   • Best 5%:    ${risk['percentile_95']:,.0f}
   • Worst 5%:   ${risk['percentile_5']:,.0f}
   • Average:    ${risk['mean_outcome']:,.0f}
   
   Risk Metrics:
   • Max Drawdown:        {risk['max_drawdown']*100:.1f}%
   • Probability of Loss: {risk['prob_loss']*100:.1f}%
   • Prob of 10%+ Gain:   {risk['prob_gain_10pct']*100:.1f}%
   • Sharpe Ratio:        {risk['sharpe_ratio']:.2f}
   • Value at Risk (95%): {risk['var_95']*100:.1f}%

"""
        
        # Add violations if any
        if validation['violations']:
            output += "🚨 CONSTRAINT VIOLATIONS:\n"
            for v in validation['violations']:
                output += f"   • {v}\n"
            output += "\n"
        
        # Add concerns if any
        if validation['concerns']:
            output += "⚠️  RISK CONCERNS:\n"
            for c in validation['concerns']:
                output += f"   • {c}\n"
            output += "\n"
        
        # Add modifications if any
        if validation['suggested_modifications']:
            output += "💡 SUGGESTED MODIFICATIONS:\n"
            for m in validation['suggested_modifications']:
                output += f"   • {m}\n"
            output += "\n"
        
        # Add explanation
        output += f"""💬 RISK ASSESSMENT:
{self._wrap_text(validation['explanation'])}

📈 Confidence: {validation['confidence']*100:.0f}%

════════════════════════════════════════════════
"""
        return output
    
    def _wrap_text(self, text: str, width: int = 60, indent: str = "   ") -> str:
        """Wrap text for better display"""
        if not text:
            return f"{indent}(Not available)"
        
        words = text.split()
        lines = []
        current_line = indent
        
        for word in words:
            if len(current_line) + len(word) + 1 <= width + len(indent):
                current_line += word + " "
            else:
                lines.append(current_line.rstrip())
                current_line = indent + word + " "
        
        if current_line.strip():
            lines.append(current_line.rstrip())
        
        return '\n'.join(lines)


# ========================================
# EXAMPLE USAGE
# ========================================

if __name__ == "__main__":
    # Example: Validate a strategy with Monte Carlo
    
    risk_agent = RiskAgent(
        openrouter_api_key="YOUR_KEY_HERE",
        model="nvidia/llama-3.1-nemotron-70b-instruct",
        use_gpu=True,  # Will fall back to CPU if GPU not available
        num_simulations=10000
    )
    
    # Mock strategy from Strategy Agent
    strategy = {
        'strategy_summary': 'Reduce equity exposure to 50%, increase bonds to 30%',
        'target_allocation': {
            'SPY': 0.50,
            'TLT': 0.30,
            'GLD': 0.10,
            'cash': 0.10
        },
        'recommended_trades': []
    }
    
    # Current portfolio
    current_portfolio = {
        'total_value': 100000,
        'cash': 10000,
        'positions': {
            'SPY': {'shares': 150, 'value': 71298, 'weight': 0.71},
            'TLT': {'shares': 100, 'value': 9500, 'weight': 0.095}
        }
    }
    
    # User profile
    user_profile = {
        'risk_tolerance': 'moderate',
        'time_horizon': 'long-term',
        'goals': ['retirement'],
        'experience_level': 'beginner'
    }
    
    # Market report
    market_report = {
        'market_data': {
            'vix': 22.5,
            'spy_change_pct': -1.2
        },
        'analysis': 'Bearish market conditions'
    }
    
    # Risk constraints
    risk_constraints = {
        'max_position_size': 0.60,
        'max_drawdown_limit': 0.20,
        'min_cash_reserve': 0.05
    }
    
    print("\n🚀 Running risk validation with Monte Carlo simulations...\n")
    
    # Validate strategy
    validation = risk_agent.validate_strategy(
        strategy=strategy,
        current_portfolio=current_portfolio,
        user_profile=user_profile,
        market_report=market_report,
        risk_constraints=risk_constraints
    )
    
    # Display results
    print(risk_agent.get_validation_summary(validation))
    
    # Example: Run standalone Monte Carlo
    print("\n" + "="*50)
    print("Example: Standalone Monte Carlo Simulation")
    print("="*50 + "\n")
    
    mc_results = risk_agent.run_monte_carlo(
        portfolio_allocation={'SPY': 0.60, 'TLT': 0.30, 'GLD': 0.10},
        initial_value=100000,
        time_horizon_years=10.0
    )
    
    print(f"10-Year Projection ({mc_results['simulation_params']['num_simulations']:,} simulations):")
    print(f"  Median: ${mc_results['median_outcome']:,.0f}")
    print(f"  Best 5%: ${mc_results['percentile_95']:,.0f}")
    print(f"  Worst 5%: ${mc_results['percentile_5']:,.0f}")
