"""
APEX Strategy Agent
Generates portfolio allocation strategies and trade recommendations
based on market conditions, risk constraints, and user goals.
"""

from openai import OpenAI
from datetime import datetime
from typing import Dict, List, Optional
import json


class StrategyAgent:
    """
    Portfolio strategy and allocation agent for APEX multi-agent system.
    
    Responsibilities:
    - Generate asset allocation recommendations
    - Propose specific trades (buy/sell decisions)
    - Optimize portfolio balance
    - Consider market conditions from Market Agent
    - Respect risk constraints from Risk Agent
    - Align with user goals and preferences
    """
    
    def __init__(
        self,
        openrouter_api_key: str,
        enable_logging: bool = True,
        model: str = "nvidia/llama-3.1-nemotron-70b-instruct"
    ):
        """
        Initialize Strategy Agent.
        
        Args:
            openrouter_api_key: API key from openrouter.ai
            enable_logging: Print status messages
            model: NVIDIA model to use (same as Market Agent)
        """
        # Initialize OpenRouter client
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )
        
        self.model = model
        self.logging_enabled = enable_logging
        
        # Track strategy history for continuity
        self.strategy_history = []
        
        self.log(f"✅ Strategy Agent initialized with {self._get_model_name()}")
    
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
            print(f"[{timestamp}] 🧠 Strategy Agent: {message}")
    
    # ========================================
    # MAIN STRATEGY FUNCTION
    # ========================================
    
    def generate_strategy(
        self,
        market_report: Dict,
        current_portfolio: Dict,
        user_profile: Dict,
        risk_constraints: Optional[Dict] = None
    ) -> Dict:
        """
        Generate portfolio strategy based on current market and portfolio state.
        
        Args:
            market_report: Output from MarketAgent.scan_market()
                {
                    'market_data': {...},
                    'news_summary': {...},
                    'alerts': [...],
                    'analysis': "..."
                }
            
            current_portfolio: Current holdings
                {
                    'total_value': 100000,
                    'cash': 20000,
                    'positions': {
                        'SPY': {'shares': 100, 'value': 47532, 'weight': 0.59},
                        'TLT': {'shares': 50, 'value': 8500, 'weight': 0.11},
                        'GLD': {'shares': 30, 'value': 5400, 'weight': 0.07}
                    }
                }
            
            user_profile: User preferences and goals
                {
                    'risk_tolerance': 'moderate',  # conservative/moderate/aggressive
                    'time_horizon': 'long-term',   # short/medium/long-term
                    'goals': ['retirement', 'growth'],
                    'investment_style': 'growth'   # income/growth/balanced
                }
            
            risk_constraints: Optional constraints from Risk Agent
                {
                    'max_position_size': 0.20,     # Max 20% in single position
                    'max_sector_exposure': 0.40,   # Max 40% in single sector
                    'max_drawdown_limit': 0.15,    # Max 15% portfolio loss
                    'min_cash_reserve': 0.05       # Keep 5% in cash
                }
        
        Returns:
            {
                'strategy_summary': "Defensive positioning recommended...",
                'target_allocation': {
                    'SPY': 0.50,    # Target 50% in S&P 500
                    'TLT': 0.25,    # Target 25% in bonds
                    'GLD': 0.15,    # Target 15% in gold
                    'cash': 0.10    # Target 10% cash
                },
                'recommended_trades': [
                    {
                        'action': 'SELL',
                        'symbol': 'SPY',
                        'shares': 15,
                        'reason': 'Reduce equity exposure due to elevated volatility',
                        'urgency': 'medium'  # low/medium/high
                    },
                    {
                        'action': 'BUY',
                        'symbol': 'TLT',
                        'shares': 20,
                        'reason': 'Increase bond allocation for downside protection',
                        'urgency': 'medium'
                    }
                ],
                'rationale': "Detailed explanation of strategy...",
                'risk_assessment': 'medium',  # low/medium/high
                'confidence': 0.75,  # 0-1 scale
                'timestamp': datetime(...),
                'market_context_used': {
                    'market_condition': 'Bearish',
                    'vix_level': 18.5,
                    'key_alerts': [...]
                }
            }
        """
        self.log("🎯 Generating investment strategy...")
        
        # Build comprehensive prompt
        prompt = self._build_strategy_prompt(
            market_report,
            current_portfolio,
            user_profile,
            risk_constraints
        )
        
        # Get strategy from NVIDIA model
        strategy_text = self._generate_strategy_with_ai(prompt)
        
        # Parse structured strategy from AI response
        strategy = self._parse_strategy_response(
            strategy_text,
            market_report,
            current_portfolio
        )
        
        # Store in history for continuity
        self.strategy_history.append({
            'timestamp': datetime.now(),
            'strategy': strategy,
            'market_condition': market_report['market_data']['vix']
        })
        
        self.log(f"✅ Strategy generated: {strategy['strategy_summary'][:60]}...")
        return strategy
    
    # ========================================
    # PROMPT BUILDING
    # ========================================
    
    def _build_strategy_prompt(
        self,
        market_report: Dict,
        current_portfolio: Dict,
        user_profile: Dict,
        risk_constraints: Optional[Dict]
    ) -> str:
        """
        Build comprehensive prompt for strategy generation.
        """
        # Extract key market data
        market_data = market_report['market_data']
        market_analysis = market_report['analysis']
        alerts = market_report['alerts']
        
        # Format current positions
        positions_text = self._format_positions(current_portfolio)
        
        # Format risk constraints
        constraints_text = self._format_constraints(risk_constraints)
        
        # Build the prompt
        prompt = f"""You are the Strategy Agent in APEX, a professional multi-agent investment system. Your role is to generate optimal portfolio allocation strategies.

**CURRENT MARKET ENVIRONMENT:**
{market_analysis}

**MARKET METRICS:**
- S&P 500: ${market_data['spy_price']:.2f} ({market_data['spy_change_pct']:+.2f}%)
- VIX: {market_data['vix']:.1f}
- Volume: {market_data['volume_ratio']:.2f}x average
- Alerts: {', '.join(alerts[:3])}

**CURRENT PORTFOLIO (Total Value: ${current_portfolio['total_value']:,.2f}):**
{positions_text}

**USER PROFILE:**
- Risk Tolerance: {user_profile['risk_tolerance']}
- Time Horizon: {user_profile['time_horizon']}
- Goals: {', '.join(user_profile['goals'])}
- Investment Style: {user_profile['investment_style']}

**RISK CONSTRAINTS:**
{constraints_text}

**YOUR TASK:**
Generate a comprehensive investment strategy that:
1. Responds to current market conditions
2. Aligns with user risk tolerance and goals
3. Respects all risk constraints
4. Provides specific, actionable trade recommendations

**REQUIRED OUTPUT FORMAT:**

**STRATEGY_SUMMARY:**
[One sentence overview of the recommended approach]

**TARGET_ALLOCATION:**
SPY: XX%
TLT: XX%
GLD: XX%
Cash: XX%
[Ensure totals = 100%]

**RECOMMENDED_TRADES:**
Trade 1: [ACTION] [SHARES] shares of [SYMBOL]
Reason: [Why this trade is needed]
Urgency: [low/medium/high]

Trade 2: [ACTION] [SHARES] shares of [SYMBOL]
Reason: [Why this trade is needed]
Urgency: [low/medium/high]

**RATIONALE:**
[2-3 paragraphs explaining:
- How this strategy responds to market conditions
- Why the allocation changes are appropriate
- How this serves the user's long-term goals
- Expected risk/reward profile]

**RISK_ASSESSMENT:** [low/medium/high]
**CONFIDENCE:** [0.XX on 0-1 scale]

Be specific with numbers. Focus on practical, executable recommendations."""

        return prompt
    
    def _format_positions(self, portfolio: Dict) -> str:
        """Format portfolio positions for prompt"""
        lines = [f"- Cash: ${portfolio['cash']:,.2f} ({portfolio['cash']/portfolio['total_value']*100:.1f}%)"]
        
        for symbol, pos in portfolio['positions'].items():
            lines.append(
                f"- {symbol}: {pos['shares']} shares = ${pos['value']:,.2f} ({pos['weight']*100:.1f}%)"
            )
        
        return "\n".join(lines)
    
    def _format_constraints(self, constraints: Optional[Dict]) -> str:
        """Format risk constraints for prompt"""
        if not constraints:
            return "No specific constraints provided"
        
        lines = []
        if 'max_position_size' in constraints:
            lines.append(f"- Max position size: {constraints['max_position_size']*100:.0f}%")
        if 'max_sector_exposure' in constraints:
            lines.append(f"- Max sector exposure: {constraints['max_sector_exposure']*100:.0f}%")
        if 'max_drawdown_limit' in constraints:
            lines.append(f"- Max drawdown limit: {constraints['max_drawdown_limit']*100:.0f}%")
        if 'min_cash_reserve' in constraints:
            lines.append(f"- Min cash reserve: {constraints['min_cash_reserve']*100:.0f}%")
        
        return "\n".join(lines) if lines else "No specific constraints"
    
    # ========================================
    # AI INTERACTION
    # ========================================
    
    def _generate_strategy_with_ai(self, prompt: str) -> str:
        """
        Call NVIDIA model via OpenRouter to generate strategy.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert portfolio strategist with 20 years of experience managing institutional investments. Provide clear, actionable strategies with specific numbers and reasoning."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1200,  # Strategy needs more tokens for detailed reasoning
                temperature=0.7,  # Balanced between creativity and consistency
                extra_headers={
                    "HTTP-Referer": "https://apex-financial.com",
                    "X-Title": "APEX Strategy Agent"
                }
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.log(f"❌ Error calling AI: {e}")
            return self._generate_fallback_strategy()
    
    def _generate_fallback_strategy(self) -> str:
        """Simple fallback strategy if AI fails"""
        return """**STRATEGY_SUMMARY:**
