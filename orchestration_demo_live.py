"""
APEX AGENT ORCHESTRATION LIVE DEMO
Real API calls to OpenRouter with agent-to-agent communication.
Demonstrates the professional output styling and multi-agent reasoning.

Run with: python orchestration_demo_live.py
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from openai import OpenAI
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

# Get API key from environment or .env file
import sys
from pathlib import Path

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Try loading from .env file if not in environment
if not OPENROUTER_API_KEY:
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY="):
                    OPENROUTER_API_KEY = line.split("=", 1)[1].strip().strip("'\"")
                    break

# Try .env.example as fallback
if not OPENROUTER_API_KEY:
    env_example = Path(".env.example")
    if env_example.exists():
        with open(env_example, "r") as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY="):
                    OPENROUTER_API_KEY = line.split("=", 1)[1].strip().strip("'\"")
                    if OPENROUTER_API_KEY and not OPENROUTER_API_KEY.startswith("YOUR"):
                        break

if not OPENROUTER_API_KEY:
    print("\n" + "=" * 80)
    print("ERROR: OPENROUTER_API_KEY not found")
    print("=" * 80)
    print("\nTo fix this, choose ONE of these methods:\n")
    
    print("METHOD 1: Set Environment Variable (Recommended)")
    print("  PowerShell:")
    print("    $env:OPENROUTER_API_KEY = 'sk-or-v1-your-key-here'\n")
    
    print("METHOD 2: Create .env file")
    print("  Create file: .env")
    print("  Content:")
    print("    OPENROUTER_API_KEY=sk-or-v1-your-key-here\n")
    
    print("METHOD 3: Use setup script")
    print("  python setup_api_key.py\n")
    
    print("To get an API key:")
    print("  1. Visit https://openrouter.ai")
    print("  2. Sign up or login")
    print("  3. Go to https://openrouter.ai/keys")
    print("  4. Click 'Create New Key'")
    print("  5. Copy your key (starts with 'sk-or-v1-')\n")
    print("=" * 80 + "\n")
    exit(1)

# Model configuration
MODEL = "nvidia/llama-3.1-nemotron-70b-instruct"
BASE_URL = "https://openrouter.ai/api/v1"

# ============================================================================
# DEMONSTRATION CONTEXT
# ============================================================================

DEMO_PORTFOLIO = {
    "total_value": 100000,
    "cash": 15000,
    "positions": {
        "SPY": {"shares": 100, "price": 450.00, "value": 45000},
        "AAPL": {"shares": 50, "price": 150.00, "value": 7500},
        "BND": {"shares": 250, "price": 80.00, "value": 20000},
        "GLD": {"shares": 40, "price": 200.00, "value": 8000}
    }
}

DEMO_MARKET_CONDITIONS = """
Current Market Environment:
- VIX (Volatility): 18.5 (elevated)
- Fed Stance: Hawkish (potential rate hikes)
- Treasury Yields: 10Y at 4.5%
- Inflation: 3.8% YoY (cooling trend)
- Economic Growth: Solid Q3 GDP at 2.8%
- Corporate Earnings: Mixed, tech sector under pressure
- Sector Performance: Tech -5%, Healthcare +2%, Utilities +1%
"""

DEMO_USER_PROFILE = {
    "name": "Conservative Growth Investor",
    "risk_tolerance": "moderate",
    "time_horizon": "long-term (10+ years)",
    "goals": ["retirement planning", "steady growth"],
    "investment_style": "balanced",
    "preferred_sectors": ["healthcare", "technology", "industrials"],
    "max_drawdown_tolerance": 0.20
}

# ============================================================================
# AGENT COMMUNICATION SYSTEM
# ============================================================================

class ProfessionalAgent:
    """
    Professional AI Agent that communicates via OpenRouter API.
    Implements clean, structured message passing.
    """
    
    def __init__(self, name: str, role: str, emoji: str = "🤖"):
        self.name = name
        self.role = role
        self.emoji = emoji
        self.client = OpenAI(
            base_url=BASE_URL,
            api_key=OPENROUTER_API_KEY
        )
        self.message_history = []
        self.current_analysis = None
        
    def log(self, message: str, level: str = "INFO"):
        """Print professional log message"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        level_symbol = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ANALYSIS": "📊",
            "PROPOSAL": "📋",
            "WARNING": "⚠️",
            "ERROR": "❌"
        }.get(level, "•")
        print(f"[{timestamp}] {self.emoji} {self.name:20} | {level_symbol} {level:10} | {message}")
    
    def call_api(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        """
        Call OpenRouter API with professional error handling.
        """
        try:
            self.log(f"Calling OpenRouter API ({MODEL})", "INFO")
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens,
                top_p=0.9
            )
            
            elapsed = time.time() - start_time
            content = response.choices[0].message.content
            
            # Log token usage
            usage = response.usage
            self.log(
                f"API response received ({elapsed:.2f}s, "
                f"{usage.prompt_tokens} in, {usage.completion_tokens} out)",
                "SUCCESS"
            )
            
            return content
            
        except Exception as e:
            self.log(f"API Error: {str(e)}", "ERROR")
            raise
    
    def format_output(self, title: str, content: str) -> str:
        """Format professional output with clear structure"""
        separator = "─" * 78
        return f"\n{separator}\n{title}\n{separator}\n{content}\n"


