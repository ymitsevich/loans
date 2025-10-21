"""In-memory cache for application statuses."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple

from ...application.ports import ApplicationStatusCache
from ...domain import ApplicationStatus


class InMemoryStatusCache(ApplicationStatusCache):
    """Stores statuses with an expiration timestamp."""

    def __init__(self) -> None:
        self._store: Dict[str, Tuple[ApplicationStatus, datetime]] = {}

    async def set(self, applicant_id: str, status: ApplicationStatus, ttl_seconds: int) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        self._store[applicant_id] = (status, expires_at)

    async def get(self, applicant_id: str) -> ApplicationStatus | None:
        entry = self._store.get(applicant_id)
        if not entry:
            return None
        status, expires_at = entry
        if expires_at < datetime.now(timezone.utc):
            del self._store[applicant_id]
            return None
        return status
