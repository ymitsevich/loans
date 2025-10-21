"""Use case responsible for submitting loan applications."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ...domain import LoanApplication
from ..ports import ApplicationEventPublisher, ApplicationMessage, LoanApplicationRepository


@dataclass(frozen=True)
class SubmitApplicationCommand:
    """Data required to submit a loan application."""

    applicant_id: str
    amount: Decimal
    term_months: int


class SubmitApplication:
    """Persist pending application and publish an event for async processing."""

    def __init__(
        self,
        repository: LoanApplicationRepository,
        publisher: ApplicationEventPublisher,
        topic: str,
    ) -> None:
        self._repository = repository
        self._publisher = publisher
        self._topic = topic

    async def execute(self, command: SubmitApplicationCommand) -> LoanApplication:
        application = LoanApplication(
            applicant_id=command.applicant_id,
            amount=command.amount,
            term_months=command.term_months,
        )

        await self._repository.create(application)
        await self._publisher.publish(
            topic=self._topic,
            message=ApplicationMessage(
                applicant_id=command.applicant_id,
                amount=command.amount,
                term_months=command.term_months,
            ),
        )
        return application
