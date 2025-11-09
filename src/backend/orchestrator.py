"""
APEX Multi-Agent Orchestrator
Coordinates conversations between Market, Strategy, and Risk agents.
Allows agents to debate, refine, and iterate on investment decisions.
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum
import logging
import time

try:
    from output_refinement_pipeline import RefinementPipeline
    REFINEMENT_AVAILABLE = True
except ImportError:
    REFINEMENT_AVAILABLE = False
    print("⚠️  Output Refinement Pipeline not available")


class OrchestratorState(Enum):
    """State machine states for orchestrator workflow"""
    IDLE = "idle"
    SCANNING = "scanning"
    STRATEGIZING = "strategizing"
    RISK_CHECK = "risk_check"
    EXECUTING = "executing"
    EXPLAINING = "explaining"
    WAITING_USER = "waiting_user"
    PAUSED = "paused"
    ERROR = "error"


class Orchestrator:
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

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.logger = logging.getLogger(__name__)
        self.redis_url = redis_url

        # Agent network for communication
        self.network = AgentNetwork(redis_url=redis_url)

        # Initialize all agents
        self.agents = {
            "market": MarketAgent(agent_network=self.network),
            "strategy": StrategyAgent(agent_network=self.network),
            "risk": RiskAgent(agent_network=self.network),
            "executor": ExecutorAgent(agent_network=self.network),
            "explainer": ExplainerAgent(agent_network=self.network),
            "user": None  # Will be initialized after UserAgent is created
        }

        # State management
        self.state = OrchestratorState.IDLE
        self.is_paused = False
        self.is_running = False

        # Decision tracking
        self.current_decision = {
            "market_report": None,
            "strategy": None,
            "risk_assessment": None,
            "execution_result": None,
            "explanation": None,
            "user_input": None
        }
        self.decision_history: List[Dict[str, Any]] = []

        # Configuration
        self.config = {
            "scan_interval": 300,  # 5 minutes
            "max_retries": 3,
            "user_timeout": 60,  # seconds to wait for user input
            "enable_auto_execute": False,  # Require user approval for trades
            "refinement": {
                "enabled": REFINEMENT_AVAILABLE,
                "explanation_level": "beginner",  # beginner/intermediate/advanced
                "max_terms_per_output": 10,
                "format": "terminal"  # terminal/web/both
            }
        }

        # Error tracking
        self.error_count = 0
        self.max_errors = 10

        # Output Refinement Pipeline
        self.refinement_pipeline = None

    async def initialize(self):
        """Initialize the orchestrator and all agents"""
        self.logger.info("🚀 Initializing APEX Orchestrator...")

        try:
            # Initialize agent network
            await self.network.initialize()
            self.logger.info("✓ Agent network initialized")

            # Subscribe to key channels
            await self._subscribe_to_channels()
            self.logger.info("✓ Subscribed to agent channels")

            # Initialize User Agent (when available)
            try:
                self.agents["user"] = UserAgent(agent_network=self.network)
                self.logger.info("✓ User Agent initialized")
            except Exception as e:
                self.logger.warning(f"⚠ User Agent not available: {e}")

            # Initialize Output Refinement Pipeline
            if REFINEMENT_AVAILABLE and self.config["refinement"]["enabled"]:
                try:
                    self.refinement_pipeline = RefinementPipeline(
                        explanation_level=self.config["refinement"]["explanation_level"],
                        max_terms=self.config["refinement"]["max_terms_per_output"]
                    )
                    self.logger.info("✓ Output Refinement Pipeline initialized")
                    stats = self.refinement_pipeline.get_stats()
                    self.logger.info(f"   Glossary terms: {stats['glossary_terms']}")
                    self.logger.info(f"   Explanation level: {stats['explanation_level']}")
                except Exception as e:
                    self.logger.warning(f"⚠ Refinement Pipeline failed: {e}")
                    self.refinement_pipeline = None

            self.state = OrchestratorState.IDLE
            self.logger.info("✅ Orchestrator ready")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize orchestrator: {e}")
            self.state = OrchestratorState.ERROR
            raise

    async def _subscribe_to_channels(self):
        """Subscribe orchestrator to relevant agent channels"""
        channels = [
            "market_update",
            "strategy.updated",
            "risk_assessment",
            "trade_executed",
            "trade_explanation",
            "user_input",
            "agent_pause",
            "agent_resume"
        ]

        for channel in channels:
            # Note: actual subscription handled by agent network
            self.logger.debug(f"Monitoring channel: {channel}")

    async def start(self):
        """Start the main orchestrator loop"""
        if self.is_running:
            self.logger.warning("Orchestrator already running")
            return

        self.is_running = True
        self.logger.info("🎬 Starting orchestrator main loop")

        # Start background message listener
        asyncio.create_task(self._message_listener())

        # Start main decision loop
        while self.is_running:
            try:
                if self.is_paused:
                    await asyncio.sleep(1)
                    continue

                if self.state == OrchestratorState.IDLE:
                    await self._execute_decision_cycle()
                    await asyncio.sleep(self.config["scan_interval"])

                elif self.state == OrchestratorState.ERROR:
                    self.logger.error("Orchestrator in error state, attempting recovery...")
                    await asyncio.sleep(30)
                    self.state = OrchestratorState.IDLE
                    self.error_count = 0

                else:
                    # State machine is progressing, check periodically
                    await asyncio.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                self.error_count += 1

                if self.error_count >= self.max_errors:
                    self.logger.critical("Max errors reached, stopping orchestrator")
                    self.state = OrchestratorState.ERROR
                    self.is_running = False
                else:
                    await asyncio.sleep(5)

    async def _execute_decision_cycle(self):
        """Execute one complete decision cycle through all agents"""
        cycle_start = datetime.now()
        self.logger.info("=" * 60)
        self.logger.info("📊 Starting new decision cycle")

        try:
            # Reset current decision
            self.current_decision = {k: None for k in self.current_decision.keys()}

            # Step 1: Market Scanning
            await self._transition_state(OrchestratorState.SCANNING)
            market_report = await self._run_market_scan()
            if not market_report:
                self.logger.warning("Market scan failed, aborting cycle")
                await self._transition_state(OrchestratorState.IDLE)
                return

            self.current_decision["market_report"] = market_report
            await self.network.broadcast_agent_communication(
                from_agent="market",
                to_agent="strategy",
                message=f"Market scan complete. VIX: {market_report.get('vix_level', 'N/A')}, "
                        f"Alerts: {len(market_report.get('alerts', []))}"
            )

            # Step 2: Strategy Generation
            await self._transition_state(OrchestratorState.STRATEGIZING)
            strategy = await self._run_strategy_generation(market_report)
            if not strategy:
                self.logger.warning("Strategy generation failed, aborting cycle")
                await self._transition_state(OrchestratorState.IDLE)
                return

            self.current_decision["strategy"] = strategy
            await self.network.broadcast_agent_communication(
                from_agent="strategy",
                to_agent="risk",
                message=f"Proposed {len(strategy.get('recommendations', []))} trades. "
                        f"Allocation adjustments: {strategy.get('target_allocation', {})}"
            )

            # Step 3: Risk Assessment
            await self._transition_state(OrchestratorState.RISK_CHECK)
            risk_assessment = await self._run_risk_check(strategy)
            if not risk_assessment:
                self.logger.warning("Risk assessment failed, aborting cycle")
                await self._transition_state(OrchestratorState.IDLE)
                return

            self.current_decision["risk_assessment"] = risk_assessment

            # Check if risk agent approved the strategy
            if risk_assessment.get("approval") != "approved":
                self.logger.warning(f"❌ Strategy rejected by Risk Agent: {risk_assessment.get('reason')}")
                await self.network.broadcast_agent_communication(
                    from_agent="risk",
                    to_agent="all",
                    message=f"⚠️ Strategy REJECTED: {risk_assessment.get('reason', 'High risk detected')}"
                )

                # Save rejected decision to history
                self._save_decision_to_history(status="rejected", reason=risk_assessment.get('reason'))
                await self._transition_state(OrchestratorState.IDLE)
                return

            await self.network.broadcast_agent_communication(
                from_agent="risk",
                to_agent="executor",
                message=f"✅ Strategy approved. Risk score: {risk_assessment.get('risk_score', 0):.2f}. "
                        f"Proceeding to execution."
            )

            # Step 4: Wait for User Approval (if configured)
            if not self.config["enable_auto_execute"]:
                await self._transition_state(OrchestratorState.WAITING_USER)
                self.logger.info("⏸ Waiting for user approval to execute trades...")

                await self.network.broadcast_agent_communication(
                    from_agent="system",
                    to_agent="user",
                    message="🤚 Strategy ready for execution. Please review and approve, or provide feedback."
                )

                # Wait for user input with timeout
                user_approved = await self._wait_for_user_approval()

                if not user_approved:
                    self.logger.info("User did not approve, skipping execution")
                    self._save_decision_to_history(status="user_rejected")
                    await self._transition_state(OrchestratorState.IDLE)
                    return

            # Step 5: Execute Trades
            await self._transition_state(OrchestratorState.EXECUTING)
            execution_result = await self._run_trade_execution(strategy)
            if not execution_result:
                self.logger.warning("Trade execution failed")
                await self._transition_state(OrchestratorState.IDLE)
                return

            self.current_decision["execution_result"] = execution_result
            await self.network.broadcast_agent_communication(
                from_agent="executor",
                to_agent="explainer",
                message=f"Executed {len(execution_result.get('trades', []))} trades. "
                        f"Total value: ${execution_result.get('total_value', 0):,.2f}"
            )

            # Step 6: Explain to User
            await self._transition_state(OrchestratorState.EXPLAINING)
            explanation = await self._run_explanation(execution_result)
            self.current_decision["explanation"] = explanation

            # Use refined output if available, otherwise use original
            if explanation.get("refined"):
                display_message = explanation["refined"]["terminal"]
            else:
                display_message = f"📝 {explanation.get('summary', 'Trades executed successfully.')}"

            await self.network.broadcast_agent_communication(
                from_agent="explainer",
                to_agent="user",
                message=display_message
            )

            # Save successful decision to history
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            self._save_decision_to_history(status="completed", duration=cycle_duration)

            self.logger.info(f"✅ Decision cycle completed in {cycle_duration:.1f}s")
            await self._transition_state(OrchestratorState.IDLE)

        except Exception as e:
            self.logger.error(f"Error in decision cycle: {e}", exc_info=True)
            self.error_count += 1
            await self._transition_state(OrchestratorState.ERROR)

    async def _run_market_scan(self) -> Optional[Dict[str, Any]]:
        """Run market scanning agent"""
        try:
            self.logger.info("🔍 Running market scan...")
            report = await self.agents["market"].scan_market()
            return report
        except Exception as e:
            self.logger.error(f"Market scan failed: {e}")
            return None

    async def _run_strategy_generation(self, market_report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run strategy generation agent"""
        try:
            self.logger.info("🧠 Generating strategy...")

            # Get current portfolio (would come from database/broker)
            current_portfolio = {
                "cash": 10000,
                "positions": {}
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
            return result

        except Exception as e:
            self.logger.error(f"Trade execution failed: {e}")
            return None

    async def _run_explanation(self, execution_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run explainer agent with output refinement"""
        try:
            self.logger.info("💬 Generating explanation...")

            explanation = await self.agents["explainer"].explain_trades(
                execution_result=execution_result
            )

            # Apply output refinement if enabled
            if self.refinement_pipeline and explanation.get("summary"):
                self.logger.info("✨ Refining output...")

                refined = self.refinement_pipeline.refine(
                    text=explanation["summary"],
                    format=self.config["refinement"]["format"]
                )

                # Add refined versions to explanation
                explanation["refined"] = {
                    "terminal": refined.terminal_output,
                    "web_html": refined.web_html,
                    "web_json": refined.web_json,
                    "markdown": refined.markdown,
                    "detected_terms": refined.detected_terms,
                    "definitions": refined.definitions
                }

                self.logger.info(f"   Detected {len(refined.detected_terms)} terms")
                self.logger.info(f"   Provided {len(refined.definitions)} definitions")

            return explanation
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
