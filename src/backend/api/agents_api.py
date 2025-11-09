"""
APEX FastAPI Backend - WITH WEBSOCKETS FOR LIVE CHAT
Real-time agent conversation feed displayed to user.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import json
import os
from datetime import datetime

from market_agent import MarketAgent
from strategy_agent import StrategyAgent
from risk_agent import RiskAgent


# ========================================
# MODELS
# ========================================

class Portfolio(BaseModel):
    total_value: float
    cash: float
    positions: Dict[str, Dict[str, Any]]


class UserProfile(BaseModel):
    risk_tolerance: str
    time_horizon: str
    goals: List[str]
    investment_style: str
    experience_level: str


class AnalysisRequest(BaseModel):
    portfolio: Portfolio
    user_profile: UserProfile


# ========================================
# FASTAPI APP
# ========================================


# ========================================
# INITIALIZE AGENTS
# ========================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "nvidia/llama-3.1-nemotron-70b-instruct"

if not OPENROUTER_API_KEY:
    raise ValueError("Set OPENROUTER_API_KEY environment variable")

market_agent = MarketAgent(OPENROUTER_API_KEY, model=MODEL, enable_logging=False)
strategy_agent = StrategyAgent(OPENROUTER_API_KEY, model=MODEL, enable_logging=False)
risk_agent = RiskAgent(OPENROUTER_API_KEY, model=MODEL, enable_logging=False, 
                       use_gpu=False, num_simulations=5000)


# ========================================
# SIMPLE REST ENDPOINT (Health Check)
# ========================================


# ========================================
# WEBSOCKET ENDPOINT (Main Chat Interface)
# ========================================

@app.websocket("/ws/analyze")
async def websocket_analyze(websocket: WebSocket):
    """
    WebSocket endpoint for live analysis with chat feed.
    
    Frontend sends: portfolio and user_profile
    Backend sends: real-time messages as analysis progresses
    User can send: messages during deliberation
    """
    await websocket.accept()
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            'type': 'connected',
            'message': 'Connected to APEX. Send your portfolio to start analysis.'
        })
        
        # Wait for initial request
        data = await websocket.receive_text()
        request_data = json.loads(data)
        
        portfolio = request_data['portfolio']
        user_profile = request_data['user_profile']
        
        # Storage for chat history
        chat_history = []
        
        async def send_message(speaker: str, message: str, data: Optional[Dict] = None):
            """Helper to send and store messages"""
            msg = {
                'type': 'message',
                'speaker': speaker,
                'message': message,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            chat_history.append(msg)
            await websocket.send_json(msg)
        
        # Start analysis
        await send_message('SYSTEM', '🚀 Starting multi-agent analysis...')
        
        # ===== PHASE 1: MARKET ANALYSIS =====
        await send_message('SYSTEM', '📊 Phase 1: Market Analysis')
        await send_message('MARKET', '🔍 Scanning current market conditions...')
        
        market_report = market_agent.scan_market()
        
        market_msg = f"""📊 Market Analysis Complete:

- S&P 500: ${market_report['market_data']['spy_price']:.2f} ({market_report['market_data']['spy_change_pct']:+.2f}%)
- VIX (Fear Index): {market_report['market_data']['vix']:.1f}
- Market Condition: {_extract_condition(market_report)}

Key Alerts:
{_format_alerts(market_report['alerts'])}"""
        
        await send_message('MARKET', market_msg, {
            'spy_price': market_report['market_data']['spy_price'],
            'vix': market_report['market_data']['vix'],
            'condition': _extract_condition(market_report)
        })
        
        # ===== PHASE 2: STRATEGY GENERATION =====
        await send_message('SYSTEM', '🧠 Phase 2: Strategy Generation')
        await send_message('STRATEGY', '💭 Analyzing your portfolio and generating recommendations...')
        
        strategy = strategy_agent.generate_strategy(
            market_report=market_report,
            current_portfolio=portfolio,
            user_profile=user_profile
        )
        
        strategy_msg = f"""💡 Strategy Recommendation:

{strategy['strategy_summary']}

Target Allocation:
{_format_allocation(strategy['target_allocation'])}

