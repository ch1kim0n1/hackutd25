    # apex_backend.py
"""
APEX Unified Backend
Combines stock analysis, agent network, auth, strategy, trades, portfolio, market endpoints
with WebSocket live chat and AI-powered stock analysis.
"""

import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

import yfinance as yf
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import jwt
import logging

# ========================================
# LOGGER
# ========================================
logger = logging.getLogger(__name__)

# ========================================
# FASTAPI APP
# ========================================
app = FastAPI(title="APEX Unified Backend API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================
# AUTH SETUP
# ========================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecret")
ALGORITHM = "HS256"
ACCESS_EXPIRE_MINUTES = 60
token_blacklist: set = set()

# Fake in-memory user db
users_db = {
    "testuser": {"id": "1", "username": "testuser", "hashed_password": "testpass", "is_active": True}
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if token in token_blacklist:
        raise HTTPException(status_code=401, detail="Token revoked")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = next((u for u in users_db.values() if u["id"] == user_id), None)
        if not user or not user["is_active"]:
            raise HTTPException(status_code=403, detail="Inactive user")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/login")
async def login(username: str, password: str):
    user = users_db.get(username)
    if not user or password != user["hashed_password"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": user["id"]})
    return {"access_token": access_token, "token_type": "bearer", "expires_in": ACCESS_EXPIRE_MINUTES*60}

@app.get("/me")
async def me(user=Depends(get_current_user)):
    return user

@app.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    token_blacklist.add(token)
    return {"message": "Logged out"}

# ========================================
# STOCK ANALYSIS
# ========================================

class StockAnalysisRequest(BaseModel):
    symbol: str
    start_date: str
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

class StockAnalyzer:
    def __init__(self):
        self.client = None  # Could add AI client here

    def get_stock_data(self, symbol: str, start_date: str, end_date: str) -> Dict:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date)
        if hist.empty:
            raise HTTPException(status_code=400, detail="No data for this range")
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
            'price_change_abs': float(price_change_abs)
        }

    def fetch_news(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        ticker = yf.Ticker(symbol)
        news_articles = getattr(ticker, "news", [])[:10] if hasattr(ticker, "news") else []
        formatted = []
        for article in news_articles:
            formatted.append({
                'title': article.get('title',''),
                'publisher': article.get('publisher','Yahoo Finance'),
                'link': article.get('link','')
            })
        return formatted

    def run_full_analysis(self, symbol: str, start_date: str, end_date: str) -> StockAnalysisResponse:
        data = self.get_stock_data(symbol, start_date, end_date)
        news = self.fetch_news(symbol, start_date, end_date)
        # Simple heuristic analysis
        pct = data['price_change_pct']
        direction = "up" if pct>0 else "down" if pct<0 else "flat"
        analysis_text = f"Stock {symbol} moved {direction} by {pct*100:+.2f}% between {start_date} and {end_date}."
        key_factors = ["Price movement"] + (["News in period"] if news else [])
        insights = ["Stocks move for various reasons including news, earnings, and sentiment."]
        return StockAnalysisResponse(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            price_start=data['start_price'],
            price_end=data['end_price'],
            price_change_pct=data['price_change_pct'],
            price_change_abs=data['price_change_abs'],
            news_articles=news,
            analysis=analysis_text,
            key_factors=key_factors,
            educational_insights=insights
        )

stock_analyzer = StockAnalyzer()

@app.post("/api/stock/analyze", response_model=StockAnalysisResponse)
async def analyze_stock(request: StockAnalysisRequest):
    return stock_analyzer.run_full_analysis(request.symbol, request.start_date, request.end_date)

@app.get("/api/stock/{symbol}/current")
async def get_current_price(symbol: str):
    ticker = yf.Ticker(symbol)
    info = ticker.info
    return {
        'symbol': symbol.upper(),
        'current_price': info.get('currentPrice', info.get('regularMarketPrice',0)),
        'previous_close': info.get('previousClose',0),
        'change_pct': info.get('regularMarketChangePercent',0),
        'day_high': info.get('dayHigh',0),
        'day_low': info.get('dayLow',0),
        'volume': info.get('volume',0),
        'market_cap': info.get('marketCap',0)
    }

# ========================================
# MOCK AGENT NETWORK
# ========================================
class AgentNetwork:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def initialize(self):
        print("Agent network initialized")

    async def listen(self):
        while True:
            await asyncio.sleep(1)  # placeholder for message handling

    async def publish(self, topic: str, message: dict):
        print(f"Published to {topic}: {message}")

agent_network = AgentNetwork()

# ========================================
# STRATEGY
# ========================================
@app.post("/strategy/run")
async def strategy_run(strategy_id: str, user=Depends(get_current_user)):
    await agent_network.publish("strategy_execute", {"strategy_id": strategy_id, "user_id": user["id"]})
    return {"status": "submitted", "strategy_id": strategy_id}

# ========================================
# PORTFOLIO
# ========================================
@app.get("/portfolio")
async def get_portfolio(user=Depends(get_current_user)):
    # Mock portfolio
    return {"user_id": user["id"], "portfolio": [{"symbol":"AAPL","shares":10},{"symbol":"TSLA","shares":5}]}

# ========================================
# TRADES
# ========================================
@app.post("/trade/buy")
async def buy(symbol: str, qty: int, user=Depends(get_current_user)):
    await agent_network.publish("trade_order", {"user_id": user["id"], "symbol": symbol, "qty": qty, "side": "buy"})
    return {"status":"executed","symbol":symbol,"qty":qty,"side":"buy"}

@app.post("/trade/sell")
async def sell(symbol: str, qty: int, user=Depends(get_current_user)):
    await agent_network.publish("trade_order", {"user_id": user["id"], "symbol": symbol, "qty": qty, "side": "sell"})
    return {"status":"executed","symbol":symbol,"qty":qty,"side":"sell"}

@app.get("/trade/positions")
async def positions(user=Depends(get_current_user)):
    return [{"symbol":"AAPL","shares":10},{"symbol":"TSLA","shares":5}]

# ========================================
# MARKET
# ========================================
@app.get("/market/{symbol}")
async def market(symbol: str):
    return {
        "symbol": symbol,
        "open":100.0,"high":105.0,"low":95.0,"close":102.0,"volume":1000000
    }

# ========================================
# STARTUP
# ========================================
@app.on_event("startup")
async def startup_event():
    await agent_network.initialize()
    asyncio.create_task(agent_network.listen())

# ========================================
# RUN SERVER
# ========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apex_backend:app", host="0.0.0.0", port=8000, reload=True)
