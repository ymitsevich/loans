"""Integration tests that require real PostgreSQL and Redis services."""

from __future__ import annotations

import os
from decimal import Decimal
from uuid import uuid4

import pytest

from loans.application import GetApplicationStatus, ProcessApplication, ProcessApplicationCommand
from loans.application.ports import ApplicationStatusCache, LoanApplicationRepository
from loans.interfaces.http.dependencies import AppContainer, cleanup_container
from sqlalchemy import text

from loans.infrastructure.db import initialize_database, get_engine


@pytest.mark.asyncio
async def test_process_application_with_real_services() -> None:
    container = AppContainer()
    await initialize_database()

    repository: LoanApplicationRepository = container.application_repository
    cache: ApplicationStatusCache = container.status_cache

    processor = ProcessApplication(repository=repository, cache=cache)
    applicant_id = f"applicant-real-{uuid4().hex[:8]}"

    command = ProcessApplicationCommand(
        applicant_id=applicant_id,
        amount=Decimal("2500"),
        term_months=12,
    )

    try:
        result = await processor.execute(command)
        assert result.status.value == "approved"

        status_use_case = GetApplicationStatus(repository=repository, cache=cache)
        view = await status_use_case.execute(applicant_id)
        assert view.status.value == "approved"
        assert view.applicant_id == applicant_id
        assert view.amount == float(command.amount)
        assert view.term_months == command.term_months
    finally:
        await cleanup_container(container)
        await _truncate_tables()


async def _truncate_tables() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE loan_applications"))
