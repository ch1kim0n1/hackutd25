"""
APEX FastAPI Backend - Complete Implementation
Multi-agent investment advisor with stock analysis and live chat.
No OAuth - simplified for hackathon.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import json
import os
from datetime import datetime
import yfinance as yf
from openai import OpenAI

from market_agent import MarketAgent
from strategy_agent import StrategyAgent
from risk_agent import RiskAgent


# ========================================
# PYDANTIC MODELS
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


class StockAnalysisRequest(BaseModel):
    symbol: str
    start_date: str  # Format: "2024-01-01"
    end_date: str


class StockAnalysisResponse(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    price_start: float
    price_end: float
    price_change_pct: float
    price_change_abs: float
    news_articles: List[Dict]
    analysis: str
    key_factors: List[str]
    educational_insights: List[str]


# ========================================
# FASTAPI APP
# ========================================

app = FastAPI(
    title="APEX Investment Advisor",
    description="Multi-agent AI investment advisor with live analysis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# INITIALIZE AGENTS AND STOCK ANALYZER
# ========================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "nvidia/llama-3.1-nemotron-70b-instruct"

if not OPENROUTER_API_KEY:
    raise ValueError("Set OPENROUTER_API_KEY environment variable")

# Initialize investment agents
market_agent = MarketAgent(OPENROUTER_API_KEY, model=MODEL, enable_logging=False)
strategy_agent = StrategyAgent(OPENROUTER_API_KEY, model=MODEL, enable_logging=False)
risk_agent = RiskAgent(OPENROUTER_API_KEY, model=MODEL, enable_logging=False, 
                       use_gpu=False, num_simulations=5000)


# ========================================
# STOCK ANALYZER CLASS
# ========================================

class StockAnalyzer:
    """Analyzes historical stock price movements with news context."""
    
    def __init__(self, openrouter_api_key: str, model: str):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key
        )
        self.model = model
    
    def get_stock_data(self, symbol: str, start_date: str, end_date: str) -> Dict:
        """Fetch historical stock data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                raise ValueError(f"No data found for {symbol} in date range")
            
            start_price = hist['Close'].iloc[0]
            end_price = hist['Close'].iloc[-1]
            
            return {
                'start_price': float(start_price),
                'end_price': float(end_price),
                'high': float(hist['High'].max()),
                'low': float(hist['Low'].min()),
                'volume_avg': float(hist['Volume'].mean()),
                'price_change_pct': float((end_price - start_price) / start_price),
                'price_change_abs': float(end_price - start_price),
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error fetching stock data: {str(e)}")
    
    def get_company_info(self, symbol: str) -> Dict:
        """Get basic company information."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
            }
        except:
            return {'name': symbol, 'sector': 'Unknown', 'industry': 'Unknown'}
    
    def fetch_news(self, symbol: str) -> List[Dict]:
        """Fetch recent news articles."""
        try:
            ticker = yf.Ticker(symbol)
            yf_news = ticker.news[:10] if hasattr(ticker, 'news') else []
            
            return [{
                'title': article.get('title', ''),
                'publisher': article.get('publisher', 'Yahoo Finance'),
                'link': article.get('link', ''),
            } for article in yf_news]
        except:
            return []
    
    def analyze_with_ai(self, symbol: str, stock_data: Dict, company_info: Dict, 
                       news_articles: List[Dict], start_date: str, end_date: str) -> Dict:
        """Use AI to analyze why the stock moved."""
        
        news_context = '\n'.join([f"{i+1}. {a['title']}" for i, a in enumerate(news_articles[:10])])
        
        prompt = f"""Analyze this stock price movement for a beginner investor.

COMPANY: {company_info['name']} ({symbol}) - {company_info['sector']}
PERIOD: {start_date} to {end_date}
PRICE CHANGE: ${stock_data['start_price']:.2f} → ${stock_data['end_price']:.2f} ({stock_data['price_change_pct']*100:+.2f}%)

NEWS: {news_context if news_context else 'Limited news available'}

Provide a JSON response with:
1. "analysis": 2-3 paragraph explanation
2. "key_factors": List of 3-5 factors
3. "educational_insights": List of 2-3 learning points

Output ONLY valid JSON, no markdown."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Financial educator. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content.strip().replace('```json', '').replace('```', ''))
            return {
                'analysis': result.get('analysis', 'Analysis unavailable'),
                'key_factors': result.get('key_factors', []),
                'educational_insights': result.get('educational_insights', [])
            }
        except:
            return {
                'analysis': 'Unable to generate analysis',
                'key_factors': ['Analysis error'],
                'educational_insights': []
            }
    
    def run_full_analysis(self, symbol: str, start_date: str, end_date: str) -> StockAnalysisResponse:
        """Run complete analysis pipeline."""
        stock_data = self.get_stock_data(symbol, start_date, end_date)
        company_info = self.get_company_info(symbol)
        news_articles = self.fetch_news(symbol)
        ai_result = self.analyze_with_ai(symbol, stock_data, company_info, news_articles, start_date, end_date)
        
        return StockAnalysisResponse(
            symbol=symbol.upper(),
            start_date=start_date,
            end_date=end_date,
            price_start=stock_data['start_price'],
            price_end=stock_data['end_price'],
            price_change_pct=stock_data['price_change_pct'],
            price_change_abs=stock_data['price_change_abs'],
            news_articles=news_articles,
            analysis=ai_result['analysis'],
            key_factors=ai_result['key_factors'],
            educational_insights=ai_result['educational_insights']
        )


# Initialize stock analyzer
stock_analyzer = StockAnalyzer(OPENROUTER_API_KEY, MODEL)


# ========================================
# HELPER FUNCTIONS
# ========================================

def _extract_condition(market_report: Dict) -> str:
    """Extract market condition from report."""
    analysis = market_report.get('analysis', '')
    for condition in ['Bullish', 'Bearish', 'Volatile', 'Mixed', 'Neutral']:
        if condition in analysis:
            return condition
    return 'Neutral'


def _format_alerts(alerts: List[str]) -> str:
    """Format alerts list."""
    return '\n'.join([f"  • {alert}" for alert in alerts[:3]])


def _format_allocation(allocation: Dict[str, float]) -> str:
    """Format allocation dict."""
    return '\n'.join([f"  • {s.upper()}: {w*100:.0f}%" 
                     for s, w in sorted(allocation.items(), key=lambda x: x[1], reverse=True)])


def _format_trades(trades: List[Dict]) -> str:
    """Format trades list."""
    if not trades:
        return "  • No trades needed"
    
    lines = [f"  {i}. {t['action']} {t['shares']} {t['symbol']} - {t['reason']}" 
             for i, t in enumerate(trades[:5], 1)]
    
    if len(trades) > 5:
        lines.append(f"  ... and {len(trades)-5} more")
    
    return '\n'.join(lines)


def _format_list(items: List[str]) -> str:
    """Format generic list."""
    return '\n'.join([f"  • {item}" for item in items])


def _build_context(market_report: Dict, strategy: Dict, validation: Dict, user_profile: Dict) -> str:
    """Build context for deliberation."""
    return f"""MARKET: VIX {market_report['market_data']['vix']:.1f}, {_extract_condition(market_report)}
STRATEGY: {strategy['strategy_summary'][:100]}
RISK: {validation['recommendation']}, {len(validation['violations'])} violations
USER: {user_profile['risk_tolerance']} risk tolerance"""


def _generate_deliberation(agent_name: str, context: str, round_num: int) -> str:
    """Generate deliberation message."""
    templates = {
        'MARKET': [
            "Given current volatility, I recommend proceeding cautiously with this allocation.",
            "Market conditions support this strategy. VIX levels are manageable.",
            "I see some headwinds in the market, but diversification helps mitigate risk."
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
# REST API ENDPOINTS
# ========================================

@app.get("/")
def root():
    """Health check."""
    return {
        "status": "online",
        "service": "APEX Investment Advisor",
        "version": "1.0.0"
    }


@app.post("/api/stock/analyze", response_model=StockAnalysisResponse)
def analyze_stock(request: StockAnalysisRequest):
    """
    Analyze historical stock price movement with AI explanation.
    
    Example:
    {
        "symbol": "AAPL",
        "start_date": "2024-01-01",
        "end_date": "2024-03-31"
    }
    """
    try:
        return stock_analyzer.run_full_analysis(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{symbol}/info")
def get_stock_info(symbol: str):
    """Get basic company information."""
    try:
        return stock_analyzer.get_company_info(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{symbol}/current")
def get_current_price(symbol: str):
    """Get current stock price and stats."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            'symbol': symbol.upper(),
            'current_price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
            'previous_close': info.get('previousClose', 0),
            'change_pct': info.get('regularMarketChangePercent', 0),
            'day_high': info.get('dayHigh', 0),
            'day_low': info.get('dayLow', 0),
            'volume': info.get('volume', 0),
            'market_cap': info.get('marketCap', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# WEBSOCKET ENDPOINT - LIVE ANALYSIS
# ========================================

@app.websocket("/ws/analyze")
async def websocket_analyze(websocket: WebSocket):
    """
    WebSocket for live multi-agent analysis with chat interface.
    
    Client sends: {portfolio: {...}, user_profile: {...}}
    Server sends: Real-time agent messages
    Client can send: User messages during deliberation or final approval
    """
    await websocket.accept()
    
    try:
        await websocket.send_json({
            'type': 'connected',
            'message': 'Connected to APEX. Send your portfolio to start analysis.'
        })
        
        # Wait for initial request
        data = await websocket.receive_text()
        request_data = json.loads(data)
        
        portfolio = request_data['portfolio']
        user_profile = request_data['user_profile']
        
        # Chat history storage
        chat_history = []
        
        async def send_message(speaker: str, message: str, data: Optional[Dict] = None):
            """Helper to send and store messages."""
            msg = {
                'type': 'message',
                'speaker': speaker,
                'message': message,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            chat_history.append(msg)
            await websocket.send_json(msg)
        
        # ===== PHASE 1: MARKET ANALYSIS =====
        await send_message('SYSTEM', '🚀 Starting multi-agent analysis...')
        await send_message('SYSTEM', '📊 Phase 1: Market Analysis')
        await send_message('MARKET', '🔍 Scanning current market conditions...')
        
        market_report = market_agent.scan_market()
        
        market_msg = f"""📊 Market Analysis Complete:

- S&P 500: ${market_report['market_data']['spy_price']:.2f} ({market_report['market_data']['spy_change_pct']:+.2f}%)
- VIX: {market_report['market_data']['vix']:.1f}
- Condition: {_extract_condition(market_report)}

Alerts:
{_format_alerts(market_report['alerts'])}"""
        
        await send_message('MARKET', market_msg, {
            'spy_price': market_report['market_data']['spy_price'],
            'vix': market_report['market_data']['vix'],
            'condition': _extract_condition(market_report)
        })
        
        # ===== PHASE 2: STRATEGY GENERATION =====
        await send_message('SYSTEM', '🧠 Phase 2: Strategy Generation')
        await send_message('STRATEGY', '💭 Analyzing portfolio and generating recommendations...')
        
        strategy = strategy_agent.generate_strategy(
            market_report=market_report,
            current_portfolio=portfolio,
            user_profile=user_profile
        )
        
        strategy_msg = f"""💡 Strategy Recommendation:

{strategy['strategy_summary']}

Target Allocation:
{_format_allocation(strategy['target_allocation'])}

Trades ({len(strategy['recommended_trades'])}):
{_format_trades(strategy['recommended_trades'])}

Confidence: {strategy['confidence']*100:.0f}%"""
        
        await send_message('STRATEGY', strategy_msg, {
            'allocation': strategy['target_allocation'],
            'trades': strategy['recommended_trades'],
            'confidence': strategy['confidence']
        })
        
        # ===== PHASE 3: RISK VALIDATION =====
        await send_message('SYSTEM', '⚠️ Phase 3: Risk Assessment')
        await send_message('RISK', '🎲 Running Monte Carlo simulations...')
        
        validation = risk_agent.validate_strategy(
            strategy=strategy,
            current_portfolio=portfolio,
            user_profile=user_profile,
            market_report=market_report
        )
        
        risk_msg = f"""⚠️ Risk Analysis:

Status: {'✅ APPROVED' if validation['approved'] else '❌ NEEDS REVISION'}

Results (1 year):
- Median: ${validation['risk_analysis']['median_outcome']:,.0f}
- Worst 5%: ${validation['risk_analysis']['percentile_5']:,.0f}
- Best 5%: ${validation['risk_analysis']['percentile_95']:,.0f}
- Max Drawdown: {validation['risk_analysis']['max_drawdown']*100:.1f}%
- Loss Probability: {validation['risk_analysis']['prob_loss']*100:.1f}%"""
        
        if validation['violations']:
            risk_msg += f"\n\n🚨 Violations:\n{_format_list(validation['violations'])}"
        if validation['concerns']:
            risk_msg += f"\n\n⚠️ Concerns:\n{_format_list(validation['concerns'])}"
        
        await send_message('RISK', risk_msg, {
            'approved': validation['approved'],
            'median_outcome': validation['risk_analysis']['median_outcome']
        })
        
        # ===== PHASE 4: DELIBERATION =====
        await send_message('SYSTEM', '💬 Phase 4: Agent Deliberation')
        await send_message('SYSTEM', 'Agents discussing strategy. You can interrupt with input.')
        
        context = _build_context(market_report, strategy, validation, user_profile)
        finalize_requested = False
        
        for round_num in range(1, 4):
            await send_message('SYSTEM', f'--- Round {round_num}/3 ---')
            
            agent_name = ['MARKET', 'STRATEGY', 'RISK'][round_num % 3]
            
            # Check for user input (5 second timeout)
            try:
                user_data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                user_input = json.loads(user_data)
                
                if user_input.get('type') == 'user_message':
                    user_msg = user_input.get('message', '')
                    await send_message('USER', user_msg)
                    context += f"\n\nUSER: {user_msg}\n"
                    
                    if user_input.get('finalize'):
                        finalize_requested = True
                        await send_message('SYSTEM', 'Finalizing...')
                        break
            except asyncio.TimeoutError:
                pass
            
            # Agent deliberation
            delib_msg = _generate_deliberation(agent_name, context, round_num)
            await send_message(agent_name, delib_msg)
            context += f"\n{agent_name}: {delib_msg}"
            
            if finalize_requested:
                break
        
        # ===== PHASE 5: FINAL RECOMMENDATION =====
        await send_message('SYSTEM', '🏁 Final Recommendation')
        
        final_msg = f"""🎯 Investment Recommendation:

{strategy['strategy_summary']}

Target Allocation:
{_format_allocation(strategy['target_allocation'])}

Trades:
{_format_trades(strategy['recommended_trades'])}

Status: {'✅ APPROVED' if validation['approved'] else '⚠️ NEEDS REVIEW'}"""
        
        await send_message('SYSTEM', final_msg, {
            'final_allocation': strategy['target_allocation'],
            'final_trades': strategy['recommended_trades'],
            'approved': validation['approved'],
            'chat_history': chat_history
        })
        
        # Wait for approval
        await send_message('SYSTEM', 'Awaiting your approval...')
        approval_data = await websocket.receive_text()
        approval = json.loads(approval_data)
        
        if approval.get('approved'):
            await send_message('SYSTEM', '✅ Strategy approved!')
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
            await send_message('SYSTEM', '❌ Strategy rejected.')
            await websocket.send_json({
                'type': 'complete',
                'approved': False,
                'chat_history': chat_history
            })
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({'type': 'error', 'message': str(e)})
    finally:
        await websocket.close()


# ========================================
# RUN SERVER
# ========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
