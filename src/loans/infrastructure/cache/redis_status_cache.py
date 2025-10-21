"""Redis-backed cache for application statuses."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Final

from redis.asyncio import Redis, from_url

from ...application.ports import ApplicationStatusCache
from ...domain import ApplicationStatus, LoanApplication

LOGGER: Final = logging.getLogger(__name__)


def create_redis_client(url: str) -> Redis:
    """Factory to build a Redis client from the connection URL."""
    return from_url(url, decode_responses=True)


class RedisStatusCache(ApplicationStatusCache):
    """Persistence-backed cache using Redis."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def set(self, application: LoanApplication, ttl_seconds: int) -> None:
        payload = _serialize(application)
        await self._client.set(application.applicant_id, payload, ex=ttl_seconds)

    async def get(self, applicant_id: str) -> LoanApplication | None:
        payload = await self._client.get(applicant_id)
        if payload is None:
            return None
        try:
            return _deserialize(payload)
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.warning("Failed to deserialize cached application for %s: %s", applicant_id, exc)
            return None

    async def close(self) -> None:
        try:
            await self._client.aclose()
        except Exception:  # pragma: no cover - defensive
            LOGGER.exception("Failed closing Redis client")


def _serialize(application: LoanApplication) -> str:
    return json.dumps(
        {
            "applicant_id": application.applicant_id,
            "amount": str(application.amount),
            "term_months": application.term_months,
            "status": application.status.value,
            "created_at": application.created_at.isoformat(),
            "updated_at": application.updated_at.isoformat(),
        }
    )


def _deserialize(payload: str) -> LoanApplication:
    data = json.loads(payload)
    return LoanApplication(
        applicant_id=data["applicant_id"],
        amount=Decimal(data["amount"]),
        term_months=int(data["term_months"]),
        status=ApplicationStatus(data["status"]),
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
    )
