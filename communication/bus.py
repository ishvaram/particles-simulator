import asyncio
import time
from core.observer import get_logger

class Subscriber:
    __slots__ = ("name", "queue", "topics", "created_at", "received", "dropped")

    def __init__(self, name, queue, topics=None):
        self.name = name
        self.queue = queue
        self.topics = topics or set()
        self.created_at = time.time()
        self.received = 0
        self.dropped = 0

class EventBus:
    """Copy-on-write pub/sub. Publish path is lock-free."""

    def __init__(self, queue_size=50):
        self._lock = asyncio.Lock()
        self._subscribers = {}
        self._subscribers_snapshot = []
        self._queue_size = queue_size
        self._log = get_logger()
        self.total_published = 0
        self.total_delivered = 0
        self.total_dropped = 0

    async def subscribe(self, name, max_queue_size=None, topics=None):
        async with self._lock:
            if name in self._subscribers:
                return self._subscribers[name]
            subscriber = Subscriber(name, asyncio.Queue(maxsize=max_queue_size or self._queue_size),
                                   set(topics) if topics else set())
            self._subscribers[name] = subscriber
            self._subscribers_snapshot = list(self._subscribers.values())
            self._log.info(f"sub+ {name}")
            return subscriber

    async def unsubscribe(self, name):
        async with self._lock:
            if name not in self._subscribers:
                return False
            del self._subscribers[name]
            self._subscribers_snapshot = list(self._subscribers.values())
            self._log.info(f"sub- {name}")
            return True

    async def publish(self, item, topic=""):
        delivered = dropped = 0
        for subscriber in self._subscribers_snapshot:
            if subscriber.topics and topic not in subscriber.topics:
                continue
            try:
                subscriber.queue.put_nowait(item)
                subscriber.received += 1
                delivered += 1
            except asyncio.QueueFull:
                subscriber.dropped += 1
                dropped += 1
            except Exception:
                pass
        self.total_published += 1
        self.total_delivered += delivered
        self.total_dropped += dropped
        return delivered

    def get_stats(self):
        return {
            "subscriber_count": len(self._subscribers_snapshot),
            "total_published": self.total_published,
            "total_delivered": self.total_delivered,
            "total_dropped": self.total_dropped
        }

    async def get_subscriber_info(self):
        return [
            {   "name": subscriber.name,
                "queued": subscriber.queue.qsize(),
                "received": subscriber.received,
                "dropped": subscriber.dropped
            } for subscriber in self._subscribers_snapshot
        ]
