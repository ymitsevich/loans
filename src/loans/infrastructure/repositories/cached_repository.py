"""Decorator that adds caching to a loan application repository."""

from __future__ import annotations

from ...application.ports import ApplicationStatusCache, LoanApplicationRepository
from ...domain import LoanApplication


class CachedLoanApplicationRepository(LoanApplicationRepository):
    """Repository decorator that caches loan applications after reads/writes."""

    def __init__(
        self,
        backing: LoanApplicationRepository,
        cache: ApplicationStatusCache,
        cache_ttl_seconds: int,
    ) -> None:
        self._backing = backing
        self._cache = cache
        self._cache_ttl_seconds = cache_ttl_seconds

    async def create(self, application: LoanApplication) -> None:
        await self._backing.create(application)
        await self._cache.set(application, ttl_seconds=self._cache_ttl_seconds)

    async def upsert(self, application: LoanApplication) -> None:
        await self._backing.upsert(application)
        await self._cache.set(application, ttl_seconds=self._cache_ttl_seconds)

    async def get_latest(self, applicant_id: str) -> LoanApplication | None:
        cached = await self._cache.get(applicant_id)
        if cached:
            return cached
        record = await self._backing.get_latest(applicant_id)
        if record:
            await self._cache.set(record, ttl_seconds=self._cache_ttl_seconds)
        return record