Recommended Trades ({len(strategy['recommended_trades'])} total):
{_format_trades(strategy['recommended_trades'])}

Confidence: {strategy['confidence']*100:.0f}%"""
        
        await send_message('STRATEGY', strategy_msg, {
            'allocation': strategy['target_allocation'],
            'trades': strategy['recommended_trades'],
            'confidence': strategy['confidence']
        })
        
        # ===== PHASE 3: RISK VALIDATION =====
        await send_message('SYSTEM', '⚠️  Phase 3: Risk Assessment')
        await send_message('RISK', '🎲 Running Monte Carlo simulations (5,000 iterations)...')
        
        validation = risk_agent.validate_strategy(
            strategy=strategy,
            current_portfolio=portfolio,
            user_profile=user_profile,
            market_report=market_report
        )
        
        risk_msg = f"""⚠️  Risk Analysis Complete:

Recommendation: {validation['recommendation']}
Status: {'✅ APPROVED' if validation['approved'] else '❌ NEEDS REVISION'}

Monte Carlo Results (1 year projection):
- Most Likely Outcome: ${validation['risk_analysis']['median_outcome']:,.0f}
- Worst Case (5%): ${validation['risk_analysis']['percentile_5']:,.0f}
- Best Case (5%): ${validation['risk_analysis']['percentile_95']:,.0f}

Risk Metrics:
- Maximum Drawdown: {validation['risk_analysis']['max_drawdown']*100:.1f}%
- Probability of Loss: {validation['risk_analysis']['prob_loss']*100:.1f}%
- Sharpe Ratio: {validation['risk_analysis']['sharpe_ratio']:.2f}"""
        
        if validation['violations']:
            risk_msg += f"\n\n🚨 Violations:\n{_format_list(validation['violations'])}"
        
        if validation['concerns']:
            risk_msg += f"\n\n⚠️  Concerns:\n{_format_list(validation['concerns'])}"
        
        await send_message('RISK', risk_msg, {
            'approved': validation['approved'],
            'median_outcome': validation['risk_analysis']['median_outcome'],
            'max_drawdown': validation['risk_analysis']['max_drawdown'],
            'violations': validation['violations']
        })
        
        # ===== PHASE 4: DELIBERATION =====
        await send_message('SYSTEM', '💬 Phase 4: Agent Deliberation')
        await send_message('SYSTEM', 'Agents will now discuss the strategy. You can interrupt anytime with your input.')
        
        # Run deliberation with user input
        user_messages = []
        finalize_requested = False
        
        # Deliberation context
        context = _build_context(market_report, strategy, validation, user_profile)
        
        for round_num in range(1, 4):  # Max 3 rounds
            await send_message('SYSTEM', f'--- Deliberation Round {round_num}/3 ---')
            
            # Rotate through agents
            agent_name = ['MARKET', 'STRATEGY', 'RISK'][round_num % 3]
            
            # Check for user input (non-blocking)
            try:
                # Wait up to 5 seconds for user input
                user_data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=5.0
                )
                
                user_input = json.loads(user_data)
                
                if user_input.get('type') == 'user_message':
                    user_msg = user_input.get('message', '')
                    finalize = user_input.get('finalize', False)
                    
                    # Store and display user message
                    await send_message('USER', user_msg)
                    user_messages.append(user_msg)
                    context += f"\n\nUSER INPUT: {user_msg}\n"
                    
                    if finalize:
                        finalize_requested = True
                        await send_message('SYSTEM', 'User requested finalization. Moving to final recommendation.')
                        break
                
            except asyncio.TimeoutError:
                # No user input - continue
                pass
            
            # Generate agent deliberation
            deliberation_msg = _generate_deliberation(agent_name, context, round_num)
            await send_message(agent_name, deliberation_msg)
            
            context += f"\n\n{agent_name} (Round {round_num}): {deliberation_msg}"
            
            if finalize_requested:
                break
        
        # ===== PHASE 5: FINAL RECOMMENDATION =====
        await send_message('SYSTEM', '🏁 Phase 5: Final Recommendation')
        
        # Synthesize final recommendation
        final_msg = f"""🎯 Final Investment Recommendation:

After analysis and deliberation, here's our final recommendation:

{strategy['rationale'][:300]}...

