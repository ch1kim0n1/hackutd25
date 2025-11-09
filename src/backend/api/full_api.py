from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.core.agent_network import AgentNetwork
from backend.services.db import get_db
from backend.api.auth import login_user, get_current_user
from backend.api.strategy import run_strategy
from backend.api.portfolio import get_portfolio
from backend.api.trades import place_order, get_positions
from backend.api.market import get_market_data
from backend.services.alpaca import initialize_broker
import asyncio

app = FastAPI(title="APEX Backend API")

#Work
# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # replace with frontend URL in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent network
agent_network = AgentNetwork()

@app.on_event("startup")
async def startup_event():
    await agent_network.initialize()
    # Run listener in background
    asyncio.create_task(agent_network.listen())

# ---------------------
# Auth endpoints
# ---------------------
@app.post("/login")
async def login(username: str, password: str):
    return await login_user(username, password)

@app.get("/me")
async def me(user=Depends(get_current_user)):
    return user

# ---------------------
# Strategy endpoints
# ---------------------
@app.post("/strategy/run")
async def strategy_run(strategy_id: str, user=Depends(get_current_user)):
    """
    Submits a strategy to be executed by agents.
    """
    result = await run_strategy(agent_network, strategy_id, user.id)
    return result

# ---------------------
# Portfolio endpoints
# ---------------------
@app.get("/portfolio")
async def portfolio(user=Depends(get_current_user), db=Depends(get_db)):
    return await get_portfolio(user.id, db)

# ---------------------
# Trade endpoints
# ---------------------
@app.post("/trade/buy")
async def buy(symbol: str, qty: int, user=Depends(get_current_user)):
    return await place_order(agent_network, user.id, symbol, qty, "buy")

@app.post("/trade/sell")
async def sell(symbol: str, qty: int, user=Depends(get_current_user)):
    return await place_order(agent_network, user.id, symbol, qty, "sell")

@app.get("/trade/positions")
async def positions(user=Depends(get_current_user)):
    return await get_positions(agent_network, user.id)

# ---------------------
# Market endpoints
# ---------------------
@app.get("/market/{symbol}")
async def market(symbol: str):
    return await get_market_data(symbol)


@app.on_event("startup")
async def startup_event():
    await agent_network.initialize()
    asyncio.create_task(agent_network.listen())
    await initialize_broker()

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

