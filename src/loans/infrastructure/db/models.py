"""ORM models mapping domain entities to the database."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from ...domain import ApplicationStatus, LoanApplication
from .session import Base


class LoanApplicationModel(Base):
    """SQLAlchemy representation of a loan application.

    The service currently assumes a single active application per applicant;
    ``applicant_id`` is the primary key and subsequent submissions overwrite
    prior state.
    """

    __tablename__ = "loan_applications"

    applicant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    term_months: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ApplicationStatus.PENDING.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_loan_applications_amount_positive"),
        CheckConstraint("term_months > 0", name="ck_loan_applications_term_positive"),
    )

    @classmethod
    def from_domain(cls, application: LoanApplication) -> "LoanApplicationModel":
        """Create a model instance from the domain entity."""
        return cls(
            applicant_id=application.applicant_id,
            amount=application.amount,
            term_months=application.term_months,
            status=application.status.value,
            created_at=application.created_at,
            updated_at=application.updated_at,
        )

    def to_domain(self) -> LoanApplication:
        """Convert the persisted model back into a domain entity."""
        return LoanApplication(
            applicant_id=self.applicant_id,
            amount=self.amount,
            term_months=self.term_months,
            status=ApplicationStatus(self.status),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
