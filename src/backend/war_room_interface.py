"""
APEX War Room Interface
Real-time agent communication display for transparent multi-agent collaboration.

This is the KEY differentiator: Users can see and participate in agent debates.
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import deque
import json


@dataclass
class AgentMessage:
    """Single message in the War Room"""
    id: str
    from_agent: str
    to_agent: str
    message: str
    timestamp: str
    message_type: str  # debate, alert, decision, user_input
    importance: str  # low, medium, high, critical
    metadata: Optional[Dict] = None

    def to_dict(self):
        return asdict(self)


class WarRoomInterface:
    """
    War Room interface for displaying real-time agent communications.

    Features:
    - Real-time message streaming
    - Color-coded agent debates
    - User interjection support
    - Message filtering and search
    - Export for analysis
    """

    def __init__(self, agent_network, max_messages: int = 500):
        self.agent_network = agent_network
        self.max_messages = max_messages

        # Message storage
        self.messages: deque = deque(maxlen=max_messages)
        self.message_counter = 0

        # Agent profiles for UI display
        self.agent_profiles = {
            "Market Agent": {
                "emoji": "🔍",
                "color": "#3b82f6",  # Blue
                "role": "Scans markets, tracks volatility, analyzes sentiment"
            },
            "Strategy Agent": {
                "emoji": "🧠",
                "color": "#8b5cf6",  # Purple
                "role": "Optimizes portfolios, evaluates opportunities"
            },
            "Risk Agent": {
                "emoji": "⚠️",
                "color": "#ef4444",  # Red
                "role": "Enforces risk limits, runs simulations"
            },
            "Executor Agent": {
                "emoji": "⚡",
                "color": "#10b981",  # Green
                "role": "Places trades, validates orders"
            },
            "Explainer Agent": {
                "emoji": "💬",
                "color": "#f59e0b",  # Orange
                "role": "Translates decisions to plain English"
            },
            "User": {
                "emoji": "👤",
                "color": "#06b6d4",  # Cyan
                "role": "Human participant with veto power"
            }
        }

        # Active debate tracking
        self.active_debates = []
        self.user_can_interject = True

    async def initialize(self):
        """Initialize War Room and subscribe to agent communications"""
        await self.agent_network.subscribe("agent_communication", self._handle_agent_message)
        await self.agent_network.subscribe("user_input", self._handle_user_input)

        # Add welcome message
        self._add_system_message(
            "🎬 APEX War Room initialized. All agent communications will appear here.",
            importance="high"
        )

    async def _handle_agent_message(self, message_data: Dict):
        """Handle incoming agent communication"""
        data = message_data.get("data", {})

        msg = AgentMessage(
            id=f"msg_{self.message_counter}",
            from_agent=data.get("from", "System"),
            to_agent=data.get("to", "All"),
            message=data.get("message", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            message_type=data.get("type", "debate"),
            importance=self._classify_importance(data.get("message", "")),
            metadata=data.get("metadata")
        )

        self.messages.append(msg)
        self.message_counter += 1

        # Check if this is a critical debate moment (good time for user input)
        if self._is_decision_point(msg):
            self.user_can_interject = True
            self._add_system_message(
                "⏸️ DECISION POINT: You can interject now with your opinion.",
                importance="critical"
            )

    async def _handle_user_input(self, message_data: Dict):
        """Handle user interjection"""
        data = message_data.get("data", {})

        msg = AgentMessage(
            id=f"msg_{self.message_counter}",
            from_agent="User",
            to_agent="All Agents",
            message=data.get("input", data.get("feedback", "")),
            timestamp=datetime.now().isoformat(),
            message_type="user_input",
            importance="high",
            metadata={"action": data.get("action")}
        )

        self.messages.append(msg)
        self.message_counter += 1

        # Pause agents to process user input
        await self.agent_network.pause_agents("User interjection")

    def _classify_importance(self, message: str) -> str:
        """Classify message importance based on content"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["critical", "emergency", "urgent", "rejected"]):
            return "critical"
        elif any(word in message_lower for word in ["warning", "alert", "elevated"]):
            return "high"
        elif any(word in message_lower for word in ["approved", "complete", "decision"]):
            return "medium"
        else:
            return "low"

    def _is_decision_point(self, msg: AgentMessage) -> bool:
        """Determine if this is a good moment for user interjection"""
        # Decision points: Risk rejection, Strategy proposal, Trade execution pending
        decision_keywords = ["rejected", "approve", "execute", "recommendation", "proposed"]
        return any(keyword in msg.message.lower() for keyword in decision_keywords)

    def _add_system_message(self, message: str, importance: str = "medium"):
        """Add a system message to the War Room"""
        msg = AgentMessage(
            id=f"msg_{self.message_counter}",
            from_agent="System",
            to_agent="All",
            message=message,
            timestamp=datetime.now().isoformat(),
            message_type="system",
            importance=importance
        )
        self.messages.append(msg)
        self.message_counter += 1

    # ========================================
    # PUBLIC API FOR UI
    # ========================================

    def get_recent_messages(self, limit: int = 50) -> List[Dict]:
        """Get recent messages for UI display"""
        messages = list(self.messages)[-limit:]
        return [msg.to_dict() for msg in messages]

    def get_messages_by_agent(self, agent_name: str, limit: int = 50) -> List[Dict]:
        """Get messages from specific agent"""
        filtered = [msg for msg in self.messages if msg.from_agent == agent_name]
        return [msg.to_dict() for msg in filtered[-limit:]]

    def get_critical_messages(self, limit: int = 20) -> List[Dict]:
        """Get high-priority messages"""
        critical = [msg for msg in self.messages if msg.importance in ["critical", "high"]]
        return [msg.to_dict() for msg in critical[-limit:]]

    def search_messages(self, query: str, limit: int = 50) -> List[Dict]:
        """Search messages by content"""
        query_lower = query.lower()
        matches = [
            msg for msg in self.messages
            if query_lower in msg.message.lower() or query_lower in msg.from_agent.lower()
        ]
        return [msg.to_dict() for msg in matches[-limit:]]

    def get_agent_stats(self) -> Dict:
        """Get statistics on agent activity"""
        stats = {}

        for agent_name in self.agent_profiles.keys():
            agent_messages = [msg for msg in self.messages if msg.from_agent == agent_name]
            stats[agent_name] = {
                "total_messages": len(agent_messages),
                "critical_messages": len([m for m in agent_messages if m.importance == "critical"]),
                "last_message_time": agent_messages[-1].timestamp if agent_messages else None,
                **self.agent_profiles[agent_name]
            }

        return stats

    def export_conversation(self, filename: Optional[str] = None) -> str:
        """Export entire conversation to JSON"""
        if filename is None:
            filename = f"war_room_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_messages": len(self.messages),
            "messages": [msg.to_dict() for msg in self.messages],
            "agent_stats": self.get_agent_stats()
        }

        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)

        return filename

    def get_debate_summary(self) -> Dict:
        """Generate summary of current debate state"""
        recent_messages = list(self.messages)[-20:]

        # Identify active participants
        active_agents = set(msg.from_agent for msg in recent_messages if msg.from_agent != "System")

        # Identify current topic
        topics = {
            "risk": 0,
            "strategy": 0,
            "execution": 0,
            "market": 0
        }

        for msg in recent_messages:
            msg_lower = msg.message.lower()
            for topic in topics:
                if topic in msg_lower:
                    topics[topic] += 1

        current_topic = max(topics.items(), key=lambda x: x[1])[0] if topics else "general"

        # Check for conflicts/disagreements
        conflicts = [
            msg for msg in recent_messages
            if any(word in msg.message.lower() for word in ["rejected", "disagree", "concern", "warning"])
        ]

        return {
            "active_agents": list(active_agents),
            "current_topic": current_topic,
            "has_conflicts": len(conflicts) > 0,
            "conflict_count": len(conflicts),
            "recent_conflict": conflicts[-1].to_dict() if conflicts else None,
            "user_can_interject": self.user_can_interject,
            "message_count_last_5min": len(recent_messages)
        }

    # ========================================
    # REAL-TIME STREAMING (for WebSocket)
    # ========================================

    async def stream_messages(self, websocket):
        """Stream messages in real-time to WebSocket client"""
        last_sent_id = -1

        while True:
            # Get new messages since last send
            new_messages = [
                msg.to_dict() for msg in self.messages
                if int(msg.id.split('_')[1]) > last_sent_id
            ]

            if new_messages:
                await websocket.send_json({
                    "type": "war_room_update",
                    "messages": new_messages,
                    "stats": self.get_agent_stats(),
                    "debate_summary": self.get_debate_summary()
                })

                last_sent_id = int(new_messages[-1]["id"].split('_')[1])

            await asyncio.sleep(0.5)  # Poll every 500ms

    def format_for_terminal(self, limit: int = 10) -> str:
        """Format messages for terminal display"""
        messages = list(self.messages)[-limit:]
        output = []

        output.append("╔════════════════════════════════════════════════════════════════╗")
        output.append("║                    🎬 APEX WAR ROOM                           ║")
        output.append("╚════════════════════════════════════════════════════════════════╝")
        output.append("")

        for msg in messages:
            profile = self.agent_profiles.get(msg.from_agent, {"emoji": "📡", "color": "#gray"})
            timestamp = datetime.fromisoformat(msg.timestamp).strftime("%H:%M:%S")

            # Format message
            importance_marker = {
                "critical": "🚨",
                "high": "⚠️ ",
                "medium": "ℹ️ ",
                "low": "  "
            }[msg.importance]

            output.append(f"{importance_marker} [{timestamp}] {profile['emoji']} {msg.from_agent}")
            output.append(f"   → {msg.to_agent}: {msg.message}")
            output.append("")

        output.append("═" * 64)
        output.append(f"Total messages: {len(self.messages)} | User can interject: {self.user_can_interject}")

        return "\n".join(output)


# ========================================
# EXAMPLE USAGE
# ========================================

async def demo_war_room():
    """Demo of War Room interface"""
    from core.agent_network import AgentNetwork

    network = AgentNetwork()
    await network.initialize()

    war_room = WarRoomInterface(network)
    await war_room.initialize()

    # Simulate agent conversation
    await network.broadcast_agent_communication(
        "Market Agent", "Strategy Agent",
        "VIX at 22.5, elevated volatility detected. Recommend defensive positioning."
    )

    await asyncio.sleep(1)

    await network.broadcast_agent_communication(
        "Strategy Agent", "Risk Agent",
        "Proposing 60/30/10 allocation: SPY/TLT/GLD. Expected Sharpe: 0.85"
    )

    await asyncio.sleep(1)

    await network.broadcast_agent_communication(
        "Risk Agent", "Strategy Agent",
        "⚠️ VaR95 at 4.2%, stress test shows 28% loss in 2008 scenario. Recommend more bonds."
    )

    # Print War Room display
    print(war_room.format_for_terminal())

    # Export conversation
    filename = war_room.export_conversation()
    print(f"\nConversation exported to: {filename}")


if __name__ == "__main__":
    asyncio.run(demo_war_room())
