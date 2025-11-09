from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json
from ddgs import DDGS
import feedparser  # type: ignore
import requests

try:
    from duckduckgo_search import DDGS  # type: ignore
    _DDG_AVAILABLE = True
except Exception:
    _DDG_AVAILABLE = False

# RSS Feed sources for financial news
# Stock market-focused RSS feeds
FINANCE_RSS = [
    ("Yahoo Finance - Stocks", "https://finance.yahoo.com/rss/stocks"),
    ("Seeking Alpha - Market News", "https://seekingalpha.com/market_currents.xml"),
    ("CNBC - Stocks", "https://www.cnbc.com/id/15839069/device/rss/rss.html"),
    ("MarketWatch - Stocks", "http://feeds.marketwatch.com/marketwatch/stockstowatch"),
    ("Benzinga - Trading Ideas", "https://www.benzinga.com/feeds/list/trading-ideas"),
    ("TheStreet - Investing", "https://www.thestreet.com/feeds/rss/investing"),
    ("Wall Street Journal - Markets", "https://www.wsj.com/")
]

# Stock market-specific keywords
MARKET_KEYWORDS = {
    'stock_movement': ['stock price', 'shares up', 'shares down', 'stock drops', 'stock jumps', 'trading higher', 'trading lower'],
    'technical': ['resistance', 'support', 'breakout', 'breakdown', 'volume spike', 'moving average', 'price target'],
    'earnings': ['earnings per share', 'quarterly results', 'beats estimates', 'misses estimates', 'guidance', 'revenue growth'],
    'trading': ['buy rating', 'sell rating', 'hold rating', 'upgrade', 'downgrade', 'short interest', 'institutional buying'],
    'company_events': ['stock split', 'buyback', 'insider trading', 'SEC filing', '13F filing', 'dividend', 'offering']
}

def _parse_entry(src_title: str, entry: Any) -> Dict[str, Any]:
    published = None
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
    return {
        "source": src_title,
        "title": getattr(entry, "title", ""),
        "link": getattr(entry, "link", ""),
        "summary": getattr(entry, "summary", ""),
        "published": published,
    }

def fetch_rss() -> List[Dict[str, Any]]:
    articles: List[Dict[str, Any]] = []
    for src_title, url in FINANCE_RSS:
        try:
            feed = feedparser.parse(url)
            for entry in getattr(feed, "entries", []):
                articles.append(_parse_entry(src_title, entry))
        except Exception as e:
            print(f"Error fetching {src_title}: {str(e)}")
            continue
    return articles

def ddg_news_search(query: str, max_results: int = 20) -> List[Dict[str, Any]]:
    if not _DDG_AVAILABLE:
        return []
    results: List[Dict[str, Any]] = []
    try:
        # Enhance query with market focus
        market_query = f"stock market {query} finance investing"
        with DDGS() as ddgs:
            for item in ddgs.news(keywords=market_query, max_results=max_results, timelimit="7d"):
                # Skip non-financial news
                title = item.get("title", "").lower()
                body = item.get("body", "").lower()
                if not any(kw.lower() in title or kw.lower() in body 
                          for category in MARKET_KEYWORDS.values() 
                          for kw in category):
                    continue
                    
                results.append({
                    "source": item.get("source"),
                    "title": item.get("title"),
                    "link": item.get("url"),
                    "summary": item.get("body"),
                    "published": item.get("date"),
                    "category": next((cat for cat, keywords in MARKET_KEYWORDS.items() 
                                   if any(kw.lower() in title or kw.lower() in body 
                                        for kw in keywords)), "general")
                })
    except Exception as e:
        print(f"Error searching DuckDuckGo: {str(e)}")
    return results

if __name__ == "__main__":
    print("Fetching stock market news...")
    
    # Get news from RSS feeds
    articles = fetch_rss()
    
    # Get stock-specific news from DuckDuckGo
    if _DDG_AVAILABLE:
        # Get major stock movements
        stock_news = ddg_news_search("breaking stock market movers today", max_results=5)
        articles.extend(stock_news)
        
        # Get earnings and trading updates
        earnings_news = ddg_news_search("stock earnings announcements trading updates", max_results=5)
        articles.extend(earnings_news)
        
        # Get analyst ratings and price targets
        analyst_news = ddg_news_search("stock analyst ratings price targets upgrade downgrade", max_results=5)
        articles.extend(analyst_news)
    
    # Print the results
    print("\nLatest Financial News:")
    print("-" * 50)
    
    # Sort by published date
    def process_articles(articles: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        # Remove duplicates based on title or link
        seen = set()
        unique_articles = []
        for article in articles:
            key = (article['title'], article['link'])
            if key not in seen:
                seen.add(key)
                # Clean and standardize the article format
                processed_article = {
                    "id": str(len(unique_articles) + 1),  # Add unique ID for frontend
                    "title": article['title'],
                    "source": article['source'],
                    "link": article['link'],
                    "summary": article.get('summary', ''),
                    "category": article.get('category', 'general'),
                    "published": None  # Default value
                }
                
                # Process publication date
                if article.get('published'):
                    try:
                        dt = datetime.fromisoformat(article['published'].replace("Z", "+00:00"))
                        processed_article['published'] = dt.isoformat()
                    except Exception:
                        pass
                
                unique_articles.append(processed_article)
        
        # Sort by source name and limit
        unique_articles.sort(key=lambda x: x['source'])
        unique_articles = unique_articles[:limit]
        
        return unique_articles

def print_articles_console(articles: List[Dict[str, Any]]) -> None:
    """Print articles in a nicely formatted console output"""
    print("\n" + "=" * 50)
    print("📰 Latest Stock Market News")
    print("=" * 50)
    
    number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for idx, article in enumerate(articles, 1):
        num = number_emojis[idx-1] if idx <= len(number_emojis) else f"{idx}."
        
        print(f"\n{num} {article['title']}")
        print(f"   📍 Source: {article['source']}")
        print(f"   🔗 Link: {article['link']}")
        
        if article.get('published'):
            print(f"   🕒 Published: {article['published']}")
        
        if article.get('summary'):
            summary = article['summary'].replace('\n', ' ').strip()
            if len(summary) > 200:
                summary = summary[:197] + "..."
            print(f"   📝 Summary: {summary}")
        
        if article.get('category'):
            print(f"   🏷️ Category: {article['category']}")
        
        print("-" * 50)

def save_articles_json(articles: List[Dict[str, Any]], filepath: str = "stock_news.json") -> None:
    """Save articles to a JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "articles": articles
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    print("Fetching stock market news...")
    
    # Get news from RSS feeds and DuckDuckGo
    articles = fetch_rss()
    if _DDG_AVAILABLE:
        stock_news = ddg_news_search("breaking stock market movers today", max_results=5)
        earnings_news = ddg_news_search("stock earnings announcements trading updates", max_results=5)
        analyst_news = ddg_news_search("stock analyst ratings price targets upgrade downgrade", max_results=5)
        articles.extend(stock_news + earnings_news + analyst_news)
    
    # Process articles
    processed_articles = process_articles(articles, limit=10)
    
    # Print to console
    print_articles_console(processed_articles)
    
    # Save to JSON file
    save_articles_json(processed_articles)