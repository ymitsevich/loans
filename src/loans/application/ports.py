"""Application layer boundary abstractions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from ..domain import LoanApplication


@dataclass(frozen=True)
class ApplicationMessage:
    """Payload emitted to Kafka for downstream processing."""

    applicant_id: str
    amount: Decimal
    term_months: int


class LoanApplicationRepository(Protocol):
    """Persistence gateway for loan applications."""

    async def create(self, application: LoanApplication) -> None:
        ...

    async def upsert(self, application: LoanApplication) -> None:
        ...

    async def get_latest(self, applicant_id: str) -> LoanApplication | None:
        ...


class ApplicationStatusCache(Protocol):
    """Cache for storing the most recent loan application snapshot."""

    async def set(self, application: LoanApplication, ttl_seconds: int) -> None:
        ...

    async def get(self, applicant_id: str) -> LoanApplication | None:
        ...


class ApplicationEventPublisher(Protocol):
    """Message bus used to publish application submissions."""

    async def publish(self, topic: str, message: ApplicationMessage) -> None:
        ...
