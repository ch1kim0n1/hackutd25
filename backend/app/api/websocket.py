"""
WebSocket endpoints for real-time communication
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Any, List
from datetime import datetime
import json
import logging

from app.api.routes.orchestrator_routes import manager
from app.api.routes import orchestrator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/warroom")
async def warroom_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time War Room updates"""
    await manager.connect(websocket)

    try:
        # Send welcome message
        await manager.send_personal(websocket, {
            "type": "system",
            "from": "system",
            "to": "user",
            "content": "Connected to APEX War Room",
            "timestamp": datetime.now().isoformat()
        })

        # Send recent message history
        if orchestrator:
            recent_messages = await orchestrator.network.get_message_history(limit=20)

            for msg in recent_messages:
                await manager.send_personal(websocket, {
                    "type": msg.get("type", "agent_message"),
                    "from": msg.get("from", "system"),
                    "to": msg.get("to", "all"),
                    "content": msg.get("message", ""),
                    "timestamp": msg.get("timestamp", datetime.now().isoformat()),
                    "data": msg.get("data", {})
                })

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle user messages from War Room
            if message.get("type") == "user_message":
                # Publish to agent network
                if orchestrator:
                    await orchestrator.network.publish(
                        topic="user_input",
                        message={
                            "type": "user_input",
                            "action": "comment",
                            "message": message.get("content", ""),
                            "timestamp": datetime.now().isoformat()
                        }
                    )

                # Broadcast to all clients
                await manager.broadcast({
                    "type": "user_input",
                    "from": "user",
                    "to": "all",
                    "content": message.get("content", ""),
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from War Room")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


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
