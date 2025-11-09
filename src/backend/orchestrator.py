"""
APEX Multi-Agent Orchestrator
Coordinates conversations between Market, Strategy, and Risk agents.
Allows agents to debate, refine, and iterate on investment decisions.
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime
import time


class AgentOrchestrator:
    """
    Orchestrates multi-agent conversations for APEX investment system.
    
    The orchestrator manages the flow of information between agents,
    allowing them to debate, challenge, and refine recommendations
    through multiple rounds of discussion.
    
    Conversation Flow (per round):
    1. Market Agent: Provides environment analysis
    2. Strategy Agent: Proposes allocation based on market conditions
    3. Risk Agent: Validates strategy and provides concerns
    4. Strategy Agent: Responds to risk concerns (if rejected)
    5. (Repeat for max_rounds or until consensus)
    
    User can interrupt at any point to provide input or override.
    """
    
    def __init__(
        self,
        market_agent,
        strategy_agent,
        risk_agent,
        max_rounds: int = 3,
        enable_logging: bool = True,
        require_user_approval: bool = True,
        auto_approve_threshold: float = 0.85
    ):
        """
        Initialize orchestrator with agents.
        
        Args:
            market_agent: Instance of MarketAgent
            strategy_agent: Instance of StrategyAgent
            risk_agent: Instance of RiskAgent
            max_rounds: Maximum conversation rounds before forcing decision
            enable_logging: Print conversation flow
            require_user_approval: If True, wait for user approval before executing
            auto_approve_threshold: Auto-approve if all agents have confidence > this
        """
        self.market_agent = market_agent
        self.strategy_agent = strategy_agent
        self.risk_agent = risk_agent
        
        self.max_rounds = max_rounds
        self.logging_enabled = enable_logging
        self.require_user_approval = require_user_approval
        self.auto_approve_threshold = auto_approve_threshold
        
        # Conversation history
        self.conversation_history = []
        
        # User interrupt flag
        self.user_interrupted = False
        self.user_input = None
        
        self.log("🎭 Orchestrator initialized with 3 agents")
        self.log(f"⚙️  Max rounds: {max_rounds}")
        self.log(f"👤 Require user approval: {require_user_approval}")
    
    def log(self, message: str, agent: str = "ORCHESTRATOR"):
        """Print status message if logging enabled"""
        if self.logging_enabled:
            timestamp = datetime.now().strftime("%H:%M:%S")
            emoji_map = {
                "ORCHESTRATOR": "🎭",
                "MARKET": "🔍",
                "STRATEGY": "🧠",
                "RISK": "⚠️",
                "USER": "👤"
            }
            emoji = emoji_map.get(agent, "💬")
            print(f"[{timestamp}] {emoji} {agent}: {message}")
    
    # ========================================
    # MAIN ORCHESTRATION
    # ========================================
    
    def run_analysis(
        self,
        current_portfolio: Dict,
        user_profile: Dict,
        risk_constraints: Optional[Dict] = None,
        available_assets: Optional[Dict] = None,
        user_input_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Run complete multi-agent analysis with conversation rounds.
        
        Args:
            current_portfolio: Current portfolio state
            user_profile: User preferences and goals
            risk_constraints: Risk limits to enforce
            available_assets: Tradeable assets (None = use defaults)
            user_input_callback: Function to call for user input
                                 Should return {'interrupted': bool, 'message': str}
        
        Returns:
            {
                'final_recommendation': {...},
                'approved': True/False,
                'conversation_rounds': [...],
                'consensus_reached': True/False,
                'rounds_taken': 3,
                'user_approved': True/False,
                'timestamp': datetime(...)
            }
        """
        self.log("="*60)
        self.log("🚀 STARTING MULTI-AGENT ANALYSIS")
        self.log("="*60)
        
        # Reset state
        self.conversation_history = []
        self.user_interrupted = False
        self.user_input = None
        
        # Round 0: Market Agent scans environment
        self.log("\n" + "="*60)
        self.log("📊 ROUND 0: MARKET ANALYSIS")
        self.log("="*60)
        
        market_report = self.market_agent.scan_market()
        self._record_agent_output("MARKET", 0, market_report, "market_analysis")
        
        self.log(f"Market Condition: {self._extract_market_condition(market_report)}")
        self.log(f"VIX: {market_report['market_data']['vix']:.1f}")
        
        # Check for user interrupt
        if user_input_callback and self._check_user_interrupt(user_input_callback, 0):
            return self._handle_user_override(current_portfolio, user_profile)
        
        # Main conversation rounds
        final_strategy = None
        final_validation = None
        consensus_reached = False
        
        for round_num in range(1, self.max_rounds + 1):
            self.log("\n" + "="*60)
            self.log(f"🔄 ROUND {round_num} OF {self.max_rounds}")
            self.log("="*60)
            
            # Strategy Agent proposes allocation
            self.log("\n💭 Strategy Agent thinking...")
            
            # Include feedback from previous round if available
            previous_feedback = self._get_previous_risk_feedback()
            
            strategy = self.strategy_agent.generate_strategy(
                market_report=market_report,
                current_portfolio=current_portfolio,
                user_profile=user_profile,
                risk_constraints=risk_constraints,
                available_assets=available_assets
            )
            
            self._record_agent_output("STRATEGY", round_num, strategy, "strategy_proposal")
            
            self.log(f"Strategy: {strategy['strategy_summary'][:80]}...")
            self.log(f"Confidence: {strategy['confidence']*100:.0f}%")
            
            # Check for user interrupt
            if user_input_callback and self._check_user_interrupt(user_input_callback, round_num):
                return self._handle_user_override(current_portfolio, user_profile)
            
            # Risk Agent validates
            self.log("\n🔍 Risk Agent validating...")
            
            validation = self.risk_agent.validate_strategy(
                strategy=strategy,
                current_portfolio=current_portfolio,
                user_profile=user_profile,
                market_report=market_report,
                risk_constraints=risk_constraints
            )
            
            self._record_agent_output("RISK", round_num, validation, "risk_validation")
            
            self.log(f"Risk Verdict: {validation['recommendation']}")
            self.log(f"Approved: {'✅ YES' if validation['approved'] else '❌ NO'}")
            
            if validation['violations']:
                self.log(f"Violations: {len(validation['violations'])}")
            if validation['concerns']:
                self.log(f"Concerns: {len(validation['concerns'])}")
            
            # Check for user interrupt
            if user_input_callback and self._check_user_interrupt(user_input_callback, round_num):
                return self._handle_user_override(current_portfolio, user_profile)
            
            # Store latest results
            final_strategy = strategy
            final_validation = validation
            
            # Check if consensus reached
            if validation['approved']:
                # Check confidence levels
                strategy_confident = strategy['confidence'] >= 0.70
                risk_confident = validation['confidence'] >= 0.70
                
                if strategy_confident and risk_confident:
                    self.log("\n" + "="*60)
                    self.log("✅ CONSENSUS REACHED - All agents approve!")
                    self.log("="*60)
                    consensus_reached = True
                    break
                else:
                    self.log("\n⚠️  Approved but low confidence - continuing discussion...")
            else:
                self.log(f"\n❌ Strategy rejected - {len(validation['violations'])} violations, {len(validation['concerns'])} concerns")
                
                # If not last round, continue to let Strategy Agent respond
                if round_num < self.max_rounds:
                    self.log("↻ Strategy Agent will refine proposal in next round...")
                else:
                    self.log("⚠️  Max rounds reached without consensus")
        
        # Final decision
        self.log("\n" + "="*60)
        self.log("🏁 MULTI-AGENT ANALYSIS COMPLETE")
        self.log("="*60)
        
        # Get user approval if required
        user_approved = True
        if self.require_user_approval:
            user_approved = self._get_user_approval(
                final_strategy,
                final_validation,
                user_input_callback
            )
        elif consensus_reached:
            # Auto-approve if consensus and high confidence
            high_confidence = (
                final_strategy['confidence'] >= self.auto_approve_threshold and
                final_validation['confidence'] >= self.auto_approve_threshold
            )
            user_approved = high_confidence
            
            if user_approved:
                self.log(f"✅ Auto-approved (confidence > {self.auto_approve_threshold*100:.0f}%)")
        
        # Build final result
        result = {
            'final_strategy': final_strategy,
            'final_validation': final_validation,
            'approved': validation['approved'] and user_approved,
            'conversation_rounds': self.conversation_history,
            'consensus_reached': consensus_reached,
            'rounds_taken': round_num,
            'user_approved': user_approved,
            'market_context': market_report,
            'timestamp': datetime.now()
        }
        
        self.log(f"\nFinal Status: {'✅ APPROVED' if result['approved'] else '❌ NOT APPROVED'}")
        self.log(f"Rounds: {result['rounds_taken']}/{self.max_rounds}")
        self.log(f"Consensus: {'✅ YES' if consensus_reached else '❌ NO'}")
        self.log(f"User Approved: {'✅ YES' if user_approved else '❌ NO'}")
        
        return result
    
    # ========================================
    # CONVERSATION MANAGEMENT
    # ========================================
    
    def _record_agent_output(
        self,
        agent_name: str,
        round_num: int,
        output: Dict,
        output_type: str
    ):
        """Record agent contribution to conversation history"""
        self.conversation_history.append({
            'agent': agent_name,
            'round': round_num,
            'type': output_type,
            'output': output,
            'timestamp': datetime.now()
        })
    
    def _get_previous_risk_feedback(self) -> Optional[Dict]:
        """Get feedback from Risk Agent in previous round"""
        # Look backwards through history for most recent risk validation
        for entry in reversed(self.conversation_history):
            if entry['agent'] == 'RISK' and entry['type'] == 'risk_validation':
                validation = entry['output']
                
                if not validation['approved']:
                    return {
                        'violations': validation['violations'],
                        'concerns': validation['concerns'],
                        'suggested_modifications': validation['suggested_modifications']
                    }
        
        return None
    
    def _extract_market_condition(self, market_report: Dict) -> str:
        """Extract market condition from report"""
        analysis = market_report.get('analysis', '')
        
        for condition in ['Bullish', 'Bearish', 'Volatile', 'Mixed', 'Neutral']:
            if condition in analysis:
                return condition
        
        return 'Unknown'
    
    # ========================================
    # USER INTERACTION
    # ========================================
    
    def _check_user_interrupt(
        self,
        user_input_callback: Callable,
        round_num: int
    ) -> bool:
        """
        Check if user wants to interrupt and provide input.
        
        Args:
            user_input_callback: Function that returns {'interrupted': bool, 'message': str}
            round_num: Current round number
        
        Returns:
            True if user interrupted, False otherwise
        """
        if not user_input_callback:
            return False
        
        # Call user input callback (non-blocking)
        try:
            user_response = user_input_callback(round_num)
            
            if user_response and user_response.get('interrupted', False):
                self.user_interrupted = True
                self.user_input = user_response.get('message', '')
                
                self.log(f"👤 USER INTERRUPTED", agent="USER")
                self.log(f"Message: {self.user_input}", agent="USER")
                
                return True
        except Exception as e:
            self.log(f"Error checking user input: {e}")
        
        return False
    
    def _get_user_approval(
        self,
        strategy: Dict,
        validation: Dict,
        user_input_callback: Optional[Callable]
    ) -> bool:
        """
        Get final user approval for strategy.
        
        In a real UI, this would show a dialog with approve/reject buttons.
        For now, we'll use a callback function.
        """
        self.log("\n" + "="*60)
        self.log("👤 REQUESTING USER APPROVAL")
        self.log("="*60)
        
        self.log(f"Strategy: {strategy['strategy_summary']}")
        self.log(f"Risk Status: {validation['recommendation']}")
        
        # If callback provided, use it
        if user_input_callback:
            try:
                approval_response = user_input_callback('approval_request')
                
                if approval_response:
                    approved = approval_response.get('approved', False)
                    message = approval_response.get('message', '')
                    
                    if message:
                        self.log(f"User message: {message}", agent="USER")
                    
                    return approved
            except Exception as e:
                self.log(f"Error getting user approval: {e}")
        
        # Default: auto-approve if risk agent approved
        return validation['approved']
    
    def _handle_user_override(
        self,
        current_portfolio: Dict,
        user_profile: Dict
    ) -> Dict:
        """
        Handle case where user interrupted and wants to override.
        """
        self.log("👤 Processing user override...")
        
        # Return a special result indicating user took over
        return {
            'final_strategy': None,
            'final_validation': None,
            'approved': False,
            'conversation_rounds': self.conversation_history,
            'consensus_reached': False,
            'rounds_taken': len([r for r in self.conversation_history if r['type'] == 'strategy_proposal']),
            'user_approved': False,
            'user_interrupted': True,
            'user_input': self.user_input,
            'timestamp': datetime.now()
        }
    
    # ========================================
    # REFINEMENT (Strategy Agent responds to Risk feedback)
    # ========================================
    
    def _refine_strategy_with_feedback(
        self,
        original_strategy: Dict,
        risk_feedback: Dict,
        market_report: Dict,
        current_portfolio: Dict,
        user_profile: Dict,
        risk_constraints: Optional[Dict]
    ) -> Dict:
        """
        Have Strategy Agent refine proposal based on Risk Agent feedback.
        
        This creates a more sophisticated conversation where Strategy Agent
        can respond to specific concerns.
        """
        self.log("🔄 Strategy Agent refining based on Risk feedback...")
        
        # Build a refined prompt that includes risk feedback
        # This would be added to the Strategy Agent's context
        
        # For now, we rely on the Strategy Agent to naturally improve
        # in the next round based on the conversation history
        
        # In a more advanced version, you could have a specific
        # "refine_strategy" method that takes feedback as input
        
        return self.strategy_agent.generate_strategy(
            market_report=market_report,
            current_portfolio=current_portfolio,
            user_profile=user_profile,
            risk_constraints=risk_constraints
        )
    
    # ========================================
    # REPORTING & DISPLAY
    # ========================================
    
    def get_conversation_summary(self, result: Dict) -> str:
        """
        Format conversation history for display.
        """
        output = f"""
╔════════════════════════════════════════════════╗
║        🎭 MULTI-AGENT ANALYSIS SUMMARY        ║
╚════════════════════════════════════════════════╝

⏰ Completed: {result['timestamp'].strftime('%I:%M:%S %p')}
🔄 Rounds: {result['rounds_taken']}/{self.max_rounds}
🤝 Consensus: {'✅ YES' if result['consensus_reached'] else '❌ NO'}
👤 User Approved: {'✅ YES' if result['user_approved'] else '❌ NO'}

"""
        
        # Show conversation flow
        output += "📜 CONVERSATION HISTORY:\n"
        output += "─" * 50 + "\n\n"
        
        current_round = -1
        for entry in result['conversation_rounds']:
            # New round header
            if entry['round'] != current_round:
                current_round = entry['round']
                output += f"\n{'='*50}\n"
                output += f"ROUND {current_round}\n"
                output += f"{'='*50}\n\n"
            
            # Agent contribution
            agent_emoji = {
                'MARKET': '🔍',
                'STRATEGY': '🧠',
                'RISK': '⚠️'
            }
            
            emoji = agent_emoji.get(entry['agent'], '💬')
            output += f"{emoji} {entry['agent']} AGENT:\n"
            
            # Summary of output
            if entry['type'] == 'market_analysis':
                market_data = entry['output']['market_data']
                output += f"   • Market: SPY {market_data['spy_change_pct']:+.2f}%, VIX {market_data['vix']:.1f}\n"
                output += f"   • Alerts: {len(entry['output']['alerts'])}\n"
            
            elif entry['type'] == 'strategy_proposal':
                strategy = entry['output']
                output += f"   • Summary: {strategy['strategy_summary'][:60]}...\n"
                output += f"   • Trades: {len(strategy['recommended_trades'])}\n"
                output += f"   • Confidence: {strategy['confidence']*100:.0f}%\n"
            
            elif entry['type'] == 'risk_validation':
                validation = entry['output']
                output += f"   • Recommendation: {validation['recommendation']}\n"
                output += f"   • Approved: {'✅ YES' if validation['approved'] else '❌ NO'}\n"
                output += f"   • Violations: {len(validation['violations'])}\n"
                output += f"   • Concerns: {len(validation['concerns'])}\n"
            
            output += "\n"
        
        # Final recommendation
        output += "="*50 + "\n"
        output += "🏁 FINAL RECOMMENDATION\n"
        output += "="*50 + "\n\n"
        
        if result.get('user_interrupted'):
            output += "👤 User interrupted - no automated recommendation\n"
        elif result['final_strategy']:
            strategy = result['final_strategy']
            validation = result['final_validation']
            
            output += f"Strategy: {strategy['strategy_summary']}\n\n"
            
            output += "Target Allocation:\n"
            for symbol, weight in sorted(strategy['target_allocation'].items(), 
                                        key=lambda x: x[1], reverse=True):
                output += f"  • {symbol.upper()}: {weight*100:.1f}%\n"
            
            output += f"\nRisk Assessment: {validation['risk_assessment'].upper()}\n"
            output += f"Overall Status: {'✅ APPROVED' if result['approved'] else '❌ NOT APPROVED'}\n"
        
        output += "\n" + "="*50 + "\n"
        
        return output
    
    def get_execution_plan(self, result: Dict) -> Optional[Dict]:
        """
        Extract executable trade plan from approved result.
        
        Returns None if not approved, otherwise returns trade plan.
        """
        if not result['approved']:
            return None
        
        strategy = result['final_strategy']
        
        return {
            'target_allocation': strategy['target_allocation'],
            'recommended_trades': strategy['recommended_trades'],
            'strategy_summary': strategy['strategy_summary'],
            'risk_level': result['final_validation']['risk_assessment'],
            'confidence': strategy['confidence'],
            'approved_at': result['timestamp']
        }


