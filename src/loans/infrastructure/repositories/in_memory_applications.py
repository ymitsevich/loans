"""In-memory repository for loan applications."""

from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, List

from ...application.ports import LoanApplicationRepository
from ...domain import LoanApplication


class InMemoryLoanApplicationRepository(LoanApplicationRepository):
    """Dictionary-backed repository storing the latest application per applicant."""

    def __init__(self) -> None:
        self._items: DefaultDict[str, List[LoanApplication]] = defaultdict(list)

    async def create(self, application: LoanApplication) -> None:
        self._items[application.applicant_id].append(application)

    async def upsert(self, application: LoanApplication) -> None:
        history = self._items[application.applicant_id]
        if history:
            history[-1] = application
        else:
            history.append(application)

    async def get_latest(self, applicant_id: str) -> LoanApplication | None:
        history = self._items.get(applicant_id)
        if not history:
            return None
        return history[-1]