Maintain balanced allocation with defensive tilt

**TARGET_ALLOCATION:**
SPY: 50%
TLT: 30%
GLD: 10%
Cash: 10%

**RECOMMENDED_TRADES:**
Trade 1: REBALANCE to target allocation
Reason: Maintain diversification
Urgency: low

**RATIONALE:**
Due to technical difficulties, recommending conservative rebalancing to standard 60/40-style allocation with modest gold hedge. This provides balanced exposure across asset classes while maintaining liquidity.

**RISK_ASSESSMENT:** medium
**CONFIDENCE:** 0.60"""
    
    # ========================================
    # RESPONSE PARSING
    # ========================================
    
    def _parse_strategy_response(
        self,
        strategy_text: str,
        market_report: Dict,
        current_portfolio: Dict
    ) -> Dict:
        """
        Parse AI response into structured strategy dict.
        
        This extracts the key information from the AI's text response
        and formats it into a clean, usable dictionary.
        """
        # Extract sections using simple text parsing
        summary = self._extract_section(strategy_text, "STRATEGY_SUMMARY")
        allocation_text = self._extract_section(strategy_text, "TARGET_ALLOCATION")
        trades_text = self._extract_section(strategy_text, "RECOMMENDED_TRADES")
        rationale = self._extract_section(strategy_text, "RATIONALE")
        risk = self._extract_section(strategy_text, "RISK_ASSESSMENT").lower().strip()
        confidence_text = self._extract_section(strategy_text, "CONFIDENCE")
        
        # Parse target allocation
        target_allocation = self._parse_allocation(allocation_text)
        
        # Parse trades
        recommended_trades = self._parse_trades(trades_text)
        
        # Parse confidence (handle "0.75" or "75%" formats)
        try:
            confidence = float(confidence_text.replace('%', '').strip())
            if confidence > 1:
                confidence = confidence / 100
        except:
            confidence = 0.70  # Default
        
        # Build final strategy dict
        return {
            'strategy_summary': summary.strip(),
            'target_allocation': target_allocation,
            'recommended_trades': recommended_trades,
            'rationale': rationale.strip(),
            'risk_assessment': risk if risk in ['low', 'medium', 'high'] else 'medium',
            'confidence': confidence,
            'timestamp': datetime.now(),
            'market_context_used': {
                'market_condition': self._extract_market_condition(market_report['analysis']),
                'vix_level': market_report['market_data']['vix'],
                'key_alerts': market_report['alerts'][:3]
            },
            'raw_response': strategy_text  # Keep full text for debugging
        }
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """
        Extract a section from the AI response.
        
        Example:
        Input: "**STRATEGY_SUMMARY:**\nDefensive positioning\n**TARGET_ALLOCATION:**..."
        Section: "STRATEGY_SUMMARY"
        Output: "Defensive positioning"
        """
        # Look for the section header
        start_marker = f"**{section_name}:**"
        if start_marker not in text:
            # Try alternate format
            start_marker = f"{section_name}:"
            if start_marker not in text:
                return ""
        
        # Find where section starts
        start_idx = text.index(start_marker) + len(start_marker)
        
        # Find where next section starts (or end of text)
        remaining_text = text[start_idx:]
        end_idx = len(remaining_text)
        
        # Look for next section marker
        for next_section in ["**", "\n\n**"]:
            if next_section in remaining_text:
                potential_end = remaining_text.index(next_section)
                if potential_end < end_idx:
                    end_idx = potential_end
        
        return remaining_text[:end_idx].strip()
    
    def _parse_allocation(self, allocation_text: str) -> Dict[str, float]:
        """
        Parse target allocation from text.
        
        Example input:
        "SPY: 50%
         TLT: 30%
         GLD: 10%
         Cash: 10%"
        
        Output:
        {'SPY': 0.50, 'TLT': 0.30, 'GLD': 0.10, 'cash': 0.10}
        """
        allocation = {}
        
        for line in allocation_text.split('\n'):
            line = line.strip()
            if ':' in line:
                parts = line.split(':')
                symbol = parts[0].strip().upper()
                
                # Extract percentage
                pct_text = parts[1].strip().replace('%', '').strip()
                try:
                    pct = float(pct_text) / 100
                    allocation[symbol if symbol != 'CASH' else 'cash'] = pct
                except:
                    continue
        
        # Normalize to ensure it sums to 1.0
        total = sum(allocation.values())
        if total > 0:
            allocation = {k: v/total for k, v in allocation.items()}
        
        return allocation
    
    def _parse_trades(self, trades_text: str) -> List[Dict]:
        """
        Parse trade recommendations from text.
        
        Example input:
        "Trade 1: SELL 15 shares of SPY
         Reason: Reduce equity exposure
         Urgency: medium
         
         Trade 2: BUY 20 shares of TLT
         Reason: Increase bond allocation
         Urgency: medium"
        
        Output:
        [
            {
                'action': 'SELL',
                'symbol': 'SPY',
                'shares': 15,
                'reason': 'Reduce equity exposure',
                'urgency': 'medium'
            },
            ...
        ]
        """
        trades = []
        
        # Split by "Trade X:"
        trade_blocks = trades_text.split('Trade ')[1:]  # Skip first empty split
        
        for block in trade_blocks:
            try:
                lines = [l.strip() for l in block.split('\n') if l.strip()]
                
                # Parse first line: "1: SELL 15 shares of SPY"
                first_line = lines[0]
                if ':' in first_line:
                    first_line = first_line.split(':', 1)[1].strip()
                
                # Extract action, shares, symbol
                words = first_line.split()
                action = words[0].upper()  # BUY or SELL
                
                shares = None
                symbol = None
                
                for i, word in enumerate(words):
                    if word.isdigit():
                        shares = int(word)
                    if word.upper() in ['SPY', 'TLT', 'GLD', 'QQQ', 'IWM', 'VTI']:
                        symbol = word.upper()
                
                # Extract reason and urgency from subsequent lines
                reason = ""
                urgency = "medium"
                
                for line in lines[1:]:
                    if line.lower().startswith('reason:'):
                        reason = line.split(':', 1)[1].strip()
                    elif line.lower().startswith('urgency:'):
                        urgency = line.split(':', 1)[1].strip().lower()
                
                if action and symbol and shares:
                    trades.append({
                        'action': action,
                        'symbol': symbol,
                        'shares': shares,
                        'reason': reason,
                        'urgency': urgency
                    })
            except:
                continue
        
        return trades
    
    def _extract_market_condition(self, analysis_text: str) -> str:
        """Extract market condition from Market Agent analysis"""
        if 'Bullish' in analysis_text:
            return 'Bullish'
        elif 'Bearish' in analysis_text:
            return 'Bearish'
        elif 'Volatile' in analysis_text:
            return 'Volatile'
        elif 'Mixed' in analysis_text:
            return 'Mixed'
        else:
            return 'Neutral'
    
    # ========================================
    # UTILITY FUNCTIONS
    # ========================================
    
    def get_strategy_summary(self, strategy: Dict) -> str:
        """
        Format strategy for display in UI/terminal.
        
        Args:
            strategy: Output from generate_strategy()
        
        Returns:
            Formatted string for display
        """
        output = f"""
