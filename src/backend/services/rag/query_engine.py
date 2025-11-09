# backend/services/rag/query_engine.py
"""
RAG Query Engine for APEX.
Handles semantic search queries and generates contextualized responses using LLM.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from enum import Enum

from .chroma_service import chroma_service


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
            Stock symbol if found, None otherwise
        """
        # Look for all-caps words that are 1-5 characters (typical ticker length)
        words = query.split()
        for word in words:
            # Remove punctuation
            clean_word = word.strip(".,!?;:")
            # Check if it's all caps and reasonable ticker length
            if clean_word.isupper() and 1 <= len(clean_word) <= 5:
                return clean_word
        return None

    def extract_date(self, query: str) -> Optional[str]:
        """
        Extract date from query.

        Args:
            query: Natural language query

        Returns:
            ISO date string if found, None otherwise
        """
        # Simple date extraction for common patterns
        query_lower = query.lower()

        if "today" in query_lower:
            return date.today().isoformat()
        elif "yesterday" in query_lower:
            from datetime import timedelta
            return (date.today() - timedelta(days=1)).isoformat()

        # TODO: Add more sophisticated date parsing (e.g., "last week", "March 2020")
        return None

    async def query(
        self,
        query_text: str,
        n_results: int = 5,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Main query method that handles all types of queries.

        Args:
            query_text: Natural language query
            n_results: Number of results to return
            include_context: Whether to include full context in response

        Returns:
            Dict with results and metadata
        """
        # Classify intent
        intent = self.classify_intent(query_text)

        # Extract entities
        symbol = self.extract_symbol(query_text)
        query_date = self.extract_date(query_text)

        # Route to appropriate handler
        if intent == QueryIntent.PRICE_MOVEMENT and symbol:
            return await self._handle_price_movement(symbol, query_date, n_results)
        elif intent == QueryIntent.MARKET_EVENT:
            return await self._handle_market_event(query_text, n_results)
        elif intent == QueryIntent.COMPANY_INFO:
            return await self._handle_company_info(query_text, n_results)
        elif intent == QueryIntent.NEWS_SEARCH:
            return await self._handle_news_search(query_text, symbol, n_results)
        else:
            return await self._handle_general_query(query_text, n_results)

    async def _handle_price_movement(
        self,
        symbol: str,
        date_str: Optional[str],
        n_results: int
    ) -> Dict[str, Any]:
        """Handle price movement queries"""
        if not date_str:
            date_str = date.today().isoformat()

        # Search for explanations
        results = self.chroma.explain_price_movement(symbol, date_str, n_results)

        return {
            "intent": QueryIntent.PRICE_MOVEMENT,
            "symbol": symbol,
            "date": date_str,
            "results": results,
            "answer_type": "price_explanation"
        }

    async def _handle_market_event(
        self,
        query: str,
        n_results: int
    ) -> Dict[str, Any]:
        """Handle market event queries"""
        results = self.chroma.search_market_events(query, n_results)

        return {
            "intent": QueryIntent.MARKET_EVENT,
            "query": query,
            "results": results,
            "answer_type": "market_event"
        }

    async def _handle_company_info(
        self,
        query: str,
        n_results: int
    ) -> Dict[str, Any]:
        """Handle company information queries"""
        results = self.chroma.search_company_info(query, n_results)

        return {
            "intent": QueryIntent.COMPANY_INFO,
            "query": query,
            "results": results,
            "answer_type": "company_info"
        }

    async def _handle_news_search(
        self,
        query: str,
        symbol: Optional[str],
        n_results: int
    ) -> Dict[str, Any]:
        """Handle news search queries"""
        symbols = [symbol] if symbol else None

        results = self.chroma.search_news(
            query,
            n_results=n_results,
            symbols=symbols
        )

        return {
            "intent": QueryIntent.NEWS_SEARCH,
            "query": query,
            "symbol": symbol,
            "results": results,
            "answer_type": "news"
        }

    async def _handle_general_query(
        self,
        query: str,
        n_results: int
    ) -> Dict[str, Any]:
        """Handle general queries by searching all collections"""
        # Search all collections and combine results
        market_events = self.chroma.search_market_events(query, n_results=2)
        news = self.chroma.search_news(query, n_results=2)
        company_info = self.chroma.search_company_info(query, n_results=2)

        # Combine and sort by relevance (distance/similarity)
        all_results = []

        for result in market_events.get("results", []):
            result["source"] = "market_events"
            all_results.append(result)

        for result in news.get("results", []):
            result["source"] = "news"
            all_results.append(result)

        for result in company_info.get("results", []):
            result["source"] = "company_info"
            all_results.append(result)

        # Sort by similarity (higher is better)
        all_results.sort(key=lambda x: x.get("similarity", 0), reverse=True)

        return {
            "intent": QueryIntent.GENERAL,
            "query": query,
            "results": {
                "results": all_results[:n_results],
                "count": len(all_results[:n_results])
            },
            "answer_type": "general"
        }

    async def hover_explain(
        self,
        symbol: str,
        date_str: str,
        price_change_pct: float
    ) -> Dict[str, Any]:
        """
        Special method for chart hover feature.
        User hovers over a price point and gets an explanation.

        Args:
            symbol: Stock symbol
            date_str: Date of the price point (ISO format)
            price_change_pct: Percentage change on that day

        Returns:
            Explanation of price movement
        """
        # Search for specific movement
        results = self.chroma.explain_price_movement(symbol, date_str, n_results=3)

        # Check if we found anything
        if results["price_movements"]["count"] == 0 and results["related_news"]["count"] == 0:
            return {
                "symbol": symbol,
                "date": date_str,
                "price_change_pct": price_change_pct,
                "explanation": f"No specific explanation found for {symbol}'s {price_change_pct:+.2f}% move on {date_str}.",
                "has_data": False
            }

        # Format explanation
        explanation_parts = []

        # Price movement explanations
        if results["price_movements"]["count"] > 0:
            top_movement = results["price_movements"]["results"][0]
            explanation_parts.append(top_movement["metadata"].get("reason", ""))

        # News explanations
        if results["related_news"]["count"] > 0:
            top_news = results["related_news"]["results"][0]
            explanation_parts.append(f"Related news: {top_news['metadata'].get('title', '')}")

        return {
            "symbol": symbol,
            "date": date_str,
            "price_change_pct": price_change_pct,
            "explanation": " ".join(explanation_parts),
            "has_data": True,
            "sources": results
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        collection_stats = self.chroma.get_collection_stats()

        return {
            "total_documents": sum(collection_stats.values()),
            "collections": collection_stats,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "vector_dimensions": 384
        }


# Global instance
rag_engine = RAGQueryEngine()
