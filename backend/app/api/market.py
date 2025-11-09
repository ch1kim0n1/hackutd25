from backend.core.agent_network import AgentNetwork

async def get_market_data(symbol: str):
    """
    Could call a MarketAgent internally or AlpacaBroker directly
    """
    # Placeholder: return mock data for now
    return {
        "symbol": symbol,
        "open": 100.0,
        "high": 105.0,
        "low": 95.0,
        "close": 102.0,
        "volume": 1000000
    }
