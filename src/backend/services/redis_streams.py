# backend/services/redis_streams.py
"""
Redis Streams implementation for event-driven agent communication.
Replaces polling-based pub/sub with true streaming architecture.
"""
import os
import json
import asyncio
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import redis.asyncio as aioredis


class RedisStreamsService:
    """
    Event-driven message streaming using Redis Streams.
    Provides guaranteed message ordering, consumer groups, and acknowledgments.
    """

    def __init__(self, redis_url: str = None):
        """
        Initialize Redis Streams service.

        Args:
            redis_url: Redis connection URL (default from env)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis: Optional[aioredis.Redis] = None
        self.consumers: Dict[str, asyncio.Task] = {}
        self.running = False

    async def connect(self):
        """Connect to Redis"""
        self.redis = await aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        self.running = True
        print("✅ Connected to Redis Streams")

    async def disconnect(self):
        """Disconnect from Redis"""
        self.running = False

        # Cancel all consumer tasks
        for task in self.consumers.values():
            task.cancel()

        if self.redis:
            await self.redis.close()
        print("✅ Disconnected from Redis Streams")

    async def publish_message(
        self,
        stream_name: str,
        message: Dict[str, Any],
        max_len: int = 10000
    ) -> str:
        """
        Publish message to a stream.

        Args:
            stream_name: Name of the stream
            message: Message data (will be JSON serialized)
            max_len: Maximum stream length (FIFO eviction)

        Returns:
            Message ID
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = datetime.utcnow().isoformat()

        # Serialize complex types
        serialized = self._serialize_message(message)

        # Publish to stream with max length
        message_id = await self.redis.xadd(
            stream_name,
            serialized,
            maxlen=max_len,
            approximate=True  # Use approximate trimming for performance
        )

        return message_id

    async def publish_agent_message(
        self,
        agent_name: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Publish an agent message to the war room stream.

        Args:
            agent_name: Name of the agent
            message_type: Type of message (analysis, decision, alert, etc.)
            content: Message content
            metadata: Optional additional metadata

        Returns:
            Message ID
        """
        message = {
            "agent": agent_name,
            "type": message_type,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        return await self.publish_message("warroom:messages", message)

    async def create_consumer_group(
        self,
        stream_name: str,
        group_name: str,
        start_id: str = "0"
    ):
        """
        Create a consumer group for a stream.

        Args:
            stream_name: Stream name
            group_name: Consumer group name
            start_id: Start reading from this ID ("0" = beginning, "$" = new messages)
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        try:
            await self.redis.xgroup_create(
                stream_name,
                group_name,
                id=start_id,
                mkstream=True  # Create stream if doesn't exist
            )
            print(f"✅ Created consumer group '{group_name}' for stream '{stream_name}'")
        except aioredis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                # Group already exists
                pass
            else:
                raise

    async def consume_stream(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        callback: Callable[[Dict], Any],
        block_ms: int = 1000,
        count: int = 10
    ):
        """
        Consume messages from a stream as part of a consumer group.

        Args:
            stream_name: Stream to consume
            group_name: Consumer group
            consumer_name: Unique consumer name
            callback: Async function to process each message
            block_ms: Block for this many ms waiting for messages
            count: Max messages to read per batch
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        print(f"🔄 Starting consumer '{consumer_name}' for stream '{stream_name}'")

        while self.running:
            try:
                # Read new messages
                messages = await self.redis.xreadgroup(
                    groupname=group_name,
                    consumername=consumer_name,
                    streams={stream_name: ">"},
                    count=count,
                    block=block_ms
                )

                # Process messages
                for stream, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        try:
                            # Deserialize message
                            deserialized = self._deserialize_message(message_data)

                            # Call callback
                            await callback(deserialized)

                            # Acknowledge message
                            await self.redis.xack(stream_name, group_name, message_id)

                        except Exception as e:
                            print(f"❌ Error processing message {message_id}: {e}")
                            # Message not acknowledged - will be redelivered

            except asyncio.CancelledError:
                print(f"⏹️  Consumer '{consumer_name}' cancelled")
                break
            except Exception as e:
                print(f"❌ Error in consumer '{consumer_name}': {e}")
                await asyncio.sleep(1)  # Back off on error

    def start_consumer(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        callback: Callable[[Dict], Any],
        block_ms: int = 1000,
        count: int = 10
    ) -> asyncio.Task:
        """
        Start a background consumer task.

        Args:
            stream_name: Stream to consume
            group_name: Consumer group
            consumer_name: Unique consumer name
            callback: Async function to process each message
            block_ms: Block time in ms
            count: Batch size

        Returns:
            Consumer task
        """
        consumer_key = f"{stream_name}:{group_name}:{consumer_name}"

        task = asyncio.create_task(
            self.consume_stream(
                stream_name,
                group_name,
                consumer_name,
                callback,
                block_ms,
                count
            )
        )

        self.consumers[consumer_key] = task
        return task

    async def get_pending_messages(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        count: int = 10
    ) -> List[Dict]:
        """
        Get pending messages that were not acknowledged.

        Args:
            stream_name: Stream name
            group_name: Consumer group
            consumer_name: Consumer name
            count: Max messages to retrieve

        Returns:
            List of pending messages
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        # Get pending message IDs
        pending_info = await self.redis.xpending_range(
            stream_name,
            group_name,
            min="-",
            max="+",
            count=count,
            consumername=consumer_name
        )

        if not pending_info:
            return []

        # Claim pending messages
        message_ids = [info['message_id'] for info in pending_info]
        messages = await self.redis.xclaim(
            stream_name,
            group_name,
            consumer_name,
            min_idle_time=5000,  # 5 seconds
            message_ids=message_ids
        )

        return [self._deserialize_message(msg[1]) for msg in messages]

    async def get_stream_info(self, stream_name: str) -> Dict:
        """Get information about a stream"""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        info = await self.redis.xinfo_stream(stream_name)
        return {
            "length": info['length'],
            "first_entry": info['first-entry'],
            "last_entry": info['last-entry'],
            "groups": info['groups'],
        }

    async def trim_stream(self, stream_name: str, max_len: int):
        """Trim stream to maximum length"""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        await self.redis.xtrim(stream_name, maxlen=max_len, approximate=True)

    def _serialize_message(self, message: Dict) -> Dict[str, str]:
        """Serialize message for Redis (all values must be strings)"""
        serialized = {}
        for key, value in message.items():
            if isinstance(value, (dict, list)):
                serialized[key] = json.dumps(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = str(value)
        return serialized

    def _deserialize_message(self, message: Dict[str, str]) -> Dict:
        """Deserialize message from Redis"""
        deserialized = {}
        for key, value in message.items():
            # Try to parse as JSON
            try:
                deserialized[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Keep as string
                deserialized[key] = value
        return deserialized


# Global instance
redis_streams = RedisStreamsService()


# Convenience functions for agent network
async def publish_agent_message(agent_name: str, content: str, message_type: str = "analysis"):
    """Publish agent message to war room"""
    return await redis_streams.publish_agent_message(agent_name, message_type, content)


async def publish_user_input(content: str, user_id: str = None):
    """Publish user input to agent network"""
    return await redis_streams.publish_message("warroom:user_input", {
        "type": "user_input",
        "content": content,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    })


async def publish_trade_decision(trade_data: Dict):
    """Publish trade decision to execution stream"""
    return await redis_streams.publish_message("trades:decisions", trade_data)
