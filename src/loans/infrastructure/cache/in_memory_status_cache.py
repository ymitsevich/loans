"""In-memory cache for application statuses."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple

from ...application.ports import ApplicationStatusCache
from ...domain import LoanApplication


class InMemoryStatusCache(ApplicationStatusCache):
    """Stores statuses with an expiration timestamp."""

    def __init__(self) -> None:
        self._store: Dict[str, Tuple[LoanApplication, datetime]] = {}

    async def set(self, application: LoanApplication, ttl_seconds: int) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        self._store[application.applicant_id] = (application, expires_at)

    async def get(self, applicant_id: str) -> LoanApplication | None:
        entry = self._store.get(applicant_id)
        if not entry:
            return None
        application, expires_at = entry
        if expires_at < datetime.now(timezone.utc):
            del self._store[applicant_id]
            return None
        return application