"""
Stock Price Analysis Feature
Analyzes historical stock price movements using news context from that time period.
Helps users understand WHY a stock moved the way it did.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import yfinance as yf
from openai import OpenAI
import os


# ========================================
# MODELS
# ========================================

class StockAnalysisRequest(BaseModel):
    symbol: str
    start_date: str  # Format: "2024-01-01"
    end_date: str    # Format: "2024-12-31"


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
# STOCK ANALYZER CLASS
# ========================================

class StockAnalyzer:
    """
    Analyzes historical stock price movements with news context.
    """
    
    def __init__(self, openrouter_api_key: str, model: str = "nvidia/llama-3.1-nemotron-70b-instruct"):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key
        )
        self.model = model
    
    def get_stock_data(self, symbol: str, start_date: str, end_date: str) -> Dict:
        """
        Fetch historical stock data from Yahoo Finance.
        
        Returns:
            {
                'start_price': 150.25,
                'end_price': 175.50,
                'high': 180.00,
                'low': 145.00,
                'volume_avg': 50000000,
                'price_change_pct': 0.168
            }
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                raise ValueError(f"No data found for {symbol} in date range")
            
            start_price = hist['Close'].iloc[0]
            end_price = hist['Close'].iloc[-1]
            high_price = hist['High'].max()
            low_price = hist['Low'].min()
            avg_volume = hist['Volume'].mean()
            
            price_change_pct = (end_price - start_price) / start_price
            price_change_abs = end_price - start_price
            
            return {
                'start_price': float(start_price),
                'end_price': float(end_price),
                'high': float(high_price),
                'low': float(low_price),
                'volume_avg': float(avg_volume),
                'price_change_pct': float(price_change_pct),
                'price_change_abs': float(price_change_abs),
                'data_points': len(hist)
            }
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error fetching stock data: {str(e)}")
    
    def get_company_info(self, symbol: str) -> Dict:
        """Get basic company information"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'description': info.get('longBusinessSummary', '')[:300]
            }
        except:
            return {
                'name': symbol,
                'sector': 'Unknown',
                'industry': 'Unknown',
                'description': ''
            }
    
    def fetch_news(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Fetch news articles for the time period.
        
        Uses multiple strategies:
        1. Yahoo Finance built-in news
        2. Web search for company + time period
        """
        news_articles = []
        
        # Strategy 1: Yahoo Finance news (recent only)
        try:
            ticker = yf.Ticker(symbol)
            yf_news = ticker.news[:10] if hasattr(ticker, 'news') else []
            
            for article in yf_news:
                news_articles.append({
                    'title': article.get('title', ''),
                    'publisher': article.get('publisher', 'Yahoo Finance'),
                    'link': article.get('link', ''),
                    'publish_time': article.get('providerPublishTime', 0),
                    'source': 'yahoo_finance'
                })
        except:
            pass
        
        # Strategy 2: Web search using company name + date
        # For hackathon, we'll simulate with general search
        company_info = self.get_company_info(symbol)
        company_name = company_info['name']
        
        # Build search query
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Search for major events
        search_queries = [
            f"{company_name} {symbol} stock news {start_dt.year}",
            f"{company_name} earnings {start_dt.year}",
            f"{company_name} announcement {start_dt.year}"
        ]
        
        # Note: In production, you'd use web_search tool here
        # For now, return what we have from Yahoo Finance
        
        return news_articles[:10]  # Limit to 10 articles
    
    def analyze_with_ai(
        self,
        symbol: str,
        stock_data: Dict,
        company_info: Dict,
        news_articles: List[Dict],
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Use AI to analyze why the stock moved the way it did.
        
        Returns:
            {
                'analysis': '...',
                'key_factors': [...],
                'educational_insights': [...]
            }
        """
        
        # Build context from news
        news_context = self._build_news_context(news_articles)
        
        # Build the prompt
        prompt = f"""You are a financial educator analyzing a historical stock price movement.

**COMPANY INFORMATION:**
Name: {company_info['name']} ({symbol})
Sector: {company_info['sector']}
Industry: {company_info['industry']}

**PRICE MOVEMENT:**
Time Period: {start_date} to {end_date}
Starting Price: ${stock_data['start_price']:.2f}
Ending Price: ${stock_data['end_price']:.2f}
Price Change: {stock_data['price_change_pct']*100:+.2f}% (${stock_data['price_change_abs']:+.2f})
High During Period: ${stock_data['high']:.2f}
Low During Period: ${stock_data['low']:.2f}

**NEWS CONTEXT FROM THAT TIME PERIOD:**
{news_context if news_context else 'Limited news data available for this period.'}

**YOUR TASK:**
Analyze and explain WHY this stock moved the way it did during this period. Your response should educate a beginner investor.

Provide:
1. A clear, educational explanation (2-3 paragraphs) of what likely caused this price movement
2. Identify 3-5 key factors that influenced the stock
3. Provide 2-3 educational insights that help the user learn about stock market dynamics

Use simple language. Reference specific news/events if available. If insufficient data, explain general factors that could cause such movements.

Respond in JSON format:
{{
    "analysis": "2-3 paragraph explanation here",
    "key_factors": [
        "Factor 1: Description",
        "Factor 2: Description",
        "Factor 3: Description"
    ],
    "educational_insights": [
        "Insight 1: What this teaches about markets",
        "Insight 2: What this teaches about investing"
    ]
}}

IMPORTANT: Output ONLY valid JSON, no markdown formatting."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial educator who explains stock movements in simple, educational terms. Always output valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.7,
                extra_headers={
                    "HTTP-Referer": "https://apex-financial.com",
                    "X-Title": "APEX Stock Analysis"
                }
            )
            
            # Parse JSON response
            import json
            response_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(response_text)
            
            return {
                'analysis': result.get('analysis', 'Analysis unavailable'),
                'key_factors': result.get('key_factors', []),
                'educational_insights': result.get('educational_insights', [])
            }
            
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            return {
                'analysis': response_text if 'response_text' in locals() else 'Unable to generate analysis',
                'key_factors': ['Analysis error - please try again'],
                'educational_insights': []
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI analysis error: {str(e)}")
    
    def _build_news_context(self, news_articles: List[Dict]) -> str:
        """Build news context string from articles"""
        if not news_articles:
            return ""
        
        context_parts = []
        for i, article in enumerate(news_articles[:10], 1):
            title = article.get('title', 'No title')
            publisher = article.get('publisher', 'Unknown')
            context_parts.append(f"{i}. {title} (Source: {publisher})")
        
        return "\n".join(context_parts)
    
    def run_full_analysis(self, symbol: str, start_date: str, end_date: str) -> StockAnalysisResponse:
        """
        Run complete analysis pipeline.
        """
        # Step 1: Get stock data
        stock_data = self.get_stock_data(symbol, start_date, end_date)
        
        # Step 2: Get company info
        company_info = self.get_company_info(symbol)
        
        # Step 3: Fetch news
        news_articles = self.fetch_news(symbol, start_date, end_date)
        
        # Step 4: AI analysis
        ai_result = self.analyze_with_ai(
            symbol=symbol,
            stock_data=stock_data,
            company_info=company_info,
            news_articles=news_articles,
            start_date=start_date,
            end_date=end_date
        )
        
        # Step 5: Build response
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


# ========================================
# FASTAPI ENDPOINTS
# ========================================

# Initialize analyzer (reuse across requests)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
stock_analyzer = StockAnalyzer(OPENROUTER_API_KEY)


# Add to existing FastAPI app
# app = FastAPI()  # Your existing app

@app.post("/api/stock/analyze", response_model=StockAnalysisResponse)
def analyze_stock(request: StockAnalysisRequest):
    """
    Analyze a stock's historical price movement with news context.
    
    Example:
```json
    {
        "symbol": "AAPL",
        "start_date": "2024-01-01",
        "end_date": "2024-03-31"
    }
```
    """
    try:
        result = stock_analyzer.run_full_analysis(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date
        )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{symbol}/info")
def get_stock_info(symbol: str):
    """
    Get basic company information for a stock.
    
    Example: GET /api/stock/AAPL/info
    """
    try:
        info = stock_analyzer.get_company_info(symbol)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{symbol}/current")
def get_current_price(symbol: str):
    """
    Get current stock price and basic stats.
    
    Example: GET /api/stock/AAPL/current
    """
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
# EXAMPLE USAGE
# ========================================

if __name__ == "__main__":
    # Test the analyzer
    analyzer = StockAnalyzer(
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY")
    )
    
    # Analyze AAPL's movement in Q1 2024
    result = analyzer.run_full_analysis(
        symbol="AAPL",
        start_date="2024-01-01",
        end_date="2024-03-31"
    )
    
    print(f"\n{'='*60}")
    print(f"STOCK ANALYSIS: {result.symbol}")
    print(f"{'='*60}")
    print(f"\nPeriod: {result.start_date} to {result.end_date}")
    print(f"Price Movement: ${result.price_start:.2f} → ${result.price_end:.2f}")
    print(f"Change: {result.price_change_pct*100:+.2f}% (${result.price_change_abs:+.2f})")
    
    print(f"\n📰 NEWS ARTICLES FOUND: {len(result.news_articles)}")
    for article in result.news_articles[:3]:
        print(f"  • {article['title']}")
    
    print(f"\n📊 ANALYSIS:")
    print(result.analysis)
    
    print(f"\n🔑 KEY FACTORS:")
    for factor in result.key_factors:
        print(f"  • {factor}")
    
    print(f"\n💡 EDUCATIONAL INSIGHTS:")
    for insight in result.educational_insights:
        print(f"  • {insight}")
  

