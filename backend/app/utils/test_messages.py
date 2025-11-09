"""
Test Message Generator for War Room
Sends test messages to WebSocket clients for Phase 2 testing
"""

import asyncio
import random
from datetime import datetime


class TestMessageGenerator:
    """Generates realistic test messages for War Room testing"""
    
    def __init__(self, connection_manager):
        self.manager = connection_manager
        self.is_running = False
        
        # Sample agent conversations
        self.conversations = [
            {
                "from": "market",
                "content": "🔍 Scanning market conditions... VIX at 18.5, showing moderate volatility. Tech sector down 1.2% today."
            },
            {
                "from": "strategy",
                "content": "🧠 Based on current market conditions, I recommend a defensive tilt. Increase bond allocation to 30%."
            },
            {
                "from": "risk",
                "content": "⚠️ Running Monte Carlo simulation... 10,000 scenarios. Proposed allocation has 85% probability of meeting goals."
            },
            {
                "from": "strategy",
                "content": "🧠 Noted. Let me recalculate with lower equity exposure to improve risk metrics."
            },
            {
                "from": "risk",
                "content": "⚠️ Improved! Max drawdown reduced from 22% to 16%. I approve this strategy."
            },
            {
                "from": "executor",
                "content": "⚡ Executing trades: SELL 50 shares SPY @ $445.20, BUY 25 shares TLT @ $92.50"
            },
            {
                "from": "explainer",
                "content": "💬 Here's what just happened: We reduced stock exposure because market volatility is elevated. This protects your portfolio during uncertainty."
            },
            {
                "from": "market",
                "content": "🔍 News alert: Fed hints at rate hold. Bond yields dropping. This supports our defensive positioning."
            },
            {
                "from": "strategy",
                "content": "🧠 Excellent timing! The market is validating our allocation shift. Monitoring for rebalancing opportunities."
            }
        ]
    
    async def start(self, interval: float = 3.0):
        """Start generating test messages"""
        self.is_running = True
        
        print("🧪 Test message generator started")
        
        # Send welcome message
        await self.manager.broadcast({
            "type": "system",
            "from": "system",
            "to": "all",
            "content": "🧪 Test mode: Simulating agent conversations for demonstration",
            "timestamp": datetime.now().isoformat(),
            "data": {"test_mode": True}
        })
        
        conversation_index = 0
        
        while self.is_running:
            if len(self.manager.active_connections) > 0:
                # Get next message in sequence
                msg = self.conversations[conversation_index]
                
                # Send message
                await self.manager.broadcast({
                    "type": "agent_message",
                    "from": msg["from"],
                    "to": "all",
                    "content": msg["content"],
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "test_mode": True,
                        "sequence": conversation_index
                    }
                })
                
                print(f"📤 Sent test message from {msg['from']}")
                
                # Move to next message (loop around)
                conversation_index = (conversation_index + 1) % len(self.conversations)
                
            await asyncio.sleep(interval)
    
    def stop(self):
        """Stop generating test messages"""
        self.is_running = False
        print("🛑 Test message generator stopped")


# Standalone test function
async def test_war_room_messages():
    """Test the message generator standalone"""
    
    class MockManager:
        def __init__(self):
            self.active_connections = [1]  # Fake connection
        
        async def broadcast(self, msg):
            print(f"📨 {msg['from']}: {msg['content']}")
    
    manager = MockManager()
    generator = TestMessageGenerator(manager)
    
    # Run for 30 seconds
    task = asyncio.create_task(generator.start(interval=2.0))
    await asyncio.sleep(30)
    generator.stop()
    await task


if __name__ == "__main__":
    asyncio.run(test_war_room_messages())
