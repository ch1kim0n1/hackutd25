import redis
import asyncio
import json
from typing import Callable, Dict, List
from datetime import datetime

class AgentNetwork:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.handlers: Dict[str, Callable] = {}
        self.message_log: List[Dict] = []
        self.paused = False  # NEW: Support for user agent pause functionality

    async def initialize(self):
        self.pubsub.subscribe(["agent_messages"])

    async def publish(self, channel: str, message: Dict):
        # NEW: Check if agents are paused (for User Agent integration)
        if self.paused and channel != "user_input":
            # Queue messages instead of publishing when paused
            self.message_log.append({
                "status": "queued",
                "timestamp": datetime.now().isoformat(),
                "channel": channel,
                "data": message
            })
            return
            
        msg = {
            "timestamp": datetime.now().isoformat(),
            "channel": channel,
            "data": message
        }
        
        self.redis_client.publish("agent_messages", json.dumps(msg))
        self.message_log.append(msg)

    async def subscribe(self, channel: str, handler: Callable):
        self.handlers[channel] = handler

    async def broadcast_agent_communication(self, from_agent: str, to_agent: str, message: str):
        """
        Broadcasts agent-to-agent communication visible in the War Room UI.
        This is a key feature for transparency in the refined vision.
        """
        comm = {
            "from": from_agent,
            "to": to_agent,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "type": "agent_debate"  # NEW: Tag for War Room visualization
        }
        await self.publish("agent_communication", comm)

    async def get_agent_messages(self, count: int = 50):
        messages = self.redis_client.lrange("agent_messages", 0, count - 1)
        return [json.loads(msg) for msg in messages]

    async def listen(self):
        while True:
            message = self.pubsub.get_message()
            if message and message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    channel = data.get('channel')
                    
                    if channel and channel in self.handlers:
                        await self.handlers[channel](data)
                except (json.JSONDecodeError, KeyError):
                    pass
            await asyncio.sleep(0.1)

    # NEW: User Agent pause/resume functionality
    async def pause_agents(self, reason: str = "User interjection"):
        """
        Pauses all agents when user wants to provide input.
        Critical for the human-in-the-loop feature in refined vision.
        """
        self.paused = True
        await self.broadcast_agent_communication(
            "User Agent",
            "All Agents",
            f"🛑 PAUSED: {reason}. Waiting for user input."
        )

    async def resume_agents(self, user_input: str = ""):
        """
        Resumes agent operations after user input is processed.
        """
        self.paused = False
        if user_input:
            await self.publish("user_input", {
                "input": user_input,
                "timestamp": datetime.now().isoformat()
            })
        
        await self.broadcast_agent_communication(
            "User Agent",
            "All Agents",
            f"✅ RESUMED: Processing user feedback - '{user_input[:50]}...'"
        )