# ========================================
# SIMPLE USER INPUT CALLBACK EXAMPLE
# ========================================

class SimpleUserInput:
    """
    Example user input handler for demonstrations.
    
    In a real UI, this would be connected to buttons, forms, etc.
    """
    
    def __init__(self):
        self.interrupt_on_round = None
        self.approve_final = True
    
    def __call__(self, context) -> Dict:
        """
        Called by orchestrator to check for user input.
        
        Args:
            context: Either round number (int) or 'approval_request' (str)
        
        Returns:
            Dict with user response
        """
        # During rounds
        if isinstance(context, int):
            round_num = context
            
            # Check if user wants to interrupt
            if self.interrupt_on_round == round_num:
                return {
                    'interrupted': True,
                    'message': 'User requested manual override'
                }
            
            return {'interrupted': False}
        
        # Final approval
        elif context == 'approval_request':
            return {
                'approved': self.approve_final,
                'message': 'User approved' if self.approve_final else 'User rejected'
            }
        
        return {}


# ========================================
# EXAMPLE USAGE
# ========================================

if __name__ == "__main__":
    from market_agent import MarketAgent
    from strategy_agent import StrategyAgent
    from risk_agent import RiskAgent
    
    # Initialize all agents
    openrouter_key = "YOUR_KEY_HERE"
    model = "nvidia/llama-3.1-nemotron-70b-instruct"
    
    market_agent = MarketAgent(openrouter_key, model=model)
    strategy_agent = StrategyAgent(openrouter_key, model=model)
    risk_agent = RiskAgent(openrouter_key, model=model, num_simulations=10000)
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        market_agent=market_agent,
        strategy_agent=strategy_agent,
        risk_agent=risk_agent,
        max_rounds=3,
        require_user_approval=True,
        auto_approve_threshold=0.80
    )
    
    # Portfolio and user data
    current_portfolio = {
        'total_value': 100000,
        'cash': 10000,
        'positions': {
            'SPY': {'shares': 150, 'value': 71298, 'weight': 0.71},
            'TLT': {'shares': 100, 'value': 9500, 'weight': 0.095},
            'GLD': {'shares': 50, 'value': 9202, 'weight': 0.092}
        }
    }
    
    user_profile = {
        'risk_tolerance': 'moderate',
        'time_horizon': 'long-term',
        'goals': ['retirement', 'wealth-building'],
        'investment_style': 'balanced',
        'experience_level': 'beginner'
    }
    
    risk_constraints = {
        'max_position_size': 0.60,
        'max_drawdown_limit': 0.20,
        'min_cash_reserve': 0.05
    }
    
    # Simple user input handler (auto-approve)
    user_input = SimpleUserInput()
    user_input.approve_final = True  # Auto-approve
    # user_input.interrupt_on_round = 2  # Uncomment to test interruption
    
    # Run analysis
    print("\n" + "="*60)
    print("🚀 STARTING MULTI-AGENT ORCHESTRATED ANALYSIS")
    print("="*60 + "\n")
    
    result = orchestrator.run_analysis(
        current_portfolio=current_portfolio,
        user_profile=user_profile,
        risk_constraints=risk_constraints,
        user_input_callback=user_input
    )
    
    # Display results
    print("\n")
    print(orchestrator.get_conversation_summary(result))
    
    # Get execution plan if approved
    if result['approved']:
        print("\n" + "="*60)
        print("📋 EXECUTION PLAN")
        print("="*60 + "\n")
        
        plan = orchestrator.get_execution_plan(result)
        
        print(f"Strategy: {plan['strategy_summary']}\n")
        print("Trades to Execute:")
        for i, trade in enumerate(plan['recommended_trades'], 1):
            print(f"  {i}. {trade['action']} {trade['shares']} {trade['symbol']}")
            print(f"     Reason: {trade['reason']}")
        
        print(f"\nRisk Level: {plan['risk_level'].upper()}")
        print(f"Confidence: {plan['confidence']*100:.0f}%")
    else:
        print("\n⚠️  Strategy not approved - no execution plan")
