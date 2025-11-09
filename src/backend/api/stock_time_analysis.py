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
