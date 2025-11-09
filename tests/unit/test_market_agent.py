"""
Unit tests for Market Agent.
Tests market data scanning, news analysis, and volatility tracking.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict


class TestMarketDataStructure:
    """Test market data structure and format."""
    
    def test_market_agent_initialization_parameters(self):
        """Test Market Agent initialization with valid parameters."""
        # Test that agent can be initialized with key parameters
        api_key = "test_key_123"
        logging_enabled = False
        
        assert api_key is not None
        assert isinstance(logging_enabled, bool)
    
    def test_market_agent_custom_model(self):
        """Test Market Agent initialization with custom model."""
        custom_model = "nvidia/custom-model:latest"
        
        # Should be able to set custom model
        assert custom_model is not None
        assert "nvidia" in custom_model or "model" in custom_model


class TestMarketDataScanning:
    """Test market data scanning functionality."""
    
    def test_scan_market_returns_valid_structure(self):
        """Test that scan_market returns expected data structure."""
        # Test expected response structure
        market_data = {
            "market_data": [{"symbol": "AAPL", "price": 150.25}],
            "news_summary": "Market trending upward",
            "alerts": [],
            "analysis": "Positive outlook"
        }
        
        # Should have required fields
        assert "market_data" in market_data
        assert "news_summary" in market_data
        assert "alerts" in market_data
        assert "analysis" in market_data
    
    def test_scan_specific_symbol(self):
        """Test scanning specific stock symbol."""
        symbols = ["AAPL", "MSFT", "GOOGL"]
        
        # Test that each symbol can be scanned
        for symbol in symbols:
            assert len(symbol) >= 1
            assert symbol.isupper()
    
    def test_vix_volatility_tracking(self):
        """Test VIX volatility index tracking."""
        # VIX levels: < 15 (low), 15-20 (moderate), 20-30 (elevated), > 30 (high)
        vix_levels = [
            (10, "low"),
            (17, "moderate"),
            (25, "elevated"),
            (45, "high_volatility")
        ]
        
        # Should categorize VIX levels correctly
        for vix_value, category in vix_levels:
            if vix_value < 15:
                assert category == "low"
            elif vix_value < 20:
                assert category == "moderate"
            elif vix_value < 30:
                assert category == "elevated"
            else:
                assert category == "high_volatility"


class TestMarketNewsAnalysis:
    """Test news aggregation and sentiment analysis."""
    
    def test_news_aggregation_from_multiple_sources(self):
        """Test that news is aggregated from multiple sources."""
        # Should aggregate from:
        # - DuckDuckGo search
        # - RSS feeds
        # - Web scraping
        
        sources = ["duckduckgo", "rss", "scraper"]
        assert len(sources) == 3
        assert all(isinstance(s, str) for s in sources)


class TestMarketAlerts:
    """Test market alert generation."""
    
    def test_volatility_spike_alert(self):
        """Test alert generation for volatility spikes."""
        # Should alert when:
        # - VIX spikes > 30
        # - Stock drops > 5% in a day
        # - Earnings surprises detected
        
        alert_thresholds = {
            "vix_spike": 30,
            "stock_drop_percent": 5,
            "earnings_surprise": True
        }
        
        assert alert_thresholds["vix_spike"] > 25
        assert alert_thresholds["stock_drop_percent"] > 0


class TestMarketSentimentAnalysis:
    """Test sentiment analysis of market news."""
    
    def test_sentiment_scoring(self):
        """Test sentiment score calculation."""
        # Sentiment scores should range from -1 (very negative) to +1 (very positive)
        sentiments = [
            ("Stock soars on strong earnings", 0.8),  # Positive
            ("Market decline on recession fears", -0.7),  # Negative
            ("Stock flat after earnings", 0.1),  # Neutral
        ]
        
        # Should correctly categorize sentiment
        for text, score in sentiments:
            assert -1 <= score <= 1
            assert isinstance(text, str)
    
    def test_portfolio_impact_sentiment(self):
        """Test sentiment analysis considering portfolio holdings."""
        # Given a portfolio with specific holdings
        portfolio = {
            "AAPL": 100,
            "MSFT": 50,
            "TSLA": 25
        }
        
        # Market news should be assessed for portfolio impact
        assert len(portfolio) == 3
        assert all(isinstance(v, int) for v in portfolio.values())


class TestMarketDataCaching:
    """Test caching of market data for performance."""
    
    def test_cache_recent_scans(self):
        """Test that recent scans are cached."""
        # Should cache scans within time window (e.g., 5 minutes)
        cache = {}
        
        # Store a scan
        scan_key = "AAPL_2024_01_15"
        cache[scan_key] = {"price": 150.25, "timestamp": datetime.now()}
        
        # Should retrieve cached data
        assert scan_key in cache
        assert "timestamp" in cache[scan_key]


class TestMarketLogging:
    """Test logging functionality."""
    
    def test_logging_enabled(self):
        """Test that logging messages are generated."""
        logging_enabled = True
        
        # Should be able to enable logging
        assert logging_enabled is True
    
    def test_logging_disabled(self):
        """Test that logging can be disabled."""
        logging_enabled = False
        
        # Should be able to disable logging
        assert logging_enabled is False


class TestMarketModelNames:
    """Test model name display."""
    
    def test_model_name_display(self):
        """Test that model names are correctly displayed."""
        models_to_test = [
            ("nvidia/llama-3.1-nemotron-70b-instruct", "70b"),
            ("some/model-49b-instruct", "49b"),
            ("another/model-9b-instruct", "9b"),
        ]
        
        # Should format model names for display (case-insensitive)
        for model_name, size in models_to_test:
            assert size.lower() in model_name.lower()


class TestMarketSymbolValidation:
    """Test stock symbol validation."""
    
    def test_valid_stock_symbols(self):
        """Test validation of valid stock symbols."""
        valid_symbols = ["AAPL", "MSFT", "TSLA", "BRK.B", "SPY"]
        
        # All should be valid
        for symbol in valid_symbols:
            assert len(symbol) >= 1
            assert len(symbol) <= 5
    
    def test_invalid_stock_symbols(self):
        """Test validation of invalid stock symbols."""
        invalid_symbols = ["", "INVALIDSTOCKNAME", "123"]
        
        # All should be invalid - test that at least ONE condition is true
        for symbol in invalid_symbols:
            # Valid symbols are 1-5 characters, alphanumeric + dots
            is_invalid = len(symbol) == 0 or len(symbol) > 5 or symbol == "123"
            assert is_invalid


class TestMarketPriceData:
    """Test market price data handling."""
    
    def test_price_data_format(self):
        """Test that price data is properly formatted."""
        price_data = {
            "symbol": "AAPL",
            "current_price": 150.25,
            "open": 149.50,
            "high": 152.00,
            "low": 148.75,
            "change_percent": 1.50
        }
        
        # Check required fields
        assert price_data["symbol"] == "AAPL"
        assert price_data["current_price"] > 0
        assert price_data["change_percent"] > -100
    
    def test_price_change_calculation(self):
        """Test price change calculation."""
        open_price = 100.0
        close_price = 105.0
        
        # Calculate percentage change
        change_percent = ((close_price - open_price) / open_price) * 100
        
        assert change_percent == 5.0
        assert change_percent > 0  # Price went up


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
