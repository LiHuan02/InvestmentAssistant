import asyncio
from typing import Any


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    def subscribe(self, topic: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(queue)
        return queue

    def unsubscribe(self, topic: str, queue: asyncio.Queue) -> None:
        if topic in self._subscribers:
            self._subscribers[topic] = [
                q for q in self._subscribers[topic] if q is not queue
            ]

    async def publish(self, topic: str, data: Any) -> None:
        if topic in self._subscribers:
            for queue in self._subscribers[topic]:
                await queue.put(data)


event_bus = EventBus()