╔════════════════════════════════════════════════╗
║      🧠 STRATEGY AGENT RECOMMENDATION         ║
╚════════════════════════════════════════════════╝

⏰ Generated: {strategy['timestamp'].strftime('%I:%M:%S %p')}
🤖 AI Model: {self._get_model_name()}

📋 STRATEGY SUMMARY:
   {strategy['strategy_summary']}

🎯 TARGET ALLOCATION:
"""
        for symbol, weight in strategy['target_allocation'].items():
            output += f"   {symbol.upper():5s}: {weight*100:5.1f}%\n"
        
        output += f"""
📊 RECOMMENDED TRADES ({len(strategy['recommended_trades'])} total):
"""
        for i, trade in enumerate(strategy['recommended_trades'], 1):
            output += f"   {i}. {trade['action']} {trade['shares']} {trade['symbol']}\n"
            output += f"      Reason: {trade['reason']}\n"
            output += f"      Urgency: {trade['urgency'].upper()}\n"
        
        output += f"""
💡 RATIONALE:
{strategy['rationale']}

⚠️  Risk Assessment: {strategy['risk_assessment'].upper()}
📈 Confidence: {strategy['confidence']*100:.0f}%

🌍 MARKET CONTEXT:
   Condition: {strategy['market_context_used']['market_condition']}
   VIX: {strategy['market_context_used']['vix_level']:.1f}

