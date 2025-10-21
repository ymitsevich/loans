"""Use case for retrieving the latest loan application status."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ...domain import ApplicationStatus, LoanApplication
from ..ports import ApplicationStatusCache, LoanApplicationRepository


class ApplicationNotFoundError(LookupError):
    """Raised when no loan application exists for the requested applicant."""


@dataclass(frozen=True)
class ApplicationStatusResult:
    """DTO returned by the use case."""

    applicant_id: str
    status: ApplicationStatus
    amount: float
    term_months: int
    updated_at: datetime


class GetApplicationStatus:
    """Query the cache and repository for the latest application status."""

    def __init__(
        self,
        repository: LoanApplicationRepository,
        cache: ApplicationStatusCache,
    ) -> None:
        self._repository = repository
        self._cache = cache

    async def execute(self, applicant_id: str) -> ApplicationStatusResult:
        cached_status = await self._cache.get(applicant_id)

        application: LoanApplication | None = await self._repository.get_latest(applicant_id)

        if application is None:
            raise ApplicationNotFoundError(f"No application found for applicant '{applicant_id}'.")

        status = cached_status or application.status

        return ApplicationStatusResult(
            applicant_id=application.applicant_id,
            status=status,
            amount=float(application.amount),
            term_months=application.term_months,
            updated_at=application.updated_at,
        )
