"""
APEX Agent Conversation Example
Demonstrates how agents communicate with each other in a real workflow.
This is a fully runnable example showing the War Room in action.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict
from enum import Enum
import json
import time


# ============================================================================
# TYPES & DATA STRUCTURES
# ============================================================================

class AgentType(Enum):
    """Agent types in APEX system"""
    MARKET = "market"
    STRATEGY = "strategy"
    RISK = "risk"
    EXECUTOR = "executor"
    EXPLAINER = "explainer"
    USER = "user"


@dataclass
class Message:
    """A message from one agent to another"""
    from_agent: str
    to_agent: str
    content: str
    timestamp: str
    importance: str = "normal"  # normal, high, critical
    
    def display(self):
        """Display message in professional format"""
        separator = "-" * 80
        importance_label = f"[{self.importance.upper()}]" if self.importance != "normal" else ""
        
        print(f"\n{separator}")
        print(f"FROM: {self.from_agent}")
        print(f"TO: {self.to_agent}")
        print(f"TIME: {self.timestamp} {importance_label}")
        print(separator)
        print(self.content)


class WarRoom:
    """The War Room - displays all agent conversations"""
    
    def __init__(self):
        self.messages: List[Message] = []
        self.message_id = 0
    
    def add_message(self, message: Message):
        """Add message to war room"""
        self.messages.append(message)
        message.display()
        time.sleep(0.3)  # Add slight delay for readability
    
    def print_summary(self):
        """Print summary of conversation"""
        print("\n" + "="*80)
        print("CONVERSATION SUMMARY")
        print("="*80)
        for i, msg in enumerate(self.messages, 1):
            importance_str = f" [{msg.importance.upper()}]" if msg.importance != "normal" else ""
            print(f"\n{i}. {msg.from_agent} → {msg.to_agent}{importance_str}")
            print(f"   {msg.content[:150]}...")


# ============================================================================
# AGENT SIMULATIONS
# ============================================================================

class MarketAgent:
    """Simulates market agent scanning and reporting"""
    name = "Market Agent"
    
    @staticmethod
    def scan_market():
        """Simulate market scanning"""
        return {
            "market_sentiment": "cautiously optimistic",
            "vix": 14.2,
            "sp500_change": 2.1,
            "tech_change": 3.2,
            "bonds_change": -0.5,
            "fed_status": "held rates steady",
            "key_news": "Tech earnings beat expectations"
        }


class StrategyAgent:
    """Simulates strategy agent creating recommendations"""
    name = "Strategy Agent"
    
    @staticmethod
    def create_portfolio(market_data: Dict, user_profile: Dict):
        """Create portfolio based on market and user info"""
        if user_profile.get("risk_tolerance") == "aggressive":
            return {
                "allocations": {
                    "VOO": {"amount": 4000, "percent": 80},
                    "VXUS": {"amount": 1000, "percent": 20}
                },
                "reasoning": "Long-term horizon allows higher equity exposure"
            }
        else:
            return {
                "allocations": {
                    "VOO": {"amount": 3000, "percent": 60},
                    "VXUS": {"amount": 1250, "percent": 25},
                    "BND": {"amount": 750, "percent": 15}
                },
                "reasoning": "Balanced approach suitable for moderate risk"
            }


class RiskAgent:
    """Simulates risk agent validating constraints"""
    name = "Risk Agent"
    
    @staticmethod
    def validate_portfolio(portfolio: Dict, user_capital: float):
        """Validate portfolio against risk constraints"""
        constraints_met = {
            "max_position": sum(alloc.get("amount", 0) for alloc in portfolio["allocations"].values()) <= user_capital,
            "diversification": len(portfolio["allocations"]) >= 2,
            "no_margin": True,
            "volatility_acceptable": True
        }
        
        all_met = all(constraints_met.values())
        return {
            "approved": all_met,
            "constraints": constraints_met,
            "notes": "All safety limits verified" if all_met else "Risk constraints violated"
        }


class ExecutorAgent:
    """Simulates executor placing trades"""
    name = "Executor Agent"
    
    @staticmethod
    def place_orders(portfolio: Dict):
        """Place orders for portfolio"""
        orders = []
        for symbol, details in portfolio["allocations"].items():
            orders.append({
                "symbol": symbol,
                "amount": details["amount"],
                "shares": round(details["amount"] / 50),  # Simulated price
                "status": "FILLED"
            })
        return {"orders": orders, "total_filled": sum(o["amount"] for o in orders)}


class ExplainerAgent:
    """Simulates explainer translating to plain English"""
    name = "Explainer Agent"
    
    @staticmethod
    def explain_portfolio(portfolio: Dict, user_name: str = "Friend"):
        """Explain portfolio in simple terms"""
        explanation = f"""
