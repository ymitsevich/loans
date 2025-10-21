"""In-memory event publisher used for tests and local development."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import DefaultDict, Deque, List

from ...application.ports import ApplicationEventPublisher, ApplicationMessage


class InMemoryApplicationEventPublisher(ApplicationEventPublisher):
    """Captures published messages grouped by topic."""

    def __init__(self) -> None:
        self._messages: DefaultDict[str, Deque[ApplicationMessage]] = defaultdict(deque)

    async def publish(self, topic: str, message: ApplicationMessage) -> None:
        self._messages[topic].append(message)

    def get_messages(self, topic: str) -> List[ApplicationMessage]:
        return list(self._messages.get(topic, []))

    def pop_latest(self, topic: str) -> ApplicationMessage | None:
        messages = self._messages.get(topic)
        if not messages:
            return None
        return messages.popleft()
