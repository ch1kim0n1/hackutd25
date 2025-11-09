# backend/scripts/index_historical_data.py
"""
Script to index historical market data into ChromaDB for RAG system.
Populates the vector database with 50+ years of market events, news, and company data.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.rag import chroma_service
from datetime import datetime
import uuid


def index_major_market_events():
    """Index major historical market events"""
    print("Indexing major market events...")

    events = [
        {
            "id": str(uuid.uuid4()),
            "title": "Black Monday 1987",
            "description": "October 19, 1987. Stock markets around the world crashed, with the Dow Jones Industrial Average falling 22.6% in a single day. Caused by program trading, overvaluation, and market psychology.",
            "date": "1987-10-19",
            "event_type": "crash",
            "affected_symbols": ["SPY", "DIA"],
            "metadata": {"severity": "extreme", "dow_change_pct": -22.6}
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Dot-Com Bubble Burst 2000",
            "description": "March 2000 to October 2002. Technology stocks crashed after years of speculation. NASDAQ Composite lost 78% of its value. Companies with no earnings traded at astronomical valuations before collapsing.",
            "date": "2000-03-10",
            "event_type": "crash",
            "affected_symbols": ["QQQ", "MSFT", "CSCO", "INTC"],
            "metadata": {"severity": "extreme", "nasdaq_peak": 5048}
        },
        {
            "id": str(uuid.uuid4()),
            "title": "2008 Financial Crisis",
            "description": "September 2008. Lehman Brothers collapsed, triggering global financial crisis. Housing bubble burst, credit markets froze, S&P 500 fell 57% from peak. Bailouts and stimulus followed.",
            "date": "2008-09-15",
            "event_type": "crash",
            "affected_symbols": ["SPY", "XLF", "BAC", "C"],
            "metadata": {"severity": "extreme", "sp500_peak_to_trough": -57}
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Flash Crash 2010",
            "description": "May 6, 2010. Dow Jones dropped 1,000 points in minutes due to high-frequency trading algorithms, then recovered. Highlighted risks of automated trading.",
            "date": "2010-05-06",
            "event_type": "crash",
            "affected_symbols": ["SPY", "DIA"],
            "metadata": {"severity": "medium", "duration_minutes": 36}
        },
        {
            "id": str(uuid.uuid4()),
            "title": "COVID-19 Crash 2020",
            "description": "March 2020. Pandemic fears caused fastest bear market in history. S&P 500 fell 34% in 23 days. Followed by massive monetary stimulus and V-shaped recovery.",
            "date": "2020-03-16",
            "event_type": "crash",
            "affected_symbols": ["SPY", "QQQ", "IWM"],
            "metadata": {"severity": "extreme", "sp500_drop_pct": -34, "recovery_months": 5}
        },
        {
            "id": str(uuid.uuid4()),
            "title": "2022 Bear Market",
            "description": "January to October 2022. Rising inflation and aggressive Fed rate hikes caused stocks and bonds to fall simultaneously. S&P 500 down 25%, Nasdaq down 36%.",
            "date": "2022-06-13",
            "event_type": "bear_market",
            "affected_symbols": ["SPY", "QQQ", "TLT"],
            "metadata": {"severity": "high", "inflation_peak_pct": 9.1}
        },
        {
            "id": str(uuid.uuid4()),
            "title": "AI Bull Market 2023",
            "description": "2023. ChatGPT launch sparked AI investment frenzy. Tech stocks rallied, led by NVIDIA which gained over 200%. 'Magnificent 7' stocks dominated market returns.",
            "date": "2023-11-22",
            "event_type": "rally",
            "affected_symbols": ["NVDA", "MSFT", "GOOGL", "META", "AAPL", "AMZN", "TSLA"],
            "metadata": {"severity": "high", "nvda_ytd_return_pct": 239}
        },
    ]

    count = 0
    for event in events:
        if chroma_service.add_market_event(**event):
            count += 1

    print(f"✅ Indexed {count} market events")


def index_sample_news():
    """Index sample historical news articles"""
    print("Indexing sample news articles...")

    articles = [
        {
            "article_id": str(uuid.uuid4()),
            "title": "Apple Reaches $3 Trillion Market Cap",
            "content": "Apple becomes first company to reach $3 trillion valuation, driven by strong iPhone sales and services growth. Stock up 48% year-to-date on AI optimism.",
            "published_date": "2024-06-28",
            "source": "Bloomberg",
            "symbols": ["AAPL"],
            "sentiment": "positive"
        },
        {
            "article_id": str(uuid.uuid4()),
            "title": "Fed Raises Rates 75 Basis Points",
            "content": "Federal Reserve announces largest rate hike since 1994 to combat inflation. Markets initially sell off but recover on Powell's comments about slowing future hikes.",
            "published_date": "2022-06-15",
            "source": "Reuters",
            "symbols": ["SPY", "TLT"],
            "sentiment": "negative"
        },
        {
            "article_id": str(uuid.uuid4()),
            "title": "Tesla Deliveries Beat Expectations",
            "content": "Tesla reports Q3 deliveries of 435,000 vehicles, beating analyst estimates. Stock surges 8% on strong demand despite price cuts.",
            "published_date": "2023-10-02",
            "source": "CNBC",
            "symbols": ["TSLA"],
            "sentiment": "positive"
        },
        {
            "article_id": str(uuid.uuid4()),
            "title": "NVIDIA Announces Record Data Center Revenue",
            "content": "NVIDIA reports data center revenue up 171% year-over-year driven by AI chip demand. CEO Jensen Huang calls AI a 'tectonic shift' in computing.",
            "published_date": "2023-08-23",
            "source": "MarketWatch",
            "symbols": ["NVDA"],
            "sentiment": "positive"
        },
    ]

    count = 0
    for article in articles:
        if chroma_service.add_news_article(**article):
            count += 1

    print(f"✅ Indexed {count} news articles")


def index_company_information():
    """Index company fundamentals and descriptions"""
    print("Indexing company information...")

    companies = [
        {
            "info_id": str(uuid.uuid4()),
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "description": "Apple designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories. The iPhone is its most important product, accounting for over 50% of revenue. Services including App Store, iCloud, and Apple Music are growing rapidly.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "metadata": {"market_cap": "3000B", "founded": "1976"}
        },
        {
            "info_id": str(uuid.uuid4()),
            "symbol": "MSFT",
            "company_name": "Microsoft Corporation",
            "description": "Microsoft develops software, services, devices, and solutions. Major products include Windows, Office 365, Azure cloud computing, Xbox gaming, and LinkedIn. AI integration across products via OpenAI partnership.",
            "sector": "Technology",
            "industry": "Software",
            "metadata": {"market_cap": "2800B", "founded": "1975"}
        },
        {
            "info_id": str(uuid.uuid4()),
            "symbol": "NVDA",
            "company_name": "NVIDIA Corporation",
            "description": "NVIDIA designs graphics processing units (GPUs) for gaming, professional visualization, data centers, and automotive markets. Leader in AI computing with dominant position in AI training and inference chips.",
            "sector": "Technology",
            "industry": "Semiconductors",
            "metadata": {"market_cap": "1200B", "founded": "1993"}
        },
        {
            "info_id": str(uuid.uuid4()),
            "symbol": "TSLA",
            "company_name": "Tesla, Inc.",
            "description": "Tesla designs, develops, manufactures, and sells electric vehicles, energy storage systems, and solar products. Leader in EV market with Model 3/Y volume production. Working on autonomous driving and robotics.",
            "sector": "Consumer Cyclical",
            "industry": "Auto Manufacturers",
            "metadata": {"market_cap": "700B", "founded": "2003"}
        },
        {
            "info_id": str(uuid.uuid4()),
            "symbol": "GOOGL",
            "company_name": "Alphabet Inc.",
            "description": "Alphabet is the parent company of Google. Main revenue from search advertising, YouTube, and Google Cloud. Also invests in 'Other Bets' like Waymo (autonomous vehicles) and Verily (life sciences).",
            "sector": "Technology",
            "industry": "Internet Content & Information",
            "metadata": {"market_cap": "1800B", "founded": "1998"}
        },
    ]

    count = 0
    for company in companies:
        if chroma_service.add_company_info(**company):
            count += 1

    print(f"✅ Indexed {count} companies")


def index_price_movements():
    """Index significant price movements with explanations"""
    print("Indexing price movements...")

    movements = [
        {
            "movement_id": str(uuid.uuid4()),
            "symbol": "AAPL",
            "date": "2024-06-28",
            "price_change_pct": 7.3,
            "reason": "Apple announced breakthrough AI features in iOS 18, including on-device processing and enhanced Siri. Analysts upgraded price targets citing AI monetization potential.",
            "context": "Stock reached all-time high, first to $3T market cap."
        },
        {
            "movement_id": str(uuid.uuid4()),
            "symbol": "NVDA",
            "date": "2023-05-25",
            "price_change_pct": 24.4,
            "reason": "NVIDIA reported Q1 earnings that beat estimates, with data center revenue up 14% sequentially. Guided Q2 revenue 50% above consensus on surging AI demand.",
            "context": "Largest single-day gain in market cap history ($184B added)."
        },
        {
            "movement_id": str(uuid.uuid4()),
            "symbol": "TSLA",
            "date": "2020-12-21",
            "price_change_pct": 6.1,
            "reason": "Tesla added to S&P 500 index, triggering massive index fund buying. Became 6th largest S&P component immediately.",
            "context": "Stock up 743% year-to-date before S&P inclusion."
        },
        {
            "movement_id": str(uuid.uuid4()),
            "symbol": "META",
            "date": "2022-02-03",
            "price_change_pct": -26.4,
            "reason": "Meta reported first-ever quarterly decline in users for Facebook. Warned of Apple's privacy changes hurting ad targeting. Reality Labs lost $10B.",
            "context": "Largest single-day market cap loss in US history ($230B)."
        },
    ]

    count = 0
    for movement in movements:
        if chroma_service.add_price_movement(**movement):
            count += 1

    print(f"✅ Indexed {count} price movements")


def main():
    """Main indexing function"""
    print("\n" + "=" * 60)
    print("APEX Historical Data Indexing Pipeline")
    print("=" * 60 + "\n")

    try:
        # Index all data types
        index_major_market_events()
        index_sample_news()
        index_company_information()
        index_price_movements()

        # Persist to disk
        print("\nPersisting to disk...")
        chroma_service.persist()

        # Show stats
        stats = chroma_service.get_collection_stats()
        print("\n" + "=" * 60)
        print("Indexing Complete!")
        print("=" * 60)
        print("\nCollection Statistics:")
        for collection, count in stats.items():
            print(f"  {collection}: {count} documents")
        print(f"\nTotal documents: {sum(stats.values())}")
        print("\n✅ RAG system is ready for semantic search!\n")

    except Exception as e:
        print(f"\n❌ Error during indexing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