════════════════════════════════════════════════
"""
        return output
    
    def calculate_rebalance_trades(
        self,
        current_portfolio: Dict,
        target_allocation: Dict
    ) -> List[Dict]:
        """
        Calculate specific trades needed to reach target allocation.
        
        This is a helper function to convert percentage targets into
        actual buy/sell orders.
        
        Args:
            current_portfolio: Current holdings
            target_allocation: Target percentages from strategy
        
        Returns:
            List of trades needed to rebalance
        """
        total_value = current_portfolio['total_value']
        trades = []
        
        # Calculate target dollar amounts
        targets = {
            symbol: total_value * weight
            for symbol, weight in target_allocation.items()
        }
        
        # For each position, calculate needed change
        for symbol, target_value in targets.items():
            if symbol == 'cash':
                continue
            
            # Current value
            current_value = 0
            current_shares = 0
            if symbol in current_portfolio['positions']:
                current_value = current_portfolio['positions'][symbol]['value']
                current_shares = current_portfolio['positions'][symbol]['shares']
            
            # Calculate difference
            diff_value = target_value - current_value
            
            # Estimate shares needed (rough estimate - would need current price)
            if current_shares > 0:
                price_per_share = current_value / current_shares
            else:
                price_per_share = 100  # Default estimate
            
            shares_to_trade = int(diff_value / price_per_share)
            
            if abs(shares_to_trade) > 0:
                trades.append({
                    'action': 'BUY' if shares_to_trade > 0 else 'SELL',
                    'symbol': symbol,
                    'shares': abs(shares_to_trade),
                    'reason': f'Rebalance to {target_allocation[symbol]*100:.0f}% target',
                    'urgency': 'low'
                })
        
        return trades


# ========================================
# EXAMPLE USAGE
# ========================================

if __name__ == "__main__":
    # Example integration with Market Agent
    
    # 1. Initialize Strategy Agent
    strategy_agent = StrategyAgent(
        openrouter_api_key="YOUR_KEY_HERE",
        model="nvidia/llama-3.1-nemotron-70b-instruct"
    )
    
    # 2. Mock market report (would come from Market Agent)
    market_report = {
        'market_data': {
            'spy_price': 475.32,
            'spy_change_pct': -0.82,
            'vix': 22.5,
            'volume_ratio': 1.35
        },
        'alerts': [
            '⚠️ ELEVATED VOLATILITY: VIX above 20',
            '📊 NOTABLE MOVE: SPY down 0.8%'
        ],
        'analysis': """**Market Condition:** Bearish