# ============================================================================
# SPECIALIZED AGENTS
# ============================================================================

class MarketAgent(ProfessionalAgent):
    """Analyzes market conditions and opportunities"""
    
    def __init__(self):
        super().__init__("Market Agent", "Market Analysis", "🔍")
    
    def analyze_market(self, market_data: str) -> Dict:
        """Analyze current market conditions using OpenRouter"""
        self.log("Analyzing market environment", "ANALYSIS")
        
        system_prompt = """You are a professional market analyst for an investment firm.
Analyze the provided market data and provide:
1. Market sentiment (bullish/bearish/neutral)
2. Key risks and opportunities
3. Sector rotation recommendations
4. Impact on current portfolio (moderate risk tolerance, balanced allocation)

Keep response concise and professional. Focus on actionable insights."""
        
        user_prompt = f"""Analyze this market environment:

{market_data}

Portfolio Profile:
- Risk Tolerance: Moderate
- Time Horizon: Long-term
- Current Holdings: 45% equities, 20% bonds, 8% gold, 15% cash

Provide analysis and recommendations."""
        
        analysis = self.call_api(system_prompt, user_prompt)
        
        # Store result
        self.current_analysis = {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis
        }
        
        print(self.format_output("📊 MARKET ANALYSIS", analysis))
        return self.current_analysis


class StrategyAgent(ProfessionalAgent):
    """Develops portfolio strategy based on market analysis"""
    
    def __init__(self):
        super().__init__("Strategy Agent", "Portfolio Strategy", "🧠")
    
    def propose_strategy(self, market_analysis: str, portfolio: Dict, profile: Dict) -> Dict:
        """Propose portfolio strategy using OpenRouter"""
        self.log("Developing portfolio strategy", "PROPOSAL")
        
        # Calculate current allocation
        total = portfolio["total_value"]
        allocations = {k: (v["value"] / total) for k, v in portfolio["positions"].items()}
        allocations["cash"] = portfolio["cash"] / total
        
        portfolio_str = "\n".join([
            f"  {k}: {v/total:.1%} (${v:.0f})" 
            for k, v in allocations.items()
        ])
        
        system_prompt = """You are a professional portfolio strategist.
Based on market analysis and current holdings, recommend:
1. Target asset allocation
2. Specific trades (buy/sell actions)
3. Rebalancing rationale
4. Risk mitigation strategies

Provide specific, actionable recommendations."""
        
        user_prompt = f"""Based on this market analysis:
{market_analysis}

Current Portfolio (${total:,.0f}):
{portfolio_str}

User Profile:
- Risk Tolerance: {profile['risk_tolerance']}
- Time Horizon: {profile['time_horizon']}
- Goals: {', '.join(profile['goals'])}

Recommend a rebalancing strategy."""
        
        strategy = self.call_api(system_prompt, user_prompt)
        
        self.current_analysis = {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy
        }
        
        print(self.format_output("🧠 PORTFOLIO STRATEGY", strategy))
        return self.current_analysis


