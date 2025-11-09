"""
APEX Multi-Agent Orchestrator - WITH DELIBERATION PHASE & DEBATE ENGINE
Coordinates agents with a new "reasoning roundtable" where agents discuss strategy.
Includes formal debate mechanism with consensus voting and conflict resolution.
"""

from typing import Dict, List, Optional, Callable, Tuple, Any
from datetime import datetime
from openai import OpenAI
import time
from app.services.agent_debate_engine import AgentDebateEngine, AgentStance
from app.agents.agent_network import AgentNetwork
from app.core.types import OrchestratorState

# Re-export for legacy imports from server.py
__all__ = ["AgentOrchestrator", "Orchestrator", "OrchestratorState"]


class AgentOrchestrator:
    """
    Orchestrates multi-agent conversations for APEX investment system.
    
    NEW FLOW:
    1. Market Agent: Scan environment (once)
    2. Strategy Agent: Propose strategy (once)
    3. Risk Agent: Validate with Monte Carlo (once)
    4. DELIBERATION PHASE: Agents discuss via simulated conversation
       - User can interrupt anytime
       - Runs for max_deliberation_rounds or until user says "finalize"
    5. Final recommendation
    """
    
    def __init__(
        self,
        market_agent,
        strategy_agent,
        risk_agent,
        openrouter_api_key: str,
        model: str = "nvidia/llama-3.1-nemotron-70b-instruct",
        max_deliberation_rounds: int = 5,
        enable_logging: bool = True,
        require_user_approval: bool = True
    ):
        """
        Initialize orchestrator.
        
        Args:
            market_agent: MarketAgent instance
            strategy_agent: StrategyAgent instance
            risk_agent: RiskAgent instance
            openrouter_api_key: API key for deliberation phase
            model: Model to use for deliberation
            max_deliberation_rounds: Max discussion turns
            enable_logging: Print conversation
            require_user_approval: Wait for user approval
        """
        self.market_agent = market_agent
        self.strategy_agent = strategy_agent
        self.risk_agent = risk_agent
        
        # Client for deliberation phase
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key
        )
        self.model = model
        
        self.max_deliberation_rounds = max_deliberation_rounds
        self.logging_enabled = enable_logging
        self.require_user_approval = require_user_approval
        
        # Debate engine for formal voting and consensus
        self.debate_engine = AgentDebateEngine(
            agent_names=["market_agent", "strategy_agent", "risk_agent"],
            max_rounds=max_deliberation_rounds
        )
        
        # Conversation history
        self.initial_analysis = {}
        self.deliberation_history = []
        self.debate_transcript = []
        
        # User control
        self.user_interrupted = False
        self.user_message = None
        self.finalize_requested = False
        
        self.log("🎭 Orchestrator initialized")
        self.log(f"⚙️  Max deliberation rounds: {max_deliberation_rounds}")
    
    def log(self, message: str, agent: str = "ORCHESTRATOR"):
        """Print message if logging enabled"""
        if self.logging_enabled:
            timestamp = datetime.now().strftime("%H:%M:%S")
            emoji_map = {
                "ORCHESTRATOR": "🎭",
                "MARKET": "🔍",
                "STRATEGY": "🧠",
                "RISK": "⚠️",
                "DELIBERATION": "💬",
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
        Run complete analysis with deliberation phase.
        
        Returns:
            {
                'initial_analysis': {...},
                'deliberation_conversation': [...],
                'final_recommendation': {...},
                'approved': bool,
                'user_interrupted': bool,
                'deliberation_rounds': int
            }
        """
        self.log("="*60)
        self.log("🚀 STARTING MULTI-AGENT ANALYSIS")
        self.log("="*60)
        
        # Reset state
        self.initial_analysis = {}
        self.deliberation_history = []
        self.user_interrupted = False
        self.user_message = None
        self.finalize_requested = False
        
        # ===== PHASE 1: INITIAL ANALYSIS (FAST) =====
        self.log("\n📊 PHASE 1: INITIAL ANALYSIS")
        self.log("-"*60)
        
        # Market scan
        self.log("Market Agent analyzing environment...", "MARKET")
        market_report = self.market_agent.scan_market()
        self.log(f"Market: {self._extract_condition(market_report)}, VIX: {market_report['market_data']['vix']:.1f}", "MARKET")
        
        # Strategy proposal
        self.log("Strategy Agent generating proposal...", "STRATEGY")
        strategy = self.strategy_agent.generate_strategy(
            market_report=market_report,
            current_portfolio=current_portfolio,
            user_profile=user_profile,
            risk_constraints=risk_constraints,
            available_assets=available_assets
        )
        self.log(f"Strategy: {strategy['strategy_summary'][:60]}...", "STRATEGY")
        self.log(f"Confidence: {strategy['confidence']*100:.0f}%", "STRATEGY")
        
        # Risk validation
        self.log("Risk Agent running Monte Carlo...", "RISK")
        validation = self.risk_agent.validate_strategy(
            strategy=strategy,
            current_portfolio=current_portfolio,
            user_profile=user_profile,
            market_report=market_report,
            risk_constraints=risk_constraints
        )
        self.log(f"Risk: {validation['recommendation']}", "RISK")
        self.log(f"Approved: {'✅' if validation['approved'] else '❌'}", "RISK")
        
        # Store initial analysis
        self.initial_analysis = {
            'market_report': market_report,
            'strategy': strategy,
            'validation': validation,
            'timestamp': datetime.now()
        }
        
        # ===== PHASE 2: DELIBERATION (INTERACTIVE) =====
        self.log("\n💬 PHASE 2: AGENT DELIBERATION")
        self.log("-"*60)
        self.log("Agents will now discuss and refine the strategy.")
        self.log("You can interrupt anytime with feedback or say 'finalize' to conclude.")
        
        deliberation_result = self._run_deliberation(
            initial_analysis=self.initial_analysis,
            user_profile=user_profile,
            user_input_callback=user_input_callback
        )
        
        # ===== PHASE 3: FINAL RECOMMENDATION =====
        self.log("\n🏁 PHASE 3: FINAL RECOMMENDATION")
        self.log("-"*60)
        
        final_recommendation = self._generate_final_recommendation(
            initial_analysis=self.initial_analysis,
            deliberation_history=self.deliberation_history,
            current_portfolio=current_portfolio,      # ← ADD THIS
            user_profile=user_profile,                # ← ADD THIS
            risk_constraints=risk_constraints         # ← ADD THIS
        )
        
        # User approval if required
        user_approved = True
        if self.require_user_approval and not self.user_interrupted:
            user_approved = self._get_user_approval(final_recommendation, user_input_callback)
        
        # Build result
        result = {
            'initial_analysis': self.initial_analysis,
            'deliberation_conversation': self.deliberation_history,
            'final_recommendation': final_recommendation,
            'approved': validation['approved'] and user_approved,
            'user_interrupted': self.user_interrupted,
            'user_message': self.user_message,
            'deliberation_rounds': len(self.deliberation_history),
            'timestamp': datetime.now()
        }
        
        self.log(f"\n✅ Analysis complete: {'APPROVED' if result['approved'] else 'NOT APPROVED'}")
        self.log(f"Deliberation rounds: {result['deliberation_rounds']}")
        
        return result
    
    # ========================================
    # DELIBERATION PHASE (NEW!)
    # ========================================
    
    def _run_deliberation(
        self,
        initial_analysis: Dict,
        user_profile: Dict,
        user_input_callback: Optional[Callable]
    ) -> Dict:
        """
        Run deliberation phase where simulated agents discuss strategy.
        
        Uses ONE model with different system prompts to simulate 3 agents talking.
        """
        market_report = initial_analysis['market_report']
        strategy = initial_analysis['strategy']
        validation = initial_analysis['validation']
        
        # Build context for deliberation
        context = self._build_deliberation_context(
            market_report, strategy, validation, user_profile
        )
        
        # Run deliberation rounds
        for round_num in range(1, self.max_deliberation_rounds + 1):
            self.log(f"\n--- Deliberation Round {round_num}/{self.max_deliberation_rounds} ---", "DELIBERATION")
            
            # Check for user input before round
            if user_input_callback:
                user_response = user_input_callback(f"deliberation_round_{round_num}")
                
                if user_response:
                    if user_response.get('interrupted'):
                        self.user_interrupted = True
                        self.user_message = user_response.get('message', '')
                        self.log(f"User interrupted: {self.user_message}", "USER")
                        
                        # Add user message to conversation
                        self.deliberation_history.append({
                            'round': round_num,
                            'speaker': 'USER',
                            'message': self.user_message,
                            'timestamp': datetime.now()
                        })
                        
                        # Continue deliberation with user input
                        context += f"\n\nUSER INPUT: {self.user_message}\n"
                    
                    if user_response.get('finalize'):
                        self.finalize_requested = True
                        self.log("User requested finalization", "USER")
                        break
            
            # Generate deliberation turn (rotating between agent perspectives)
            agent_perspective = ['MARKET', 'STRATEGY', 'RISK'][round_num % 3]
            
            deliberation_turn = self._generate_deliberation_turn(
                agent_perspective=agent_perspective,
                context=context,
                round_num=round_num
            )
            
            # Add to history
            self.deliberation_history.append({
                'round': round_num,
                'speaker': agent_perspective,
                'message': deliberation_turn,
                'timestamp': datetime.now()
            })
            
            # Display
            self.log(f"{agent_perspective} Agent:", "DELIBERATION")
            self.log(deliberation_turn, "DELIBERATION")
            
            # Update context
            context += f"\n\n{agent_perspective} AGENT (Round {round_num}): {deliberation_turn}"
            
            # Check if finalization requested
            if self.finalize_requested or "FINAL RECOMMENDATION" in deliberation_turn.upper():
                self.log("Deliberation concluded", "DELIBERATION")
                break
        
        return {
            'rounds_completed': len(self.deliberation_history),
            'user_interrupted': self.user_interrupted,
            'finalized': self.finalize_requested or len(self.deliberation_history) >= self.max_deliberation_rounds
        }
    
    def _generate_deliberation_turn(
        self,
        agent_perspective: str,
        context: str,
        round_num: int
    ) -> str:
        """
        Generate one turn of deliberation from an agent's perspective.
        
        Uses system prompts to simulate different agent viewpoints.
        """
        # Define agent personas
        personas = {
            'MARKET': """You are the Market Agent. Your focus is on current market conditions, 
trends, and how external factors affect the investment environment. Reference the market 
data and news in your responses. Be data-driven and objective.""",
            
            'STRATEGY': """You are the Strategy Agent. Your focus is on portfolio construction, 
asset allocation, and ensuring the strategy aligns with user goals. You care about balance, 
diversification, and long-term success. Be solution-oriented.""",
            
            'RISK': """You are the Risk Agent. Your focus is on downside protection, constraint 
validation, and ensuring the strategy doesn't exceed acceptable risk levels. Reference Monte 
Carlo results and probability distributions. Be cautious but not alarmist."""
        }
        
        system_prompt = f"""{personas[agent_perspective]}

You are participating in a deliberation about an investment strategy. This is round {round_num}.

CRITICAL INSTRUCTIONS:
- Keep responses to 2-3 sentences maximum
- Be conversational and natural
- Reference specific numbers/data when relevant
- Build on what other agents said
- If you agree, briefly say why and add new insight
- If you disagree, explain your concern concisely
- Do NOT repeat information already stated
- Focus on moving the discussion forward

This is a discussion among professional advisors, not a presentation."""
        
        user_prompt = f"""Continue the deliberation based on the conversation so far:

{context}

Your turn ({agent_perspective} Agent perspective):"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,  # Keep it brief!
                temperature=0.7,
                extra_headers={
                    "HTTP-Referer": "https://apex-financial.com",
                    "X-Title": "APEX Deliberation"
                }
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.log(f"Error in deliberation: {e}", "DELIBERATION")
            return f"I agree with the current approach. ({agent_perspective})"
    
    def _build_deliberation_context(
        self,
        market_report: Dict,
        strategy: Dict,
        validation: Dict,
        user_profile: Dict
    ) -> str:
        """Build initial context for deliberation"""
        
        context = f"""INVESTMENT STRATEGY DELIBERATION

USER PROFILE:
- Risk Tolerance: {user_profile.get('risk_tolerance', 'moderate')}
- Time Horizon: {user_profile.get('time_horizon', 'long-term')}
- Experience: {user_profile.get('experience_level', 'beginner')}

MARKET CONDITIONS:
- S&P 500: ${market_report['market_data']['spy_price']:.2f} ({market_report['market_data']['spy_change_pct']:+.2f}%)
- VIX: {market_report['market_data']['vix']:.1f}
- Condition: {self._extract_condition(market_report)}

PROPOSED STRATEGY:
{strategy['strategy_summary']}

Target Allocation:
{self._format_simple_allocation(strategy['target_allocation'])}

RISK ANALYSIS:
- Recommendation: {validation['recommendation']}
- Median Outcome: ${validation['risk_analysis']['median_outcome']:,.0f}
- Max Drawdown: {validation['risk_analysis']['max_drawdown']*100:.1f}%
- Prob of Loss: {validation['risk_analysis']['prob_loss']*100:.1f}%
"""
        
        if validation['violations']:
            context += f"\nVIOLATIONS: {', '.join(validation['violations'])}"
        
        if validation['concerns']:
            context += f"\nCONCERNS: {', '.join(validation['concerns'])}"
        
        context += "\n\nBEGIN DELIBERATION:"
        
        return context
    
    # ========================================
    # FINAL RECOMMENDATION
    # ========================================
    
    def _generate_final_recommendation(
        self,
        initial_analysis: Dict,
        deliberation_history: List[Dict]
    ) -> Dict:
        """
        Generate final recommendation after deliberation.
        
        Synthesizes initial analysis + deliberation into final decision.
        """
        self.log("Synthesizing final recommendation...", "DELIBERATION")
        
        strategy = initial_analysis['strategy']
        validation = initial_analysis['validation']
        
        # Build deliberation summary
        deliberation_summary = "\n\n".join([
            f"{turn['speaker']}: {turn['message']}"
            for turn in deliberation_history
        ])
        
        # Generate synthesis
        prompt = f"""Based on the initial analysis and agent deliberation, provide a final recommendation.

INITIAL STRATEGY:
{strategy['strategy_summary']}

RISK ASSESSMENT:
{validation['recommendation']} - {validation['risk_analysis']['median_outcome']:,.0f} median outcome

DELIBERATION SUMMARY:
{deliberation_summary if deliberation_summary else 'No deliberation occurred'}

Provide a 2-3 sentence FINAL RECOMMENDATION that:
1. States the final decision (approve/modify/reject)
2. Highlights key reasoning from deliberation
3. Addresses main user concerns if any

Be concise and actionable."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are synthesizing a final investment recommendation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.6
            )
            
            final_text = response.choices[0].message.content.strip()
            
        except Exception as e:
            self.log(f"Error generating final recommendation: {e}")
            final_text = f"Recommend {validation['recommendation'].lower()} the proposed strategy."
        
        return {
            'recommendation_text': final_text,
            'strategy': strategy,
            'validation': validation,
            'deliberation_incorporated': len(deliberation_history) > 0,
            'timestamp': datetime.now()
        }
    
    # ========================================
    # USER APPROVAL
    # ========================================
    
    def _get_user_approval(
        self,
        final_recommendation: Dict,
        user_input_callback: Optional[Callable]
    ) -> bool:
        """Get final user approval"""
        self.log("Requesting user approval...", "USER")
        
        if user_input_callback:
            try:
                approval_response = user_input_callback('final_approval')
                
                if approval_response:
                    approved = approval_response.get('approved', False)
                    self.log(f"User {'approved' if approved else 'rejected'}", "USER")
                    return approved
            except Exception as e:
                self.log(f"Error getting approval: {e}")
        
        # Default: approve if validation passed
        return final_recommendation['validation']['approved']
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def _extract_condition(self, market_report: Dict) -> str:
        """Extract market condition"""
        analysis = market_report.get('analysis', '')
        for condition in ['Bullish', 'Bearish', 'Volatile', 'Mixed', 'Neutral']:
            if condition in analysis:
                return condition
        return 'Neutral'
    
    def _format_simple_allocation(self, allocation: Dict) -> str:
        """Simple allocation format"""
        lines = []
        for symbol, weight in sorted(allocation.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {symbol.upper()}: {weight*100:.0f}%")
        return "\n".join(lines)
    
    def get_conversation_summary(self, result: Dict) -> str:
        """Format conversation for display"""
        output = f"""
╔════════════════════════════════════════════════╗
║     🎭 MULTI-AGENT ANALYSIS SUMMARY           ║
╚════════════════════════════════════════════════╝

⏰ Completed: {result['timestamp'].strftime('%I:%M:%S %p')}
💬 Deliberation Rounds: {result['deliberation_rounds']}
{'👤 User Interrupted: ' + result['user_message'] if result['user_interrupted'] else ''}
{'✅ APPROVED' if result['approved'] else '❌ NOT APPROVED'}

📊 INITIAL ANALYSIS:
"""
        
        strategy = result['initial_analysis']['strategy']
        validation = result['initial_analysis']['validation']
        
        output += f"   Strategy: {strategy['strategy_summary'][:70]}...\n"
        output += f"   Risk: {validation['recommendation']}\n\n"
        
        if result['deliberation_conversation']:
            output += "💬 DELIBERATION:\n"
            for turn in result['deliberation_conversation']:
                output += f"   [{turn['speaker']}]: {turn['message'][:100]}...\n"
            output += "\n"
        
        output += "🏁 FINAL RECOMMENDATION:\n"
        output += f"   {result['final_recommendation']['recommendation_text']}\n"
        output += "\n" + "="*50 + "\n"
        
        return output
    # orchestrator.py

    def _generate_final_recommendation(
      self,
      initial_analysis: Dict,
      deliberation_history: List[Dict],
      current_portfolio: Dict,
      user_profile: Dict,
      risk_constraints: Optional[Dict]
  ) -> Dict:
        """
        Generate final recommendation after deliberation.
        
        NOW: Synthesizes a REVISED strategy incorporating deliberation insights.
        """
        self.log("Synthesizing final recommendation with revised strategy...", "DELIBERATION")
        
        strategy = initial_analysis['strategy']
        validation = initial_analysis['validation']
        market_report = initial_analysis['market_report']
        
        # If no deliberation occurred, just return original
        if not deliberation_history:
            self.log("No deliberation - using original strategy", "DELIBERATION")
            return {
                'recommendation_text': strategy['rationale'],
                'strategy': strategy,
                'validation': validation,
                'deliberation_incorporated': False,
                'revised': False,
                'timestamp': datetime.now()
            }
        
        # Build deliberation summary
        deliberation_summary = "\n".join([
            f"{turn['speaker']}: {turn['message']}"
            for turn in deliberation_history
        ])
        
        # ===== NEW: SYNTHESIZE REVISED ALLOCATION =====
        revised_allocation = self._synthesize_revised_allocation(
            original_strategy=strategy,
            validation=validation,
            deliberation_summary=deliberation_summary,
            user_profile=user_profile
        )
        
        # If allocation changed, re-validate and regenerate trades
        if revised_allocation != strategy['target_allocation']:
            self.log("Allocation revised based on deliberation - re-validating...", "DELIBERATION")
            
            # Create revised strategy object
            revised_strategy = {
                'strategy_summary': strategy['strategy_summary'],
                'target_allocation': revised_allocation,
                'confidence': strategy['confidence'],
                'risk_assessment': strategy['risk_assessment']
            }
            
            # Re-calculate trades for revised allocation
            revised_strategy['recommended_trades'] = self._generate_trades_for_allocation(
                target_allocation=revised_allocation,
                current_portfolio=current_portfolio
            )
            
            # Re-run Risk Agent on revised strategy
            revised_validation = self.risk_agent.validate_strategy(
                strategy=revised_strategy,
                current_portfolio=current_portfolio,
                user_profile=user_profile,
                market_report=market_report,
                risk_constraints=risk_constraints
            )
            
            self.log(f"Revised strategy: {revised_validation['recommendation']}", "RISK")
            
            # Generate final explanation
            final_text = self._generate_final_explanation(
                original_strategy=strategy,
                revised_strategy=revised_strategy,
                deliberation_summary=deliberation_summary
            )
            
            return {
                'recommendation_text': final_text,
                'strategy': revised_strategy,      # ✅ NEW revised strategy!
                'validation': revised_validation,  # ✅ NEW validation!
                'original_strategy': strategy,     # Keep original for comparison
                'deliberation_incorporated': True,
                'revised': True,
                'timestamp': datetime.now()
            }
        
        else:
            # Allocation didn't change, but update explanation
            self.log("Deliberation confirmed original strategy", "DELIBERATION")
            
            final_text = self._generate_final_explanation(
                original_strategy=strategy,
                revised_strategy=None,
                deliberation_summary=deliberation_summary
            )
            
            return {
                'recommendation_text': final_text,
                'strategy': strategy,
                'validation': validation,
                'deliberation_incorporated': True,
                'revised': False,
                'timestamp': datetime.now()
            }


    def _synthesize_revised_allocation(
    self,
    original_strategy: Dict,
    validation: Dict,
    deliberation_summary: str,
    user_profile: Dict
) -> Dict[str, float]:
      """
      NEW METHOD: Use AI to synthesize a revised allocation based on deliberation.
      
      Returns:
          Dict of {symbol: weight} - revised target allocation
      """
      original_allocation = original_strategy['target_allocation']
      
      prompt = f"""Based on the agent deliberation, determine the FINAL allocation.

  ORIGINAL PROPOSED ALLOCATION:
  {self._format_simple_allocation(original_allocation)}

  RISK ASSESSMENT:
  - Recommendation: {validation['recommendation']}
  - Violations: {len(validation['violations'])}
  - Concerns: {len(validation['concerns'])}

  AGENT DELIBERATION:
  {deliberation_summary}

  USER PROFILE:
  - Risk Tolerance: {user_profile.get('risk_tolerance', 'moderate')}
  - Time Horizon: {user_profile.get('time_horizon', 'long-term')}

  TASK: Provide the FINAL allocation incorporating insights from deliberation.

  If deliberation suggested changes (e.g., "increase bonds", "reduce tech exposure"), 
  incorporate them. If deliberation confirmed the original, keep it.

  Respond ONLY with JSON:
  {{
      "SPY": 0.50,
      "TLT": 0.30,
      "GLD": 0.10,
      "cash": 0.10
  }}

  CRITICAL:
  - Must sum to 1.0 (100%)
  - Only include symbols from original allocation or standard ETFs (SPY, QQQ, TLT, IEF, AGG, GLD, SLV, VNQ)
  - Use the EXACT format shown above
  - No explanation, just the JSON object"""

      try:
          response = self.client.chat.completions.create(
              model=self.model,
              messages=[
                  {
                      "role": "system", 
                      "content": "You synthesize investment allocations. Output ONLY valid JSON."
                  },
                  {"role": "user", "content": prompt}
              ],
              max_tokens=300,
              temperature=0.3  # Lower temp for consistent JSON
          )
          
          response_text = response.choices[0].message.content.strip()
          
          # Parse JSON (handle markdown code blocks)
          import json
          response_text = response_text.replace('```json', '').replace('```', '').strip()
          revised_allocation = json.loads(response_text)
          
          # Validate allocation
          total = sum(revised_allocation.values())
          if not (0.95 <= total <= 1.05):
              self.log(f"⚠️  Allocation sum {total:.2f} - normalizing", "DELIBERATION")
              # Normalize
              revised_allocation = {k: v/total for k, v in revised_allocation.items()}
          
          # Log changes
          self._log_allocation_changes(original_allocation, revised_allocation)
          
          return revised_allocation
          
      except Exception as e:
          self.log(f"❌ Error synthesizing allocation: {e} - using original", "DELIBERATION")
          return original_allocation


    def _generate_trades_for_allocation(
        self,
        target_allocation: Dict[str, float],
        current_portfolio: Dict
    ) -> List[Dict]:
        """
        NEW METHOD: Generate trade list to reach target allocation.
        
        This replicates what Strategy Agent does internally.
        """
        trades = []
        portfolio_value = current_portfolio['total_value']
        current_positions = current_portfolio.get('positions', {})
        
        # Calculate target dollar amounts
        for symbol, target_weight in target_allocation.items():
            if symbol == 'cash':
                continue  # Skip cash for trades
            
            target_value = portfolio_value * target_weight
            
            # Get current position
            current_position = current_positions.get(symbol, {})
            current_value = current_position.get('value', 0)
            current_shares = current_position.get('shares', 0)
            
            # Estimate share price
            if current_shares > 0:
                share_price = current_value / current_shares
            else:
                # Rough estimates for common ETFs
                share_price_estimates = {
                    'SPY': 475, 'QQQ': 400, 'IWM': 200,
                    'TLT': 100, 'IEF': 100, 'AGG': 100,
                    'GLD': 180, 'SLV': 22, 'VNQ': 90
                }
                share_price = share_price_estimates.get(symbol, 100)
            
            # Calculate shares needed
            target_shares = int(target_value / share_price)
            shares_diff = target_shares - current_shares
            
            # Generate trade if meaningful difference (>5% change or >$500)
            value_diff = abs(target_value - current_value)
            pct_diff = abs(target_value - current_value) / portfolio_value if portfolio_value > 0 else 0
            
            if abs(shares_diff) >= 1 and (value_diff > 500 or pct_diff > 0.05):
                if shares_diff > 0:
                    trades.append({
                        'action': 'BUY',
                        'symbol': symbol,
                        'shares': shares_diff,
                        'reason': f'Increase {symbol} to {target_weight*100:.0f}% allocation',
                        'urgency': 'medium'
                    })
                else:
                    trades.append({
                        'action': 'SELL',
                        'symbol': symbol,
                        'shares': abs(shares_diff),
                        'reason': f'Reduce {symbol} to {target_weight*100:.0f}% allocation',
                        'urgency': 'medium'
                    })
        
        return trades


    def _generate_final_explanation(
        self,
        original_strategy: Dict,
        revised_strategy: Optional[Dict],
        deliberation_summary: str
    ) -> str:
        """
        NEW METHOD: Generate explanation of final recommendation.
        """
        if revised_strategy:
            # Strategy was revised
            prompt = f"""Explain the FINAL investment recommendation after deliberation.

    ORIGINAL ALLOCATION:
    {self._format_simple_allocation(original_strategy['target_allocation'])}

    REVISED ALLOCATION (after deliberation):
    {self._format_simple_allocation(revised_strategy['target_allocation'])}

    DELIBERATION SUMMARY:
    {deliberation_summary}

    Provide a 2-3 sentence explanation that:
    1. States what changed and why
    2. Highlights the key insight from deliberation
    3. Confirms this is the final recommendation

    Be concise and clear."""
        else:
            # Strategy confirmed
            prompt = f"""Explain why the original strategy was confirmed after deliberation.

    ALLOCATION:
    {self._format_simple_allocation(original_strategy['target_allocation'])}

    DELIBERATION SUMMARY:
    {deliberation_summary}

    Provide 2-3 sentences explaining:
    1. Why agents agreed with the original strategy
    2. What deliberation confirmed
    3. Why this is sound

    Be concise and confident."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You explain investment decisions clearly."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.6
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.log(f"Error generating explanation: {e}")
            if revised_strategy:
                return "After deliberation, the allocation was adjusted to better balance risk and return."
            else:
                return "After deliberation, agents confirmed the original strategy is optimal."


    def _log_allocation_changes(
        self,
        original: Dict[str, float],
        revised: Dict[str, float]
    ):
        """Log what changed in allocation"""
        changes = []
        
        all_symbols = set(original.keys()) | set(revised.keys())
        
        for symbol in all_symbols:
            orig_weight = original.get(symbol, 0)
            new_weight = revised.get(symbol, 0)
            
            if abs(new_weight - orig_weight) > 0.01:  # More than 1% change
                change = new_weight - orig_weight
                changes.append(f"{symbol}: {orig_weight*100:.0f}% → {new_weight*100:.0f}% ({change*100:+.0f}%)")
        
        if changes:
            self.log("📊 Allocation changes:", "DELIBERATION")
            for change in changes:
                self.log(f"   • {change}", "DELIBERATION")
        else:
            self.log("📊 No allocation changes - original confirmed", "DELIBERATION")

    # ========================================
    # FORMAL DEBATE & VOTING
    # ========================================

    def run_formal_debate_on_decision(
        self,
        topic: str,
        market_report: Dict,
        strategy: Dict,
        validation: Dict,
        user_profile: Dict
    ) -> Dict[str, Any]:
        """
        Run formal debate with voting and consensus.
        
        Args:
            topic: What to debate (e.g., "execute_trade", "rebalance_portfolio")
            market_report: Market conditions
            strategy: Proposed strategy
            validation: Risk assessment
            user_profile: User preferences
        
        Returns:
            Debate result with consensus decision
        """
        self.log(f"\n🗳️  FORMAL DEBATE: {topic}", "DELIBERATION")
        self.log("="*60)
        
        # Start debate
        debate_round = self.debate_engine.start_debate(topic)
        
        # Get agent positions
        # Market Agent: Focus on market conditions
        market_position, market_confidence = self._get_market_agent_position(
            market_report, strategy, user_profile
        )
        self.debate_engine.record_position(
            "market_agent",
            market_position,
            f"Market conditions: {market_report.get('market_condition', 'unknown')}. VIX: {market_report.get('market_data', {}).get('vix', 0):.1f}",
            market_confidence
        )
        self.log(f"Market Agent: {market_position.value.upper()} ({market_confidence:.0%})", "DELIBERATION")
        
        # Strategy Agent: Focus on strategy fit
        strategy_position, strategy_confidence = self._get_strategy_agent_position(
            strategy, user_profile
        )
        self.debate_engine.record_position(
            "strategy_agent",
            strategy_position,
            f"Strategy confidence: {strategy.get('confidence', 0.5):.1%}. Fit: {strategy.get('strategy_summary', 'unknown')}",
            strategy_confidence
        )
        self.log(f"Strategy Agent: {strategy_position.value.upper()} ({strategy_confidence:.0%})", "DELIBERATION")
        
        # Risk Agent: Focus on risk assessment
        risk_position, risk_confidence = self._get_risk_agent_position(
            validation, user_profile
        )
        self.debate_engine.record_position(
            "risk_agent",
            risk_position,
            f"Risk approved: {validation.get('approved', False)}. Recommendation: {validation.get('recommendation', 'unknown')}",
            risk_confidence
        )
        self.log(f"Risk Agent: {risk_position.value.upper()} ({risk_confidence:.0%})", "DELIBERATION")
        
        # Check consensus
        consensus_reached, consensus_data = self.debate_engine.check_consensus()
        
        self.log(f"\nConsensus Level: {consensus_data['consensus_level']:.0%}", "DELIBERATION")
        self.log(f"Decision: {consensus_data['decision'].upper()}", "DELIBERATION")
        
        # Store transcript
        self.debate_transcript.append(consensus_data)
        
        return {
            "topic": topic,
            "consensus_reached": consensus_reached,
            "consensus_level": consensus_data["consensus_level"],
            "decision": consensus_data["decision"],
            "positions": {
                "market": market_position.value,
                "strategy": strategy_position.value,
                "risk": risk_position.value
            },
            "timestamp": datetime.now().isoformat()
        }

    def _get_market_agent_position(
        self,
        market_report: Dict,
        strategy: Dict,
        user_profile: Dict
    ) -> Tuple[AgentStance, float]:
        """Determine Market Agent's position on a decision"""
        vix = market_report.get('market_data', {}).get('vix', 20)
        market_condition = market_report.get('market_condition', 'normal')
        
        # Market Agent is conservative when VIX is high
        if vix > 30:  # High volatility
            confidence = min(0.9, vix / 50)
            return AgentStance.DISAGREE, confidence
        elif vix > 20:  # Moderate volatility
            confidence = 0.7
            return AgentStance.NEUTRAL, confidence
        else:  # Low volatility
            confidence = 0.8
            return AgentStance.AGREE, confidence

    def _get_strategy_agent_position(
        self,
        strategy: Dict,
        user_profile: Dict
    ) -> Tuple[AgentStance, float]:
        """Determine Strategy Agent's position"""
        confidence = strategy.get('confidence', 0.5)
        
        if confidence > 0.8:
            return AgentStance.AGREE, confidence
        elif confidence > 0.6:
            return AgentStance.NEUTRAL, confidence
        else:
            return AgentStance.DISAGREE, 1.0 - confidence

    def _get_risk_agent_position(
        self,
        validation: Dict,
        user_profile: Dict
    ) -> Tuple[AgentStance, float]:
        """Determine Risk Agent's position"""
        approved = validation.get('approved', False)
        confidence = validation.get('confidence', 0.5)
        
        if approved:
            return AgentStance.AGREE, confidence
        else:
            return AgentStance.DISAGREE, confidence


# -----------------------------------------------------------------------------
# Minimal compatibility wrapper expected by server.py
# -----------------------------------------------------------------------------
class Orchestrator:
    """
    Minimal orchestrator wrapper to satisfy the FastAPI server interface.
    Exposes: initialize(), start(), stop(), pause(), resume(), get_status(),
    .network, .is_running, .config
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.network = AgentNetwork()
        self.is_running: bool = False
        self.is_paused: bool = False
        self._state: OrchestratorState = OrchestratorState.IDLE
        self.config: Dict[str, Any] = {}
        self._error_count: int = 0
        self._decision_count: int = 0

    async def initialize(self):
        await self.network.initialize()
        self._state = OrchestratorState.INITIALIZING
        # Transition to idle once initialized
        self._state = OrchestratorState.IDLE

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self._state.value if hasattr(self._state, "value") else str(self._state),
            "is_paused": self.is_paused,
            "is_running": self.is_running,
            "error_count": self._error_count,
            "decision_count": self._decision_count,
        }

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._state = OrchestratorState.ANALYSIS
        # Emit a bootstrap message for demo visibility
        await self.network.publish("agent_communication", {
            "type": "system",
            "from": "system",
            "to": "all",
            "message": "Orchestrator started. Agents assembling.",
            "timestamp": datetime.now().isoformat()
        })

    async def stop(self):
        if not self.is_running:
            return
        self.is_running = False
        self._state = OrchestratorState.STOPPED
        await self.network.publish("agent_communication", {
            "type": "system",
            "from": "system",
            "to": "all",
            "message": "Orchestrator stopped.",
            "timestamp": datetime.now().isoformat()
        })

    async def pause(self):
        self.is_paused = True
        self._state = OrchestratorState.PAUSED
        await self.network.pause_agents("User requested pause")

    async def resume(self):
        self.is_paused = False
        self._state = OrchestratorState.ANALYSIS
        await self.network.resume_agents("Resuming after pause")

