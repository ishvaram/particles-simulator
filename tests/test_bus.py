"""Unit tests for EventBus."""

import asyncio
import pytest
from communication.bus import EventBus


class TestEventBus:
    """Tests for EventBus class."""

    @pytest.mark.asyncio
    async def test_bus_creation(self):
        """EventBus initializes with default queue size."""
        bus = EventBus(queue_size=10)
        assert bus._queue_size == 10
        assert len(bus._subscribers) == 0

    @pytest.mark.asyncio
    async def test_subscribe(self):
        """Subscriber is added to bus."""
        bus = EventBus(queue_size=10)
        sub = await bus.subscribe("test-client")
        assert "test-client" in bus._subscribers
        assert sub.name == "test-client"

    @pytest.mark.asyncio
    async def test_subscribe_custom_queue_size(self):
        """Subscriber can have custom queue size."""
        bus = EventBus(queue_size=10)
        sub = await bus.subscribe("test-client", max_queue_size=50)
        assert sub.queue.maxsize == 50

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """Subscriber is removed from bus."""
        bus = EventBus(queue_size=10)
        await bus.subscribe("test-client")
        await bus.unsubscribe("test-client")
        assert "test-client" not in bus._subscribers

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent(self):
        """Unsubscribing nonexistent client doesn't raise."""
        bus = EventBus(queue_size=10)
        await bus.unsubscribe("nonexistent")  # Should not raise

    @pytest.mark.asyncio
    async def test_publish_to_subscriber(self):
        """Message is delivered to subscriber."""
        bus = EventBus(queue_size=10)
        sub = await bus.subscribe("test-client")
        
        await bus.publish({"type": "test", "value": 42})
        
        msg = await asyncio.wait_for(sub.queue.get(), timeout=1.0)
        assert msg["type"] == "test"
        assert msg["value"] == 42

    @pytest.mark.asyncio
    async def test_publish_to_multiple_subscribers(self):
        """Message is delivered to all subscribers."""
        bus = EventBus(queue_size=10)
        sub1 = await bus.subscribe("client-1")
        sub2 = await bus.subscribe("client-2")
        
        await bus.publish({"type": "broadcast"})
        
        msg1 = await asyncio.wait_for(sub1.queue.get(), timeout=1.0)
        msg2 = await asyncio.wait_for(sub2.queue.get(), timeout=1.0)
        assert msg1["type"] == "broadcast"
        assert msg2["type"] == "broadcast"

    @pytest.mark.asyncio
    async def test_publish_returns_delivery_count(self):
        """Publish returns number of successful deliveries."""
        bus = EventBus(queue_size=10)
        await bus.subscribe("client-1")
        await bus.subscribe("client-2")
        
        count = await bus.publish({"type": "test"})
        assert count == 2

    @pytest.mark.asyncio
    async def test_queue_overflow_drops_message(self):
        """Full queue drops new messages."""
        bus = EventBus(queue_size=2)
        sub = await bus.subscribe("slow-client", max_queue_size=2)
        
        # Fill the queue
        await bus.publish({"msg": 1})
        await bus.publish({"msg": 2})
        
        # This should be dropped
        await bus.publish({"msg": 3})
        
        assert sub.dropped >= 1

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Bus returns statistics."""
        bus = EventBus(queue_size=10)
        await bus.subscribe("client-1")
        await bus.publish({"type": "test"})
        
        stats = bus.get_stats()
        assert "subscriber_count" in stats
        assert stats["subscriber_count"] == 1
        assert "total_published" in stats

    @pytest.mark.asyncio
    async def test_get_subscriber_info(self):
        """Bus returns subscriber details."""
        bus = EventBus(queue_size=10)
        sub = await bus.subscribe("client-1")
        await bus.publish({"type": "test"})
        
        # Consume the message
        await sub.queue.get()
        
        info = await bus.get_subscriber_info()
        assert len(info) == 1
        assert info[0]["name"] == "client-1"
        assert "received" in info[0]
        assert "dropped" in info[0]