class RiskAgent(ProfessionalAgent):
    """Validates strategy against risk constraints"""
    
    def __init__(self):
        super().__init__("Risk Agent", "Risk Validation", "⚠️")
    
    def validate_strategy(self, strategy: str, market_analysis: str) -> Dict:
        """Validate strategy for risk using OpenRouter"""
        self.log("Validating risk parameters", "ANALYSIS")
        
        system_prompt = """You are a professional risk manager and compliance officer.
Evaluate the proposed strategy for:
1. Drawdown risk (max acceptable loss)
2. Concentration risk (position sizing)
3. Liquidity risk (cash reserves)
4. Volatility alignment (risk tolerance match)
5. Regulatory/compliance concerns

Provide clear pass/fail assessment with recommendations."""
        
        user_prompt = f"""Validate this portfolio strategy:

{strategy}

Market Context:
{market_analysis}

Risk Constraints:
- Max Drawdown: 20%
- Max Single Position: 50%
- Min Cash Reserve: 5%
- Risk Tolerance: Moderate

Provide risk assessment."""
        
        validation = self.call_api(system_prompt, user_prompt)
        
        self.current_analysis = {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "validation": validation
        }
        
        print(self.format_output("⚠️ RISK VALIDATION", validation))
        return self.current_analysis


class ExecutorAgent(ProfessionalAgent):
    """Prepares execution plan for trades"""
    
    def __init__(self):
        super().__init__("Executor Agent", "Trade Execution", "⚡")
    
    def prepare_execution(self, strategy: str, validation: str) -> Dict:
        """Prepare trade execution plan using OpenRouter"""
        self.log("Preparing execution plan", "PROPOSAL")
        
        system_prompt = """You are a professional trade executor.
Create a detailed execution plan including:
1. Order sequence (priority and timing)
2. Execution prices and limits
3. Size and allocation for each trade
4. Execution timeframe
5. Monitoring checkpoints

Provide a clear, step-by-step execution roadmap."""
        
        user_prompt = f"""Based on this approved strategy:

{strategy}

With risk validation:
{validation}

Create a specific execution plan with:
- Which trades to execute
- Order and timing
- Price targets
- Position sizing
- Stop losses

Format as actionable execution checklist."""
        
        execution_plan = self.call_api(system_prompt, user_prompt)
        
        self.current_analysis = {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "execution_plan": execution_plan
        }
        
        print(self.format_output("⚡ EXECUTION PLAN", execution_plan))
        return self.current_analysis


class ExplainerAgent(ProfessionalAgent):
    """Explains reasoning and recommendations in plain language"""
    
    def __init__(self):
        super().__init__("Explainer Agent", "Communication", "💬")
    
    def explain_recommendation(self, market: str, strategy: str, risk: str, execution: str) -> Dict:
        """Explain the complete recommendation using OpenRouter"""
        self.log("Generating executive summary", "SUCCESS")
        
        system_prompt = """You are a professional financial advisor explaining to a client.
Create a clear, jargon-free explanation covering:
1. What's happening in the market (in simple terms)
2. Why we're making these changes
3. What will happen to their portfolio
4. Key risks to watch
5. What success looks like

Use professional but accessible language."""
        
        user_prompt = f"""Create a client-friendly explanation for:

Market Situation:
{market[:200]}...

Recommended Strategy:
{strategy[:200]}...

Risk Assessment:
{risk[:200]}...

Your Task:
Write a one-page summary a financial advisor would give to a client explaining:
- Market situation
- Portfolio changes
- Why these changes help their goals
- Risks and how we manage them
- Next steps

Keep it professional and clear."""
        
        explanation = self.call_api(system_prompt, user_prompt, max_tokens=600)
        
        self.current_analysis = {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "explanation": explanation
        }
        
        print(self.format_output("💬 CLIENT SUMMARY", explanation))
        return self.current_analysis


# ============================================================================
# ORCHESTRATION ENGINE
# ============================================================================

