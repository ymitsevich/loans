"""Background processor that validates loan applications from Kafka."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from decimal import Decimal

from aiokafka import AIOKafkaConsumer
from prometheus_client import Counter, Histogram, start_http_server

from loans.application import ProcessApplication, ProcessApplicationCommand
from loans.interfaces.http.dependencies import AppContainer, cleanup_container
from loans.utils.logging import configure_logging

LOGGER = logging.getLogger("loans.application_processor")

APPLICATIONS_PROCESSED = Counter(
    "loan_applications_processed_total",
    "Number of loan application messages processed",
    labelnames=("status",),
)
PROCESSING_FAILURES = Counter(
    "loan_application_processing_failures_total",
    "Number of loan application messages that failed to process",
)
PROCESSING_DURATION = Histogram(
    "loan_application_processing_seconds",
    "Time spent processing loan application messages",
)


async def main() -> None:
    configure_logging()

    metrics_port = int(os.getenv("PROCESSOR_METRICS_PORT", "9000"))
    start_http_server(metrics_port)
    LOGGER.info("processor_metrics_started", extra={"extra_data": {"port": metrics_port}})

    container = AppContainer(publisher_backend="memory")

    process_application = ProcessApplication(
        repository=container.application_repository,
        cache=container.status_cache,
        cache_ttl_seconds=container.cache_ttl_seconds,
    )

    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    topic = os.getenv("KAFKA_APPLICATION_TOPIC", "loan-applications")
    consumer_group = os.getenv("KAFKA_CONSUMER_GROUP", "loans-consumer")

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=consumer_group,
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    LOGGER.info(
        "processor_started",
        extra={
            "extra_data": {
                "topic": topic,
                "bootstrap_servers": bootstrap_servers,
                "consumer_group": consumer_group,
            }
        },
    )
    await consumer.start()
    try:
        async for record in consumer:
            await _handle_record(process_application, record.value)
    finally:
        await consumer.stop()
        await cleanup_container(container)


async def _handle_record(
    process_application: ProcessApplication,
    payload: dict[str, object],
) -> None:
    try:
        command = ProcessApplicationCommand(
            applicant_id=str(payload["applicant_id"]),
            amount=Decimal(str(payload["amount"])),
            term_months=int(payload["term_months"]),
        )
        with PROCESSING_DURATION.time():
            result = await process_application.execute(command)
        APPLICATIONS_PROCESSED.labels(status=result.status.value).inc()
        LOGGER.info(
            "application_processed",
            extra={
                "extra_data": {
                    "applicant_id": result.applicant_id,
                    "status": result.status.value,
                    "amount": float(result.amount),
                    "term_months": result.term_months,
                }
            },
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        PROCESSING_FAILURES.inc()
        LOGGER.exception("application_processing_failed", extra={"extra_data": payload})


if __name__ == "__main__":
    asyncio.run(main())
