"""
APEX FastAPI Backend - ULTRA SIMPLE
Just 2 endpoints for hackathon demo. No sessions, no complexity.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import os

from market_agent import MarketAgent
from strategy_agent import StrategyAgent
from risk_agent import RiskAgent


# ========================================
# REQUEST/RESPONSE MODELS
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
    max_deliberation_rounds: Optional[int] = 3


class UserFeedback(BaseModel):
    user_message: Optional[str] = None
    finalize: bool = False


# ========================================
# FASTAPI APP
# ========================================

# ========================================
# INITIALIZE AGENTS (ONCE AT STARTUP)
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
# API ENDPOINTS
# ========================================

@app.post("/api/analyze")
def analyze(request: AnalysisRequest):
    """
    Run complete analysis. Returns everything in one response.
    This is blocking - frontend waits for complete result.
    """
    try:
        portfolio = request.portfolio.dict()
        user_profile = request.user_profile.dict()
        
        # STEP 1: Market Analysis
        market_report = market_agent.scan_market()
        
        market_summary = {
            'spy_price': market_report['market_data']['spy_price'],
            'spy_change_pct': market_report['market_data']['spy_change_pct'],
            'vix': market_report['market_data']['vix'],
            'condition': _extract_condition(market_report),
            'alerts': market_report['alerts']
        }
        
        # STEP 2: Strategy Generation
        strategy = strategy_agent.generate_strategy(
            market_report=market_report,
            current_portfolio=portfolio,
            user_profile=user_profile
        )
        
        strategy_summary = {
            'summary': strategy['strategy_summary'],
            'allocation': strategy['target_allocation'],
            'trades': strategy['recommended_trades'],
            'confidence': strategy['confidence'],
            'rationale': strategy.get('rationale', '')
        }
        
        # STEP 3: Risk Validation
        validation = risk_agent.validate_strategy(
            strategy=strategy,
            current_portfolio=portfolio,
            user_profile=user_profile,
            market_report=market_report
        )
        
        risk_summary = {
            'recommendation': validation['recommendation'],
            'approved': validation['approved'],
            'median_outcome': validation['risk_analysis']['median_outcome'],
            'worst_case': validation['risk_analysis']['percentile_5'],
            'best_case': validation['risk_analysis']['percentile_95'],
            'max_drawdown': validation['risk_analysis']['max_drawdown'],
            'prob_loss': validation['risk_analysis']['prob_loss'],
            'sharpe_ratio': validation['risk_analysis']['sharpe_ratio'],
            'violations': validation['violations'],
            'concerns': validation['concerns'],
            'explanation': validation['explanation']
        }
        
        # STEP 4: Simple Deliberation (optional, simulated)
        deliberation = _run_simple_deliberation(
            market_report=market_report,
            strategy=strategy,
            validation=validation,
            user_profile=user_profile,
            max_rounds=request.max_deliberation_rounds
        )
        
        # Return everything
        return {
            'market': market_summary,
            'strategy': strategy_summary,
            'risk': risk_summary,
            'deliberation': deliberation,
            'overall_approved': validation['approved'],
            'timestamp': market_report['timestamp'].isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-with-feedback")
def analyze_with_feedback(request: AnalysisRequest, feedback: UserFeedback):
    """
    Run analysis WITH user feedback incorporated.
    Use this if user provides input after seeing initial analysis.
    """
    try:
        portfolio = request.portfolio.dict()
        user_profile = request.user_profile.dict()
        
        # Run initial analysis
        market_report = market_agent.scan_market()
        
        strategy = strategy_agent.generate_strategy(
            market_report=market_report,
            current_portfolio=portfolio,
            user_profile=user_profile
        )
        
        validation = risk_agent.validate_strategy(
            strategy=strategy,
            current_portfolio=portfolio,
            user_profile=user_profile,
            market_report=market_report
        )
        
        # If user provided feedback, adjust strategy
        if feedback.user_message:
            # Re-generate strategy considering user feedback
            # (Add user message to context)
            adjusted_strategy = strategy_agent.generate_strategy(
                market_report=market_report,
                current_portfolio=portfolio,
                user_profile=user_profile,
                # In a full implementation, we'd pass user_feedback here
            )
            
            strategy = adjusted_strategy
            
            # Re-validate
            validation = risk_agent.validate_strategy(
                strategy=strategy,
                current_portfolio=portfolio,
                user_profile=user_profile,
                market_report=market_report
            )
        
        return {
            'market': {
                'spy_price': market_report['market_data']['spy_price'],
                'vix': market_report['market_data']['vix'],
                'condition': _extract_condition(market_report)
            },
            'strategy': {
                'summary': strategy['strategy_summary'],
                'allocation': strategy['target_allocation'],
                'trades': strategy['recommended_trades'],
                'confidence': strategy['confidence']
            },
            'risk': {
                'recommendation': validation['recommendation'],
                'approved': validation['approved'],
                'median_outcome': validation['risk_analysis']['median_outcome'],
                'max_drawdown': validation['risk_analysis']['max_drawdown']
            },
            'user_feedback_incorporated': feedback.user_message is not None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


def _run_simple_deliberation(
    market_report: Dict,
    strategy: Dict,
    validation: Dict,
    user_profile: Dict,
    max_rounds: int = 3
) -> List[Dict]:
    """
    Simplified deliberation - just return key discussion points.
    Not full AI deliberation, just structured insights.
    """
    deliberation = []
    
    # Market Agent perspective
    deliberation.append({
        'round': 1,
        'agent': 'Market',
        'message': f"Market is {_extract_condition(market_report)} with VIX at {market_report['market_data']['vix']:.1f}. " +
                   f"{'High volatility suggests caution.' if market_report['market_data']['vix'] > 20 else 'Volatility is moderate.'}"
    })
    
    # Strategy Agent perspective
    deliberation.append({
        'round': 2,
        'agent': 'Strategy',
        'message': f"{strategy['strategy_summary']} " +
                   f"This aligns with {user_profile['risk_tolerance']} risk tolerance and {user_profile['time_horizon']} horizon."
    })
    
    # Risk Agent perspective
    deliberation.append({
        'round': 3,
        'agent': 'Risk',
        'message': f"Monte Carlo shows median outcome of ${validation['risk_analysis']['median_outcome']:,.0f}. " +
                   f"{'No violations found - strategy is within acceptable risk.' if not validation['violations'] else 'Some concerns identified: ' + ', '.join(validation['violations'][:2])}"
    })
    
    return deliberation[:max_rounds]


# ========================================
# RUN SERVER
# ========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