class OrchestrationDemo:
    """Coordinates multi-agent workflow"""
    
    def __init__(self):
        self.market_agent = MarketAgent()
        self.strategy_agent = StrategyAgent()
        self.risk_agent = RiskAgent()
        self.executor_agent = ExecutorAgent()
        self.explainer_agent = ExplainerAgent()
        
        self.results = {}
    
    def log_header(self, title: str):
        """Print formatted header"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")
    
    def run(self):
        """Execute complete orchestration workflow"""
        self.log_header("APEX MULTI-AGENT INVESTMENT ORCHESTRATION - LIVE DEMO")
        
        print(f"Configuration:")
        print(f"  Model: {MODEL}")
        print(f"  Base URL: {BASE_URL}")
        print(f"  Portfolio Value: ${DEMO_PORTFOLIO['total_value']:,.0f}")
        print(f"  Risk Profile: {DEMO_USER_PROFILE['risk_tolerance']}")
        print("\n" + "─" * 80 + "\n")
        
        try:
            # ===== PHASE 1: MARKET ANALYSIS =====
            self.log_header("PHASE 1: MARKET ANALYSIS")
            market_result = self.market_agent.analyze_market(DEMO_MARKET_CONDITIONS)
            self.results["market"] = market_result
            time.sleep(1)  # Brief pause between agents
            
            # ===== PHASE 2: STRATEGY DEVELOPMENT =====
            self.log_header("PHASE 2: STRATEGY DEVELOPMENT")
            strategy_result = self.strategy_agent.propose_strategy(
                market_result["analysis"],
                DEMO_PORTFOLIO,
                DEMO_USER_PROFILE
            )
            self.results["strategy"] = strategy_result
            time.sleep(1)
            
            # ===== PHASE 3: RISK VALIDATION =====
            self.log_header("PHASE 3: RISK VALIDATION")
            risk_result = self.risk_agent.validate_strategy(
                strategy_result["strategy"],
                market_result["analysis"]
            )
            self.results["risk"] = risk_result
            time.sleep(1)
            
            # ===== PHASE 4: EXECUTION PLANNING =====
            self.log_header("PHASE 4: EXECUTION PLANNING")
            execution_result = self.executor_agent.prepare_execution(
                strategy_result["strategy"],
                risk_result["validation"]
            )
            self.results["execution"] = execution_result
            time.sleep(1)
            
            # ===== PHASE 5: CLIENT COMMUNICATION =====
            self.log_header("PHASE 5: CLIENT COMMUNICATION")
            explanation_result = self.explainer_agent.explain_recommendation(
                market_result["analysis"],
                strategy_result["strategy"],
                risk_result["validation"],
                execution_result["execution_plan"]
            )
            self.results["explanation"] = explanation_result
            
            # ===== SUMMARY =====
            self.log_header("ORCHESTRATION COMPLETE")
            self._print_summary()
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Orchestration interrupted by user")
        except Exception as e:
            print(f"\n❌ Orchestration failed: {e}")
            raise
    
    def _print_summary(self):
        """Print orchestration summary"""
        print("Workflow Execution Summary:")
        print(f"  1. Market Analysis:      ✅ Complete")
        print(f"  2. Strategy Development: ✅ Complete")
        print(f"  3. Risk Validation:      ✅ Complete")
        print(f"  4. Execution Planning:   ✅ Complete")
        print(f"  5. Client Communication: ✅ Complete")
        
        print(f"\nAgent Communications:")
        print(f"  Market → Strategy:  ✅")
        print(f"  Strategy → Risk:    ✅")
        print(f"  Risk → Executor:    ✅")
        print(f"  Executor → Explainer: ✅")
        
        print(f"\nResults stored in:")
        print(f"  Market Analysis:  {self.results['market']['timestamp']}")
        print(f"  Strategy:         {self.results['strategy']['timestamp']}")
        print(f"  Risk Assessment:  {self.results['risk']['timestamp']}")
        print(f"  Execution Plan:   {self.results['execution']['timestamp']}")
        print(f"  Client Summary:   {self.results['explanation']['timestamp']}")
        
        print("\n" + "=" * 80)
        print("Demo completed successfully! Review output styling above.")
        print("=" * 80 + "\n")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Run the orchestration demo"""
    print("\n🚀 Starting APEX Agent Orchestration Live Demo\n")
    
    demo = OrchestrationDemo()
    demo.run()


if __name__ == "__main__":
    main()
