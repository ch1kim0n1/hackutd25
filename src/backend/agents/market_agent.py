import asyncio
from typing import Dict
from datetime import datetime
import numpy as np

class MarketAgent:
    def __init__(self, agent_network):
        self.agent_network = agent_network
        self.name = "Market Agent"
        self.current_regime = "Bull Market"
        self.vix_level = 18.4

    async def initialize(self):
        asyncio.create_task(self.monitor_market())
        return {"status": "initialized", "agent": self.name}

    async def monitor_market(self):
        while True:
            market_data = await self.fetch_market_data()
            regime = self.detect_regime(market_data)
            
            if regime != self.current_regime:
                self.current_regime = regime
                await self.agent_network.publish("market_regime_change", {
                    "old_regime": self.current_regime,
                    "regime": regime,
                    "confidence": 0.87,
                    "evidence": ["VIX elevated", "Spreads widening", "Sector rotation"]
                })
            
            await asyncio.sleep(300)

    async def fetch_market_data(self) -> Dict:
        vix = np.random.uniform(15, 35)
        yield_spread = np.random.uniform(0.8, 2.5)
        credit_spread = np.random.uniform(100, 300)
        
        return {
            "vix": vix,
            "yield_spread": yield_spread,
            "credit_spread": credit_spread,
            "timestamp": datetime.now().isoformat()
        }

    def detect_regime(self, market_data: Dict) -> str:
        vix = market_data.get("vix", 20)
        spread = market_data.get("yield_spread", 1.2)
        
        if vix > 40 or spread > 2.0:
            return "Crisis Mode"
        elif vix > 30 or spread > 1.8:
            return "High Volatility"
        elif vix > 20:
            return "Moderate Volatility"
        else:
            return "Low Volatility"

    async def analyze_sentiment(self) -> Dict:
        sentiment = {
            "news_sentiment": np.random.uniform(-1, 1),
            "social_sentiment": np.random.uniform(-1, 1),
            "technical_strength": np.random.uniform(0, 100),
            "timestamp": datetime.now().isoformat()
        }
        
        return sentiment

    async def predict_regime_transition(self) -> Dict:
        return {
            "transition_probability": np.random.uniform(0, 1),
            "target_regime": "Recovery",
            "expected_duration": "2-4 weeks"
        }

    async def get_sector_rotation_data(self) -> Dict:
        sectors = ["Technology", "Financials", "Energy", "Utilities", "Consumer Staples"]
        rotation_data = {}
        
        for sector in sectors:
            rotation_data[sector] = {
                "performance": np.random.uniform(-5, 5),
                "momentum": np.random.uniform(-1, 1),
                "correlation_market": np.random.uniform(0.3, 0.95)
            }
        
        return rotation_data

