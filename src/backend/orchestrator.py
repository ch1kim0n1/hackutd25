"""
APEX Multi-Agent Orchestrator
Coordinates all agents in the financial investment system with state machine workflow
"""

import asyncio
import logging
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from core.agent_network import AgentNetwork
from agents.market_agent import MarketAgent
from agents.strategy_agent import StrategyAgent
from agents.risk_agent import RiskAgent
from agents.executor_agent import ExecutorAgent
from agents.explainer_agent import ExplainerAgent
from agents.user_agent import UserAgent


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
    Main orchestrator that coordinates all AI agents in the APEX system.

    Features:
    - State machine workflow for agent coordination
    - Real-time agent communication via Redis pub/sub
    - Pause/resume for user interjections
    - Error recovery and retry logic
    - Decision history tracking
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
            "enable_auto_execute": False  # Require user approval for trades
        }

        # Error tracking
        self.error_count = 0
        self.max_errors = 10

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

            await self.network.broadcast_agent_communication(
                from_agent="explainer",
                to_agent="user",
                message=f"📝 {explanation.get('summary', 'Trades executed successfully.')}"
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

            # User profile (would come from database)
            user_profile = {
                "risk_tolerance": "moderate",
                "investment_style": "growth",
                "goals": ["long-term wealth building"],
                "time_horizon": "10+ years"
            }

            strategy = await self.agents["strategy"].generate_strategy(
                market_conditions=market_report,
                current_portfolio=current_portfolio,
                user_profile=user_profile
            )
            return strategy

        except Exception as e:
            self.logger.error(f"Strategy generation failed: {e}")
            return None

    async def _run_risk_check(self, strategy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run risk assessment agent"""
        try:
            self.logger.info("⚠️ Assessing risk...")

            # Current portfolio (would come from database/broker)
            current_portfolio = {
                "positions": {},
                "total_value": 10000
            }

            assessment = await self.agents["risk"].assess_strategy(
                strategy=strategy,
                current_portfolio=current_portfolio
            )
            return assessment

        except Exception as e:
            self.logger.error(f"Risk assessment failed: {e}")
            return None

    async def _run_trade_execution(self, strategy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run trade execution agent"""
        try:
            self.logger.info("⚡ Executing trades...")

            result = await self.agents["executor"].execute_rebalance(
                strategy=strategy,
                current_portfolio={}
            )
            return result

        except Exception as e:
            self.logger.error(f"Trade execution failed: {e}")
            return None

    async def _run_explanation(self, execution_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run explainer agent"""
        try:
            self.logger.info("💬 Generating explanation...")

            explanation = await self.agents["explainer"].explain_trades(
                execution_result=execution_result
            )
            return explanation

        except Exception as e:
            self.logger.error(f"Explanation failed: {e}")
            return {"summary": "Trades executed successfully."}

    async def _wait_for_user_approval(self, timeout: int = 60) -> bool:
        """Wait for user to approve strategy execution"""
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            # Check for user input in current decision
            if self.current_decision.get("user_input"):
                user_input = self.current_decision["user_input"]

                if user_input.get("action") == "approve":
                    return True
                elif user_input.get("action") == "reject":
                    return False

            await asyncio.sleep(0.5)

        # Timeout - default to not executing
        self.logger.warning("User approval timeout reached")
        return False

    async def _transition_state(self, new_state: OrchestratorState):
        """Transition to a new state and broadcast"""
        old_state = self.state
        self.state = new_state

        self.logger.info(f"State transition: {old_state.value} → {new_state.value}")

        await self.network.publish(
            topic="orchestrator.state",
            message={
                "old_state": old_state.value,
                "new_state": new_state.value,
                "timestamp": datetime.now().isoformat()
            }
        )

    def _save_decision_to_history(self, status: str, **kwargs):
        """Save current decision to history"""
        decision_record = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "data": self.current_decision.copy(),
            **kwargs
        }

        self.decision_history.append(decision_record)

        # Keep only last 100 decisions
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]

    async def _message_listener(self):
        """Background task to listen for agent messages and handle events"""
        self.logger.info("👂 Message listener started")

        while self.is_running:
            try:
                # Get recent messages from network
                messages = await self.network.get_message_history(limit=10)

                for msg in messages:
                    await self._handle_message(msg)

                await asyncio.sleep(0.5)

            except Exception as e:
                self.logger.error(f"Error in message listener: {e}")
                await asyncio.sleep(1)

    async def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming messages from agents"""
        msg_type = message.get("type")

        if msg_type == "user_input":
            # User provided input/feedback
            user_data = message.get("data", {})
            self.current_decision["user_input"] = user_data
            self.logger.info(f"📝 User input received: {user_data.get('action', 'feedback')}")

            # Process user feedback and inject into agent decision-making
            await self._process_user_feedback(user_data)

        elif msg_type == "agent_pause":
            # User wants to pause agents
            self.is_paused = True
            self.logger.info("⏸ Agents paused by user")
            await self.network.pause_agents("User requested pause")

        elif msg_type == "agent_resume":
            # User wants to resume agents
            user_input = message.get("data", {}).get("feedback", "")
            self.is_paused = False
            self.logger.info("▶️ Agents resumed by user")
            await self.network.resume_agents(user_input)

    async def _process_user_feedback(self, user_data: Dict[str, Any]):
        """
        Process user feedback and broadcast to relevant agents.
        This is KEY for the human-in-the-loop feature.
        """
        feedback_text = user_data.get("feedback", "")
        action = user_data.get("action", "comment")

        self.logger.info(f"Processing user feedback: {feedback_text[:100]}")

        # Broadcast user input to all agents
        await self.network.broadcast_agent_communication(
            from_agent="User",
            to_agent="All Agents",
            message=f"💭 User says: '{feedback_text}'"
        )

        # Parse user intent and route to appropriate agents
        feedback_lower = feedback_text.lower()

        if "risk" in feedback_lower or "conservative" in feedback_lower or "aggressive" in feedback_lower:
            # User is commenting on risk - inform Risk Agent
            await self.network.publish("user_risk_preference", {
                "feedback": feedback_text,
                "timestamp": datetime.now().isoformat()
            })
            self.logger.info("→ Routing to Risk Agent")

        if "strategy" in feedback_lower or "allocation" in feedback_lower or "buy" in feedback_lower:
            # User is commenting on strategy - inform Strategy Agent
            await self.network.publish("user_strategy_feedback", {
                "feedback": feedback_text,
                "timestamp": datetime.now().isoformat()
            })
            self.logger.info("→ Routing to Strategy Agent")

        if "market" in feedback_lower or "news" in feedback_lower or any(ticker in feedback_lower for ticker in ["spy", "qqq", "tlt", "tsla", "aapl"]):
            # User has market insights - inform Market Agent
            await self.network.publish("user_market_insight", {
                "feedback": feedback_text,
                "timestamp": datetime.now().isoformat()
            })
            self.logger.info("→ Routing to Market Agent")

    async def pause(self):
        """Pause the orchestrator"""
        self.is_paused = True
        await self.network.pause_agents()
        self.logger.info("⏸ Orchestrator paused")

    async def resume(self):
        """Resume the orchestrator"""
        self.is_paused = False
        await self.network.resume_agents()
        self.logger.info("▶️ Orchestrator resumed")

    async def stop(self):
        """Stop the orchestrator gracefully"""
        self.logger.info("🛑 Stopping orchestrator...")
        self.is_running = False

        # Save decision history before stopping
        self.logger.info(f"Saving {len(self.decision_history)} decisions to history")

        await self.network.close()
        self.logger.info("✅ Orchestrator stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status"""
        return {
            "state": self.state.value,
            "is_paused": self.is_paused,
            "is_running": self.is_running,
            "error_count": self.error_count,
            "decision_count": len(self.decision_history),
            "current_decision": self.current_decision,
            "config": self.config
        }

    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent decision history"""
        return self.decision_history[-limit:]
