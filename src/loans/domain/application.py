"""Domain models for loan application processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


class ApplicationStatus(str, Enum):
    """Possible states for a loan application."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(slots=True)
class LoanApplication:
    """Represents the lifecycle state of a loan application."""

    applicant_id: str
    amount: Decimal
    term_months: int
    status: ApplicationStatus = ApplicationStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def with_status(self, status: ApplicationStatus) -> "LoanApplication":
        """Return a copy with an updated status timestamped at mutation time."""
        return LoanApplication(
            applicant_id=self.applicant_id,
            amount=self.amount,
            term_months=self.term_months,
            status=status,
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc),
        )