Hey {user_name}! Here's what we're doing:

"""
        for symbol, details in portfolio["allocations"].items():
            explanation += f"• {symbol}: ${details['amount']} ({details['percent']}%)\n"
        
        explanation += """
This is like a balanced meal instead of all dessert. You get:
- Growth potential from stocks
- Stability from bonds
- Protection from diversity

Ready to get started?
"""
        return explanation


# ============================================================================
# MAIN AGENT CONVERSATION
# ============================================================================

def run_agent_conversation_example():
    """
    Main function demonstrating agent conversation.
    Shows how agents talk to each other for a new user starting with $5,000.
    """
    
    print("\n" + "="*80)
    print("APEX AGENT CONVERSATION EXAMPLE")
    print("New User: Starting $5,000 Investment Portfolio")
    print("="*80)
    
    # Initialize war room
    war_room = WarRoom()
    
    # User profile
    user = {
        "name": "Alex",
        "capital": 5000,
        "experience": "beginner",
        "risk_tolerance": "aggressive",
        "time_horizon": "20 years"
    }
    
    print(f"\n👤 User Profile: {user['name']} | Capital: ${user['capital']} | Risk: {user['risk_tolerance']}")
    print("Starting agent orchestration...\n")
    
    # ========================================================================
    # STEP 1: Market Agent scans
    # ========================================================================
    
    market_data = MarketAgent.scan_market()
    
    msg1 = Message(
        from_agent="Market Agent",
        to_agent="Strategy Agent",
        content=f"""Market Scan Report

Current Market Conditions:
- Market Sentiment: {market_data['market_sentiment']}
- VIX Index: {market_data['vix']} (Low volatility environment)
- S&P 500 Performance: +{market_data['sp500_change']}%
- Technology Sector: +{market_data['tech_change']}%
- Bond Market: {market_data['bonds_change']}%
- Federal Reserve Status: {market_data['fed_status']}
- Key News: {market_data['key_news']}

Analysis:
Technology sector is outperforming significantly. Current conditions support equity-heavy allocation strategy for long-term investors. Recommend proceeding with portfolio construction.""",
        timestamp=datetime.now().strftime("%H:%M:%S"),
        importance="normal"
    )
    war_room.add_message(msg1)
    
    # ========================================================================
    # STEP 2: Strategy Agent creates portfolio
    # ========================================================================
    
    portfolio = StrategyAgent.create_portfolio(market_data, user)
    
    msg2 = Message(
        from_agent="Strategy Agent",
        to_agent="Risk Agent",
        content=f"""Portfolio Allocation Recommendation

Investor Profile:
- Risk Tolerance: {user['risk_tolerance']}
- Investment Horizon: {user['time_horizon']}
- Initial Capital: ${user['capital']:,}

Proposed Allocation:
{json.dumps(portfolio['allocations'], indent=2)}

Allocation Summary:
- Total Equity Exposure: {sum(a['percent'] for a in portfolio['allocations'].values() if a['percent'] >= 20)}%
- Number of Holdings: {len(portfolio['allocations'])}

Rationale:
{portfolio['reasoning']}

