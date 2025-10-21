"""Redis-backed cache for application statuses."""

from __future__ import annotations

import logging
from typing import Final

from redis.asyncio import Redis, from_url

from ...application.ports import ApplicationStatusCache
from ...domain import ApplicationStatus

LOGGER: Final = logging.getLogger(__name__)


def create_redis_client(url: str) -> Redis:
    """Factory to build a Redis client from the connection URL."""
    return from_url(url, decode_responses=True)


class RedisStatusCache(ApplicationStatusCache):
    """Persistence-backed cache using Redis."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def set(self, applicant_id: str, status: ApplicationStatus, ttl_seconds: int) -> None:
        await self._client.set(applicant_id, status.value, ex=ttl_seconds)

    async def get(self, applicant_id: str) -> ApplicationStatus | None:
        value = await self._client.get(applicant_id)
        if value is None:
            return None
        try:
            return ApplicationStatus(value)
        except ValueError:
            LOGGER.warning("Unknown status '%s' cached for applicant %s", value, applicant_id)
            return None

    async def close(self) -> None:
        try:
            await self._client.aclose()
        except Exception:  # pragma: no cover - defensive
            LOGGER.exception("Failed closing Redis client")
