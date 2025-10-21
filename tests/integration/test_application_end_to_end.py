"""End-to-end test covering submission and processing of loan applications."""

from __future__ import annotations

from decimal import Decimal
from typing import cast

import pytest
from httpx import ASGITransport, AsyncClient

from loans.application import (
    ApplicationStatusResult,
    GetApplicationStatus,
    ProcessApplication,
    ProcessApplicationCommand,
)
from loans.domain import ApplicationStatus
from loans.interfaces.http.dependencies import AppContainer, override_container, container as default_container
from loans.main import create_app
from loans.infrastructure.messaging import InMemoryApplicationEventPublisher


@pytest.mark.asyncio
async def test_submit_application_flow() -> None:
    container = AppContainer(
        repository_backend="memory",
        cache_backend="memory",
        publisher_backend="memory",
    )
    original_container = default_container
    override_container(container)
    app = create_app()

    payload = {
        "applicant_id": "applicant-123",
        "amount": "4500.00",
        "term_months": 24,
    }

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/application", json=payload)
            assert response.status_code == 202
            assert response.json() == {"applicant_id": payload["applicant_id"], "status": "pending"}

            latest = await container.application_repository.get_latest(payload["applicant_id"])
            assert latest is not None
            assert latest.status == ApplicationStatus.PENDING

            publisher = cast(InMemoryApplicationEventPublisher, container.event_publisher)
            event = publisher.pop_latest(container.kafka_topic)
            assert event is not None
            assert event.applicant_id == payload["applicant_id"]
            assert event.amount == Decimal(payload["amount"])

            processor = ProcessApplication(
                repository=container.application_repository,
                cache=container.status_cache,
                approval_threshold=Decimal("5000"),
            )
            processed = await processor.execute(
                ProcessApplicationCommand(
                    applicant_id=event.applicant_id,
                    amount=event.amount,
                    term_months=event.term_months,
                )
            )
            assert processed.status == ApplicationStatus.APPROVED

            cached_application = await container.status_cache.get(payload["applicant_id"])
            assert cached_application is not None
            assert cached_application.status == ApplicationStatus.APPROVED

            status_use_case = GetApplicationStatus(
                repository=container.application_repository,
            )
            result: ApplicationStatusResult = await status_use_case.execute(payload["applicant_id"])
            assert result.status == ApplicationStatus.APPROVED
            assert result.amount == event.amount

            status_response = await client.get(f"/application/{payload['applicant_id']}")
            assert status_response.status_code == 200
            body = status_response.json()
            assert body["status"] == ApplicationStatus.APPROVED.value
            assert body["applicant_id"] == payload["applicant_id"]
            assert Decimal(body["amount"]) == event.amount
    finally:
        override_container(original_container)
