"""
WebSocket endpoints for real-time communication
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Any, List
from datetime import datetime
import json
import logging
import sys

from app.api.routes.orchestrator_routes import manager
# from app.api.routes import orchestrator  # Avoid circular import

router = APIRouter()
logger = logging.getLogger(__name__)

# Get orchestrator reference from parent module to avoid circular imports
def get_orchestrator():
    """Get orchestrator instance from parent routes module"""
    try:
        routes_module = sys.modules.get('app.api.routes')
        if routes_module and hasattr(routes_module, 'orchestrator'):
            return routes_module.orchestrator
        return None
    except:
        return None


# The complex warroom WebSocket is now replaced by the simple agent_chat WebSocket
# This keeps backward compatibility but directs to the new system


# Background task to relay Redis messages to WebSocket clients
async def redis_to_websocket_relay():
    """Relay messages from Redis pub/sub to WebSocket clients"""
    if not orchestrator:
        logger.warning("Orchestrator not initialized, relay cannot start")
        return

    logger.info("🔄 Starting Redis → WebSocket relay")

    while True:
        try:
            # Get recent messages from agent network
            messages = await orchestrator.network.get_message_history(limit=5)

            for msg in messages:
                # Format message for frontend
                formatted_msg = {
                    "type": msg.get("type", "agent_message"),
                    "from": msg.get("from", "system"),
                    "to": msg.get("to", "all"),
                    "content": msg.get("message", ""),
                    "timestamp": msg.get("timestamp", datetime.now().isoformat()),
                    "data": msg.get("data", {})
                }

                # Broadcast to all WebSocket clients
                await manager.broadcast(formatted_msg)

            await asyncio.sleep(0.5)  # Poll every 500ms

        except Exception as e:
            logger.error(f"Error in relay: {e}")
            await asyncio.sleep(1)

# Export the router as websocket_router
websocket_router = router
