"""Use case executed by the Kafka consumer to validate and persist applications."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ...domain import ApplicationStatus, LoanApplication
from ..ports import ApplicationStatusCache, LoanApplicationRepository


class ApplicationValidationError(ValueError):
    """Raised when an application payload violates business rules."""


@dataclass(frozen=True)
class ProcessApplicationCommand:
    """Data consumed from Kafka for processing."""

    applicant_id: str
    amount: Decimal
    term_months: int


class ProcessApplication:
    """Validate, persist, and cache loan application decisions."""

    def __init__(
        self,
        repository: LoanApplicationRepository,
        cache: ApplicationStatusCache,
        approval_threshold: Decimal = Decimal("5000"),
        cache_ttl_seconds: int = 3600,
    ) -> None:
        self._repository = repository
        self._cache = cache
        self._approval_threshold = approval_threshold
        self._cache_ttl_seconds = cache_ttl_seconds

    async def execute(self, command: ProcessApplicationCommand) -> LoanApplication:
        self._validate(command)
        status = (
            ApplicationStatus.APPROVED
            if command.amount <= self._approval_threshold
            else ApplicationStatus.REJECTED
        )

        existing = await self._repository.get_latest(command.applicant_id)
        application = (
            existing.with_status(status)
            if existing
            else LoanApplication(
                applicant_id=command.applicant_id,
                amount=command.amount,
                term_months=command.term_months,
                status=status,
            )
        )

        await self._repository.upsert(application)
        await self._cache.set(command.applicant_id, status, ttl_seconds=self._cache_ttl_seconds)
        return application

    @staticmethod
    def _validate(command: ProcessApplicationCommand) -> None:
        if command.amount <= 0:
            raise ApplicationValidationError("Amount must be greater than zero.")
        if not 1 <= command.term_months <= 60:
            raise ApplicationValidationError("Term must be between 1 and 60 months.")
