import requests
from typing import List, Dict
from datetime import datetime

class NewsAggregator:
    def __init__(self):
        self.sources = {
            'yahoo_finance': 'https://finance.yahoo.com/rss/topstories',
            'marketwatch': 'https://www.marketwatch.com/rss/topstories',
            'cnbc': 'https://search.cnbc.com/rs/search/combinedcls/view.xml?partnerId=wrss01&id=10000664'
        }
    
    def get_mock_headlines(self) -> List[Dict]:
        return [
            {
                "id": "news_001",
                "title": "Fed Holds Rates Steady, Signals Potential Cut in December",
                "source": "CNBC",
                "url": "https://www.cnbc.com/fed-rates",
                "published": datetime.now().isoformat(),
                "summary": "Federal Reserve keeps interest rates unchanged but hints at possible rate cut next month.",
                "category": "Monetary Policy"
            },
            {
                "id": "news_002",
                "title": "Tech Stocks Rally on Strong Earnings from Major Players",
                "source": "MarketWatch",
                "url": "https://www.marketwatch.com/tech-rally",
                "published": datetime.now().isoformat(),
                "summary": "Technology sector surges as Apple, Microsoft report better-than-expected quarterly results.",
                "category": "Equities"
            },
            {
                "id": "news_003",
                "title": "Oil Prices Surge Amid Middle East Tensions",
                "source": "Reuters",
                "url": "https://www.reuters.com/oil-prices",
                "published": datetime.now().isoformat(),
                "summary": "Crude oil jumps 3% as geopolitical concerns rattle energy markets.",
                "category": "Commodities"
            },
            {
                "id": "news_004",
                "title": "Bitcoin Crosses $45,000 as Institutional Interest Grows",
                "source": "Bloomberg",
                "url": "https://www.bloomberg.com/crypto",
                "published": datetime.now().isoformat(),
                "summary": "Cryptocurrency markets gain momentum with major funds increasing digital asset exposure.",
                "category": "Cryptocurrency"
            },
            {
                "id": "news_005",
                "title": "Housing Market Shows Signs of Cooling as Inventory Rises",
                "source": "Wall Street Journal",
                "url": "https://www.wsj.com/housing",
                "published": datetime.now().isoformat(),
                "summary": "Home sales decline 2.3% month-over-month as more properties hit the market.",
                "category": "Real Estate"
            },
            {
                "id": "news_006",
                "title": "Dollar Weakens Against Major Currencies on Rate Cut Expectations",
                "source": "Financial Times",
                "url": "https://www.ft.com/forex",
                "published": datetime.now().isoformat(),
                "summary": "U.S. dollar index falls to three-month low amid dovish Fed signals.",
                "category": "Forex"
            },
            {
                "id": "news_007",
                "title": "AI Boom Drives Semiconductor Stocks to Record Highs",
                "source": "CNBC",
                "url": "https://www.cnbc.com/semiconductors",
                "published": datetime.now().isoformat(),
                "summary": "Chip manufacturers benefit from surging demand for AI processing power.",
                "category": "Technology"
            },
            {
                "id": "news_008",
                "title": "Consumer Confidence Hits Highest Level Since 2021",
                "source": "Yahoo Finance",
                "url": "https://finance.yahoo.com/consumer",
                "published": datetime.now().isoformat(),
                "summary": "Economic optimism rises as inflation concerns ease and job market remains strong.",
                "category": "Economic Indicators"
            },
            {
                "id": "news_009",
                "title": "Tesla Stock Jumps 8% on Record Delivery Numbers",
                "source": "MarketWatch",
                "url": "https://www.marketwatch.com/tesla",
                "published": datetime.now().isoformat(),
                "summary": "Electric vehicle maker beats analyst estimates with Q3 deliveries.",
                "category": "Equities"
            },
            {
                "id": "news_010",
                "title": "Gold Reaches All-Time High Amid Economic Uncertainty",
                "source": "Bloomberg",
                "url": "https://www.bloomberg.com/gold",
                "published": datetime.now().isoformat(),
                "summary": "Precious metal surges as investors seek safe-haven assets.",
                "category": "Commodities"
            }
        ]
    
    def get_headlines(self, limit: int = 10) -> List[Dict]:
        try:
            return self.get_mock_headlines()[:limit]
        except Exception as e:
            print(f"Error fetching news: {e}")
            return self.get_mock_headlines()[:limit]
    
    def search_news(self, query: str) -> List[Dict]:
        all_news = self.get_mock_headlines()
        query_lower = query.lower()
        return [
            news for news in all_news 
            if query_lower in news['title'].lower() or query_lower in news['summary'].lower()
        ]

news_aggregator = NewsAggregator()
