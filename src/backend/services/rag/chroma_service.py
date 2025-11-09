# backend/services/rag/chroma_service.py
"""
ChromaDB service for APEX RAG system.
Handles vector storage and semantic search for historical market data, news, and company information.
"""
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

class ChromaService:
    """Service for managing vector embeddings and semantic search"""

    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize ChromaDB client with sentence-transformers embedding model.

        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory

        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))

        # Initialize embedding function (sentence-transformers)
        # Using all-MiniLM-L6-v2: Fast, good quality, 384 dimensions
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Collections
        self.collections = {}
        self._init_collections()

    def _init_collections(self):
        """Initialize or load collections"""
        # Market events collection (crashes, bull markets, major events)
        self.collections["market_events"] = self.client.get_or_create_collection(
            name="market_events",
            embedding_function=self.embedding_function,
            metadata={"description": "Historical market events and their impacts"}
        )

        # News archive collection
        self.collections["news_archive"] = self.client.get_or_create_collection(
            name="news_archive",
            embedding_function=self.embedding_function,
            metadata={"description": "Historical news articles and market commentary"}
        )

        # Company information collection
        self.collections["company_info"] = self.client.get_or_create_collection(
            name="company_info",
            embedding_function=self.embedding_function,
            metadata={"description": "Company fundamentals, earnings, and key events"}
        )

        # Price movements collection (why did stock X move on date Y?)
        self.collections["price_movements"] = self.client.get_or_create_collection(
            name="price_movements",
            embedding_function=self.embedding_function,
            metadata={"description": "Significant price movements and their causes"}
        )

    def add_market_event(
        self,
        event_id: str,
        title: str,
        description: str,
        date: str,
        event_type: str,
        affected_symbols: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add a market event to the collection.

        Args:
            event_id: Unique identifier for the event
            title: Event title
            description: Detailed description
            date: Event date (ISO format)
            event_type: Type of event (crash, rally, earnings, fed_decision, etc.)
            affected_symbols: List of affected stock symbols
            metadata: Additional metadata

        Returns:
            True if successful
        """
        try:
            # Combine title and description for embedding
            document = f"{title}. {description}"

            # Prepare metadata
            meta = {
                "title": title,
                "date": date,
                "event_type": event_type,
                "affected_symbols": ",".join(affected_symbols or []),
                **(metadata or {})
            }

            self.collections["market_events"].add(
                documents=[document],
                ids=[event_id],
                metadatas=[meta]
            )
            return True
        except Exception as e:
            print(f"Error adding market event: {e}")
            return False

    def add_news_article(
        self,
        article_id: str,
        title: str,
        content: str,
        published_date: str,
        source: str,
        symbols: List[str] = None,
        sentiment: str = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add a news article to the archive.

        Args:
            article_id: Unique identifier
            title: Article title
            content: Article content/summary
            published_date: Publication date (ISO format)
            source: News source (Bloomberg, Reuters, etc.)
            symbols: Related stock symbols
            sentiment: positive, negative, neutral
            metadata: Additional metadata

        Returns:
            True if successful
        """
        try:
            # Combine title and content for embedding
            document = f"{title}. {content}"

            # Prepare metadata
            meta = {
                "title": title,
                "published_date": published_date,
                "source": source,
                "symbols": ",".join(symbols or []),
                "sentiment": sentiment or "neutral",
                **(metadata or {})
            }

            self.collections["news_archive"].add(
                documents=[document],
                ids=[article_id],
                metadatas=[meta]
            )
            return True
        except Exception as e:
            print(f"Error adding news article: {e}")
            return False

    def add_company_info(
        self,
        info_id: str,
        symbol: str,
        company_name: str,
        description: str,
        sector: str,
        industry: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add company information.

        Args:
            info_id: Unique identifier
            symbol: Stock symbol
            company_name: Company name
            description: Company description/business summary
            sector: Business sector
            industry: Industry
            metadata: Additional metadata (market cap, PE ratio, etc.)

        Returns:
            True if successful
        """
        try:
            # Combine all text fields for embedding
            document = f"{company_name} ({symbol}). {description}. Sector: {sector}. Industry: {industry}."

            # Prepare metadata
            meta = {
                "symbol": symbol,
                "company_name": company_name,
                "sector": sector,
                "industry": industry,
                **(metadata or {})
            }

            self.collections["company_info"].add(
                documents=[document],
                ids=[info_id],
                metadatas=[meta]
            )
            return True
        except Exception as e:
            print(f"Error adding company info: {e}")
            return False

    def add_price_movement(
        self,
        movement_id: str,
        symbol: str,
        date: str,
        price_change_pct: float,
        reason: str,
        context: str = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add a significant price movement with explanation.

        Args:
            movement_id: Unique identifier
            symbol: Stock symbol
            date: Date of movement (ISO format)
            price_change_pct: Percentage change
            reason: Why the stock moved
            context: Additional context
            metadata: Additional metadata

        Returns:
            True if successful
        """
        try:
            # Create document for embedding
            document = f"{symbol} moved {price_change_pct:+.2f}% on {date}. Reason: {reason}."
            if context:
                document += f" Context: {context}"

            # Prepare metadata
            meta = {
                "symbol": symbol,
                "date": date,
                "price_change_pct": price_change_pct,
                "reason": reason,
                **(metadata or {})
            }

            self.collections["price_movements"].add(
                documents=[document],
                ids=[movement_id],
                metadatas=[meta]
            )
            return True
        except Exception as e:
            print(f"Error adding price movement: {e}")
            return False

    def search_market_events(
        self,
        query: str,
        n_results: int = 5,
        event_type: str = None
    ) -> Dict[str, Any]:
        """
        Semantic search for market events.

        Args:
            query: Natural language query
            n_results: Number of results to return
            event_type: Filter by event type

        Returns:
            Dict with ids, documents, metadatas, distances
        """
        where = {"event_type": event_type} if event_type else None

        results = self.collections["market_events"].query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        return self._format_results(results)

    def search_news(
        self,
        query: str,
        n_results: int = 5,
        symbols: List[str] = None,
        sentiment: str = None,
        date_from: str = None,
        date_to: str = None
    ) -> Dict[str, Any]:
        """
        Semantic search for news articles.

        Args:
            query: Natural language query
            n_results: Number of results
            symbols: Filter by stock symbols
            sentiment: Filter by sentiment
            date_from: Filter by date (ISO format)
            date_to: Filter by date (ISO format)

        Returns:
            Dict with search results
        """
        # Build where filter
        where = {}
        if sentiment:
            where["sentiment"] = sentiment

        # Note: ChromaDB doesn't support complex date range queries in where clause
        # We'll filter after retrieval if needed

        results = self.collections["news_archive"].query(
            query_texts=[query],
            n_results=n_results * 2 if (symbols or date_from or date_to) else n_results,
            where=where if where else None
        )

        # Post-filter if needed
        if symbols or date_from or date_to:
            results = self._filter_results(results, symbols=symbols, date_from=date_from, date_to=date_to)

        return self._format_results(results, limit=n_results)

    def search_company_info(
        self,
        query: str,
        n_results: int = 5,
        sector: str = None
    ) -> Dict[str, Any]:
        """
        Semantic search for company information.

        Args:
            query: Natural language query (company name, symbol, or description)
            n_results: Number of results
            sector: Filter by sector

        Returns:
            Dict with search results
        """
        where = {"sector": sector} if sector else None

        results = self.collections["company_info"].query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        return self._format_results(results)

    def explain_price_movement(
        self,
        symbol: str,
        date: str,
        n_results: int = 3
    ) -> Dict[str, Any]:
        """
        Find explanations for why a stock moved on a specific date.
        This is the "hover on chart" feature.

        Args:
            symbol: Stock symbol
            date: Date of movement (ISO format)
            n_results: Number of results

        Returns:
            Dict with explanations
        """
        # Query for this specific symbol and date
        query = f"{symbol} price movement on {date}"

        results = self.collections["price_movements"].query(
            query_texts=[query],
            n_results=n_results,
            where={"symbol": symbol}
        )

        # Also search news from that day
        news_results = self.search_news(
            query=f"{symbol} {date}",
            n_results=n_results,
            symbols=[symbol]
        )

        # Combine results
        return {
            "price_movements": self._format_results(results),
            "related_news": news_results
        }

    def _filter_results(
        self,
        results: Dict,
        symbols: List[str] = None,
        date_from: str = None,
        date_to: str = None,
        limit: int = None
    ) -> Dict:
        """Post-filter results"""
        if not results or not results['ids']:
            return results

        filtered_ids = []
        filtered_docs = []
        filtered_metas = []
        filtered_distances = []

        for i, meta in enumerate(results['metadatas'][0]):
            # Filter by symbols
            if symbols:
                result_symbols = meta.get('symbols', '').split(',')
                if not any(s in result_symbols for s in symbols):
                    continue

            # Filter by date range
            if date_from or date_to:
                result_date = meta.get('published_date') or meta.get('date')
                if result_date:
                    if date_from and result_date < date_from:
                        continue
                    if date_to and result_date > date_to:
                        continue

            filtered_ids.append(results['ids'][0][i])
            filtered_docs.append(results['documents'][0][i])
            filtered_metas.append(meta)
            if results.get('distances'):
                filtered_distances.append(results['distances'][0][i])

        return {
            'ids': [filtered_ids[:limit] if limit else filtered_ids],
            'documents': [filtered_docs[:limit] if limit else filtered_docs],
            'metadatas': [filtered_metas[:limit] if limit else filtered_metas],
            'distances': [filtered_distances[:limit] if limit else filtered_distances] if filtered_distances else None
        }

    def _format_results(self, results: Dict, limit: int = None) -> Dict[str, Any]:
        """Format ChromaDB results for API response"""
        if not results or not results['ids'] or not results['ids'][0]:
            return {
                "results": [],
                "count": 0
            }

        formatted_results = []
        for i in range(min(len(results['ids'][0]), limit or len(results['ids'][0]))):
            result = {
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
            }
            if results.get('distances'):
                result["distance"] = results['distances'][0][i]
                result["similarity"] = 1 - results['distances'][0][i]  # Convert distance to similarity

            formatted_results.append(result)

        return {
            "results": formatted_results,
            "count": len(formatted_results)
        }

    def get_collection_stats(self) -> Dict[str, int]:
        """Get count of items in each collection"""
        return {
            name: collection.count()
            for name, collection in self.collections.items()
        }

    def persist(self):
        """Persist all data to disk"""
        self.client.persist()


# RAG Query Engine Classes (consolidated from query_engine.py)
class QueryIntent(str, Enum):
    """Types of queries users can make"""
    PRICE_MOVEMENT = "price_movement"  # "Why did AAPL drop yesterday?"
    MARKET_EVENT = "market_event"  # "Tell me about the 2008 crash"
    COMPANY_INFO = "company_info"  # "What does Tesla do?"
    NEWS_SEARCH = "news_search"  # "Recent news about tech stocks"
    GENERAL = "general"  # General query


class RAGQueryEngine:
    """
    Query engine that combines semantic search with context-aware responses.
    """

    def __init__(self):
        self.chroma = chroma_service

    def classify_intent(self, query: str) -> QueryIntent:
        """
        Classify the intent of a user query.

        Args:
            query: Natural language query

        Returns:
            QueryIntent enum
        """
        query_lower = query.lower()

        # Price movement patterns
        price_keywords = ["why did", "why is", "what happened to", "price", "drop", "rise", "fall", "surge"]
        if any(keyword in query_lower for keyword in price_keywords):
            # Check if there's a stock symbol (uppercase letters)
            if any(word.isupper() for word in query.split()):
                return QueryIntent.PRICE_MOVEMENT

        # Market event patterns
        event_keywords = ["crash", "bubble", "recession", "crisis", "bull market", "bear market", "2008", "2020"]
        if any(keyword in query_lower for keyword in event_keywords):
            return QueryIntent.MARKET_EVENT

        # Company info patterns
        company_keywords = ["what does", "tell me about", "company", "business", "sector"]
        if any(keyword in query_lower for keyword in company_keywords):
            return QueryIntent.COMPANY_INFO

        # News search patterns
        news_keywords = ["news", "recent", "latest", "today", "this week"]
        if any(keyword in query_lower for keyword in news_keywords):
            return QueryIntent.NEWS_SEARCH

        return QueryIntent.GENERAL

    def extract_symbol(self, query: str) -> Optional[str]:
        """
        Extract stock symbol from query.

        Args:
            query: Natural language query

        Returns:
            Stock symbol in uppercase, or None
        """
        import re

        # Look for uppercase words that look like stock symbols
        words = query.split()
        for word in words:
            word = word.strip('.,!?')
            if len(word) >= 1 and len(word) <= 5 and word.isupper() and word.isalpha():
                # Common stock symbols
                return word

        return None

    def extract_date(self, query: str) -> Optional[str]:
        """
        Extract date references from query.

        Args:
            query: Natural language query

        Returns:
            ISO date string or None
        """
        import re
        from datetime import datetime, timedelta

        query_lower = query.lower()

        # Yesterday
        if 'yesterday' in query_lower:
            yesterday = datetime.now() - timedelta(days=1)
            return yesterday.strftime('%Y-%m-%d')

        # Today
        if 'today' in query_lower:
            return datetime.now().strftime('%Y-%m-%d')

        # Specific year
        year_match = re.search(r'\b(20\d{2})\b', query)
        if year_match:
            return f"{year_match.group(1)}-12-31"  # End of year

        return None

    def search(self, query: str, limit: int = 5, include_sources: bool = True) -> Dict[str, Any]:
        """
        Main search method that classifies intent and performs semantic search.

        Args:
            query: Natural language query
            limit: Maximum results to return
            include_sources: Whether to include source metadata

        Returns:
            Search results with intent classification
        """
        from datetime import datetime

        # Classify intent
        intent = self.classify_intent(query)

        # Extract entities
        symbol = self.extract_symbol(query)
        date_str = self.extract_date(query)

        # Search based on intent
        results = []

        if intent.value == "price_movement" and symbol:
            # Search price movement collection
            query_results = self.chroma.collections["price_movements"].query(
                query_texts=[query],
                n_results=limit
            )
            results = query_results["documents"][0] if query_results["documents"] else []

        elif intent.value == "market_event":
            # Search market events
            query_results = self.chroma.collections["market_events"].query(
                query_texts=[query],
                n_results=limit
            )
            results = query_results["documents"][0] if query_results["documents"] else []

        elif intent.value == "company_info" and symbol:
            # Search company info
            query_results = self.chroma.collections["company_info"].query(
                query_texts=[f"{symbol} company information"],
                n_results=limit
            )
            results = query_results["documents"][0] if query_results["documents"] else []

        elif intent.value == "news_search":
            # Search news archive
            query_results = self.chroma.collections["news_archive"].query(
                query_texts=[query],
                n_results=limit
            )
            results = query_results["documents"][0] if query_results["documents"] else []

        else:
            # General search across all collections
            all_results = []
            for collection_name, collection in self.chroma.collections.items():
                try:
                    query_results = collection.query(
                        query_texts=[query],
                        n_results=max(1, limit // 4)
                    )
                    if query_results["documents"]:
                        all_results.extend(query_results["documents"][0])
                except Exception as e:
                    print(f"Error querying {collection_name}: {e}")
            results = all_results[:limit]

        return {
            "query": query,
            "intent": intent.value,
            "symbol": symbol,
            "date": date_str,
            "results": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }


# Global instances
chroma_service = ChromaService()
rag_engine = RAGQueryEngine()
