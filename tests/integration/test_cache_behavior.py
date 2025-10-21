"""Integration tests for cache/database interaction in status retrieval."""

from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from loans.domain import ApplicationStatus, LoanApplication
from loans.interfaces.http.dependencies import AppContainer, cleanup_container, override_container, container as default_container
from loans.main import create_app


@pytest.mark.asyncio
async def test_get_application_status_prefers_cache() -> None:
    container = AppContainer(repository_backend="memory", cache_backend="memory", publisher_backend="memory")
    original_container = default_container
    override_container(container)
    app = create_app()

    application = LoanApplication(
        applicant_id="applicant-cache",
        amount=Decimal("1000"),
        term_months=12,
        status=ApplicationStatus.PENDING,
    )

    try:
        await container.application_repository.create(application)
        await container.status_cache.set("applicant-cache", ApplicationStatus.APPROVED, ttl_seconds=3600)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/application/applicant-cache")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == ApplicationStatus.APPROVED.value
    finally:
        await cleanup_container(container)
        override_container(original_container)


@pytest.mark.asyncio
async def test_get_application_status_falls_back_to_database() -> None:
    container = AppContainer(repository_backend="memory", cache_backend="memory", publisher_backend="memory")
    original_container = default_container
    override_container(container)
    app = create_app()

    application = LoanApplication(
        applicant_id="applicant-db",
        amount=Decimal("750"),
        term_months=6,
        status=ApplicationStatus.REJECTED,
    )

    try:
        await container.application_repository.create(application)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/application/applicant-db")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == ApplicationStatus.REJECTED.value
    finally:
        await cleanup_container(container)
        override_container(original_container)