**Risk Level:** Medium-High
**Key Insight:** Markets showing defensive rotation amid elevated VIX."""
    }
    
    # 3. Current portfolio state
    current_portfolio = {
        'total_value': 100000,
        'cash': 10000,
        'positions': {
            'SPY': {'shares': 150, 'value': 71298, 'weight': 0.71},
            'TLT': {'shares': 100, 'value': 9500, 'weight': 0.095},
            'GLD': {'shares': 50, 'value': 9202, 'weight': 0.092}
        }
    }
    
    # 4. User profile
    user_profile = {
        'risk_tolerance': 'moderate',
        'time_horizon': 'long-term',
        'goals': ['retirement', 'capital preservation'],
        'investment_style': 'balanced'
    }
    
    # 5. Risk constraints (would come from Risk Agent)
    risk_constraints = {
        'max_position_size': 0.60,
        'max_drawdown_limit': 0.15,
        'min_cash_reserve': 0.10
    }
    
    # 6. Generate strategy
    print("\n🚀 Generating investment strategy...\n")
    strategy = strategy_agent.generate_strategy(
        market_report=market_report,
        current_portfolio=current_portfolio,
        user_profile=user_profile,
        risk_constraints=risk_constraints
    )
    
    # 7. Display results
    print(strategy_agent.get_strategy_summary(strategy))
    
    # 8. Access specific recommendations
    print("\n📊 Quick Access:")
    print(f"   Strategy: {strategy['strategy_summary']}")
    print(f"   # of trades: {len(strategy['recommended_trades'])}")
    print(f"   Confidence: {strategy['confidence']*100:.0f}%")
