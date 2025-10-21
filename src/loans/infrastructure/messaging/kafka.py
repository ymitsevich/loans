"""Kafka-backed publisher for loan application events."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Final, Mapping

from aiokafka import AIOKafkaProducer

from ...application.ports import ApplicationEventPublisher, ApplicationMessage

LOGGER: Final = logging.getLogger(__name__)


def build_producer(bootstrap_servers: str, client_id: str | None = None) -> AIOKafkaProducer:
    """Create an AIOKafkaProducer with JSON serialization."""
    return AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers,
        client_id=client_id,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


class KafkaApplicationEventPublisher(ApplicationEventPublisher):
    """Publish application messages to Kafka."""

    def __init__(self, producer_factory: callable[[], AIOKafkaProducer]) -> None:
        self._producer_factory = producer_factory
        self._producer: AIOKafkaProducer | None = None
        self._lock = asyncio.Lock()

    async def _ensure_producer(self) -> AIOKafkaProducer:
        if self._producer is not None:
            return self._producer

        async with self._lock:
            if self._producer is None:
                producer = self._producer_factory()
                await producer.start()
                self._producer = producer
        assert self._producer is not None  # for type-checkers
        return self._producer

    async def publish(self, topic: str, message: ApplicationMessage) -> None:
        producer = await self._ensure_producer()
        payload = _message_to_mapping(message)
        await producer.send_and_wait(topic, payload)

    async def close(self) -> None:
        if self._producer is None:
            return
        try:
            await self._producer.stop()
        except Exception:  # pragma: no cover - defensive
            LOGGER.exception("Failed stopping Kafka producer")
        finally:
            self._producer = None


def _message_to_mapping(message: ApplicationMessage) -> Mapping[str, Any]:
    return {
        "applicant_id": message.applicant_id,
        "amount": str(message.amount),
        "term_months": message.term_months,
    }
