import redis
import asyncio
import json
from typing import Callable, Dict, List
from datetime import datetime
from contextlib import suppress

class AgentNetwork:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.pubsub = None
        self.handlers: Dict[str, Callable] = {}
        self.message_log: List[Dict] = []
        self.paused = False  # NEW: Support for user agent pause functionality
        self.redis_available = False
        # Best-effort: detect Redis availability without failing hard
        try:
            # ping lazily; if this fails we operate in in-memory mode
            self.redis_client.ping()
            self.redis_available = True
            self.pubsub = self.redis_client.pubsub()
        except Exception:
            self.redis_available = False

    async def initialize(self):
        # Subscribe only if Redis is available
        if self.redis_available and self.pubsub is not None:
            with suppress(Exception):
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
        # Always keep local history for demo/War Room even if Redis is unavailable
        self.message_log.append(msg)
        # Best-effort publish to Redis
        if self.redis_available:
            with suppress(Exception):
                self.redis_client.publish("agent_messages", json.dumps(msg))

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
        # Legacy method: prefer in-memory log if available
        if self.message_log:
            return list(self.message_log)[-count:]
        if self.redis_available:
            messages = self.redis_client.lrange("agent_messages", 0, count - 1)
            return [json.loads(msg) for msg in messages]
        return []

    async def get_message_history(self, limit: int = 50):
        # New helper used by server relay
        if not self.message_log:
            return []
        return list(self.message_log)[-limit:]

    async def listen(self):
        # If Redis isn't available, operate in no-op listen loop so the app remains responsive
        while True:
            if self.redis_available and self.pubsub is not None:
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