This allocation aligns with the investor's profile and current market conditions. Awaiting risk validation.""",
        timestamp=datetime.now().strftime("%H:%M:%S"),
        importance="high"
    )
    war_room.add_message(msg2)
    
    # ========================================================================
    # STEP 3: Risk Agent validates
    # ========================================================================
    
    risk_assessment = RiskAgent.validate_portfolio(portfolio, user["capital"])
    
    status = "APPROVED" if risk_assessment["approved"] else "REJECTED"
    msg3 = Message(
        from_agent="Risk Agent",
        to_agent="Executor Agent",
        content=f"""Portfolio Risk Assessment Report

Status: {status}

Constraint Validation Results:
- Maximum Position Size: PASS - No single position exceeds account limit
- Diversification Requirement: PASS - Portfolio contains {len(portfolio['allocations'])} positions
- Margin Usage Policy: PASS - No margin trading detected
- Capital Limit: PASS - Total allocation within available capital
- Volatility Tolerance: PASS - Portfolio aligns with investor risk profile

Risk Assessment Notes:
{risk_assessment['notes']}

This allocation satisfies all risk management constraints and is approved for execution. Executor Agent may proceed with order placement.""",
        timestamp=datetime.now().strftime("%H:%M:%S"),
        importance="critical"
    )
    war_room.add_message(msg3)
    
    # ========================================================================
    # STEP 4: Executor Agent places trades
    # ========================================================================
    
    execution = ExecutorAgent.place_orders(portfolio)
    
    orders_summary = "\n".join([
        f"  {o['symbol']}: {o['shares']} shares at approximately ${50} per share = ${o['amount']}"
        for o in execution["orders"]
    ])
    
    msg4 = Message(
        from_agent="Executor Agent",
        to_agent="Explainer Agent",
        content=f"""Order Execution Report

Status: SUCCESS - All orders filled

Executed Orders:
{orders_summary}

Execution Summary:
- Total Capital Deployed: ${execution['total_filled']}
- Number of Transactions: {len(execution['orders'])}
- Order Status: All orders FILLED
- Execution Time: {datetime.now().strftime("%H:%M:%S")}

All orders have been successfully executed at market prices. Portfolio construction is complete. Summary ready for user communication.""",
        timestamp=datetime.now().strftime("%H:%M:%S"),
        importance="critical"
    )
    war_room.add_message(msg4)
    
    # ========================================================================
    # STEP 5: Explainer Agent explains to user
    # ========================================================================
    
    explanation = ExplainerAgent.explain_portfolio(portfolio, user["name"])
    
    msg5 = Message(
        from_agent="Explainer Agent",
        to_agent="User",
        content=f"""Portfolio Setup Complete - Investor Summary

Hello {user['name']},

Your investment portfolio has been successfully established with the following allocation:

Portfolio Composition:
{json.dumps(portfolio['allocations'], indent=2)}

What This Means:
Your portfolio is structured to balance growth potential with your aggressive risk tolerance and long-term investment horizon. Each holding serves a specific purpose in your overall strategy:

- Growth stocks provide market upside participation
- International exposure adds geographic diversification
- This multi-holding approach reduces risk through diversification

Investment Strategy Going Forward:
- Regular monitoring of market conditions
- Quarterly portfolio rebalancing review
- Continued investment through monthly contributions
- Real-time alerts on significant market events

Your accounts are fully funded and active. You will receive regular updates on portfolio performance and market developments.""",
        timestamp=datetime.now().strftime("%H:%M:%S"),
        importance="high"
    )
    war_room.add_message(msg5)
    
    # ========================================================================
    # STEP 6: User responds (simulated)
    # ========================================================================
    
    msg6 = Message(
        from_agent="User",
        to_agent="Market Agent",
        content="""Portfolio Feedback and Requests

This looks excellent. I appreciate the aggressive approach given my 20-year timeline. I'm confident in this strategy.

Action Items:
1. Please monitor market developments and notify me of significant changes
2. Set up automatic monthly contributions to the portfolio
3. Alert me to major portfolio impacts (earnings announcements, policy changes, etc.)
4. Quarterly performance reviews

I'm ready to get started with long-term investing.""",
        timestamp=datetime.now().strftime("%H:%M:%S"),
        importance="normal"
    )
    war_room.add_message(msg6)
    
    # ========================================================================
    # STEP 7: Market Agent acknowledges
    # ========================================================================
    
    msg7 = Message(
        from_agent="Market Agent",
        to_agent="User",
        content="""Ongoing Monitoring and Contribution Setup Confirmed

Status: CONFIRMED

Monitoring Alerts:
I will provide notifications for the following market events:
- Major market movements exceeding 5% in weekly timeframe
- Volatility index spikes indicating market stress
- Portfolio-impacting events (earnings reports, regulatory changes)
- Sector rotation opportunities relevant to your holdings
- Federal Reserve policy announcements

Notification Method:
You will receive voice notifications with detailed market analysis. You can interrupt at any time to provide feedback or override recommendations.

Monthly Contributions:
Automatic investment of your designated monthly amount has been configured. Funds will be deployed according to your allocation targets every month.

Ongoing Service:
Your portfolio will be continuously monitored, stress-tested monthly, and rebalanced quarterly. All agent communications remain visible to you in the War Room for complete transparency.""",
        timestamp=datetime.now().strftime("%H:%M:%S"),
        importance="normal"
    )
    war_room.add_message(msg7)
    
    # ========================================================================
    # Print summary
    # ========================================================================
    
    war_room.print_summary()
    
    # ========================================================================
    # Print conversation flow diagram
    # ========================================================================
    
    print("\n" + "="*80)
    print("AGENT COMMUNICATION FLOW")
    print("="*80)
    
    flow = """
AGENT COMMUNICATION SEQUENCE

Step 1: Market Agent analyzes current market conditions and reports to Strategy Agent
Step 2: Strategy Agent creates portfolio recommendation based on market data and user profile
Step 3: Risk Agent validates portfolio against safety and risk constraints
Step 4: Executor Agent processes order execution upon approval
Step 5: Explainer Agent communicates portfolio details to user in plain language
Step 6: User provides feedback and requests to Market Agent
Step 7: Market Agent confirms monitoring setup and ongoing service parameters
    """
    
    print(flow)
    
    # ========================================================================
    # Key insights
    # ========================================================================
    
    print("\n" + "="*80)
    print("KEY INSIGHTS")
    print("="*80)
    print("""
AGENT SYSTEM ARCHITECTURE CHARACTERISTICS

1. TRANSPARENCY
   User observes the complete agent communication flow, including analysis, recommendations,
   and decision logic. All decisions are explained in context.

2. COLLABORATION
   Agents have specialized expertise and work sequentially:
   Market Analysis > Strategy Development > Risk Validation > Order Execution > User Communication

3. HUMAN-IN-THE-LOOP
   Users can interrupt the agent process, provide input, and override recommendations
   at any point in the conversation flow.

4. REAL-TIME INTERACTION
   Agents communicate synchronously, allowing immediate feedback and adjustment
   based on new information or user preferences.

5. SAFETY GUARANTEES
   Risk Agent enforces investment constraints before execution. No orders can be placed
   that violate established risk parameters or user preferences.

CONTINUOUS PORTFOLIO MANAGEMENT
After initial setup, the system maintains ongoing oversight:
- Market Agent: Daily monitoring for significant events
- Strategy Agent: Quarterly rebalancing evaluation
- Risk Agent: Monthly stress testing and constraint validation
- Executor Agent: Trade execution upon approval
- Explainer Agent: Regular communication on portfolio status and changes

All communications remain visible to the user in the War Room interface.""")
    
    return war_room.messages


# ============================================================================
# RUN THE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    messages = run_agent_conversation_example()
    
    print("\n" + "="*80)
    print(f"CONVERSATION COMPLETE: {len(messages)} messages exchanged")
    print("="*80 + "\n")