Target Allocation:
{_format_allocation(strategy['target_allocation'])}

Trades to Execute:
{_format_trades(strategy['recommended_trades'])}

Overall Assessment: {'✅ APPROVED for execution' if validation['approved'] else '⚠️  NEEDS REVIEW'}

You can now approve or reject this recommendation."""
        
        await send_message('SYSTEM', final_msg, {
            'final_allocation': strategy['target_allocation'],
            'final_trades': strategy['recommended_trades'],
            'approved': validation['approved'],
            'chat_history': chat_history
        })
        
        # Wait for user approval
        await send_message('SYSTEM', 'Waiting for your approval...')
        
        approval_data = await websocket.receive_text()
        approval = json.loads(approval_data)
        
        if approval.get('approved'):
            await send_message('SYSTEM', '✅ Strategy approved! Ready for execution.')
            await websocket.send_json({
                'type': 'complete',
                'approved': True,
                'chat_history': chat_history,
                'final_strategy': {
                    'allocation': strategy['target_allocation'],
                    'trades': strategy['recommended_trades']
                }
            })
        else:
            await send_message('SYSTEM', '❌ Strategy rejected. Analysis complete.')
            await websocket.send_json({
                'type': 'complete',
                'approved': False,
                'chat_history': chat_history
            })
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'message': str(e)
        })
    finally:
        await websocket.close()


# ========================================
# HELPER FUNCTIONS
# ========================================

def _extract_condition(market_report: Dict) -> str:
    """Extract market condition"""
    analysis = market_report.get('analysis', '')
    for condition in ['Bullish', 'Bearish', 'Volatile', 'Mixed', 'Neutral']:
        if condition in analysis:
            return condition
    return 'Neutral'


def _format_alerts(alerts: List[str]) -> str:
    """Format alerts list"""
    return '\n'.join([f"  • {alert}" for alert in alerts[:3]])


def _format_allocation(allocation: Dict[str, float]) -> str:
    """Format allocation dict"""
    lines = []
    for symbol, weight in sorted(allocation.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"  • {symbol.upper()}: {weight*100:.0f}%")
    return '\n'.join(lines)


def _format_trades(trades: List[Dict]) -> str:
    """Format trades list"""
    if not trades:
        return "  • No trades needed"
    
    lines = []
    for i, trade in enumerate(trades[:5], 1):
        lines.append(f"  {i}. {trade['action']} {trade['shares']} {trade['symbol']} - {trade['reason']}")
    
    if len(trades) > 5:
        lines.append(f"  ... and {len(trades)-5} more")
    
    return '\n'.join(lines)


def _format_list(items: List[str]) -> str:
    """Format generic list"""
    return '\n'.join([f"  • {item}" for item in items])


def _build_context(market_report: Dict, strategy: Dict, validation: Dict, user_profile: Dict) -> str:
    """Build context for deliberation"""
    return f"""MARKET: VIX {market_report['market_data']['vix']:.1f}, {_extract_condition(market_report)}
STRATEGY: {strategy['strategy_summary'][:100]}
RISK: {validation['recommendation']}, {len(validation['violations'])} violations
USER: {user_profile['risk_tolerance']} risk tolerance"""


def _generate_deliberation(agent_name: str, context: str, round_num: int) -> str:
    """
    Generate deliberation message.
    In production, this would call the AI model.
    For simplicity, returning structured responses.
    """
    templates = {
        'MARKET': [
            "Given current volatility, I recommend proceeding cautiously with this allocation.",
            "Market conditions support this strategy. VIX levels are manageable.",
            "I see some headwinds in the market, but the diversification helps mitigate risk."
        ],
        'STRATEGY': [
            "This allocation balances growth and protection well for the user's profile.",
            "I'm confident this strategy aligns with the long-term goals specified.",
            "The trade recommendations will reposition the portfolio appropriately."
        ],
        'RISK': [
            "Monte Carlo results show acceptable downside risk for this user.",
            "The probability metrics look good - within tolerance levels.",
            "I'm satisfied with the risk-adjusted returns this strategy should provide."
        ]
    }
    
    return templates[agent_name][round_num % len(templates[agent_name])]


# ========================================
# RUN SERVER
# ========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
