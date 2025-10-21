"""Dependency providers for FastAPI routes."""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Literal

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ...application import (
    GetApplicationStatus,
    ProcessApplication,
    SubmitApplication,
)
from ...application.ports import (
    ApplicationEventPublisher,
    ApplicationStatusCache,
    LoanApplicationRepository,
)
from ...infrastructure import (
    InMemoryApplicationEventPublisher,
    InMemoryLoanApplicationRepository,
    InMemoryStatusCache,
    PostgresLoanApplicationRepository,
)
from ...infrastructure.cache import RedisStatusCache, create_redis_client
from ...infrastructure.db import create_session_factory, dispose_engine
from ...infrastructure.messaging import KafkaApplicationEventPublisher, build_producer

RepositoryBackend = Literal["postgres", "memory"]
CacheBackend = Literal["redis", "memory"]
PublisherBackend = Literal["kafka", "memory"]


class AppContainer:
    """Basic service container for dependency resolution."""

    def __init__(
        self,
        *,
        repository_backend: RepositoryBackend | None = None,
        cache_backend: CacheBackend | None = None,
        publisher_backend: PublisherBackend | None = None,
    ) -> None:
        if repository_backend is None:
            backend_env = os.getenv("REPOSITORY_BACKEND", "postgres").lower()
            repository_backend = "memory" if backend_env == "memory" else "postgres"

        if cache_backend is None:
            cache_env = os.getenv("CACHE_BACKEND", "redis").lower()
            cache_backend = "memory" if cache_env == "memory" else "redis"

        if publisher_backend is None:
            publisher_env = os.getenv("PUBLISHER_BACKEND", "kafka").lower()
            publisher_backend = "memory" if publisher_env == "memory" else "kafka"

        self.repository_backend: RepositoryBackend = repository_backend
        self.cache_backend: CacheBackend = cache_backend
        self.publisher_backend: PublisherBackend = publisher_backend

        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self.status_cache: ApplicationStatusCache
        self.event_publisher: ApplicationEventPublisher
        self._redis_client = None
        self._kafka_publisher: KafkaApplicationEventPublisher | None = None

        if self.repository_backend == "postgres":
            self.session_factory = create_session_factory()
            self.application_repository: LoanApplicationRepository = PostgresLoanApplicationRepository(
                self.session_factory
            )
        else:
            self.application_repository = InMemoryLoanApplicationRepository()

        if self.cache_backend == "redis":
            redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
            self._redis_client = create_redis_client(redis_url)
            self.status_cache = RedisStatusCache(self._redis_client)
        else:
            self.status_cache = InMemoryStatusCache()

        if self.publisher_backend == "kafka":
            bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
            client_id = os.getenv("SERVICE_NAME", "loans-api")
            self._kafka_publisher = KafkaApplicationEventPublisher(
                lambda: build_producer(bootstrap_servers, client_id)
            )
            self.event_publisher = self._kafka_publisher
        else:
            self.event_publisher = InMemoryApplicationEventPublisher()

        self.kafka_topic = os.getenv("KAFKA_APPLICATION_TOPIC", "loan-applications")
        self.approval_threshold = Decimal("5000")
        self.cache_ttl_seconds = 3600


container = AppContainer()


def override_container(new_container: AppContainer) -> None:
    """Allow tests to swap out dependencies with controlled fixtures."""
    global container
    container = new_container


def is_using_postgres_repository() -> bool:
    return container.repository_backend == "postgres"


def get_application_repository() -> LoanApplicationRepository:
    return container.application_repository


def get_status_cache() -> ApplicationStatusCache:
    return container.status_cache


def get_event_publisher() -> ApplicationEventPublisher:
    return container.event_publisher


async def shutdown_container() -> None:
    await cleanup_container(container)


def get_submit_application_use_case(
    repository: LoanApplicationRepository = Depends(get_application_repository),
    publisher: ApplicationEventPublisher = Depends(get_event_publisher),
) -> SubmitApplication:
    return SubmitApplication(repository=repository, publisher=publisher, topic=container.kafka_topic)


def get_process_application_use_case(
    repository: LoanApplicationRepository = Depends(get_application_repository),
    cache: ApplicationStatusCache = Depends(get_status_cache),
) -> ProcessApplication:
    return ProcessApplication(
        repository=repository,
        cache=cache,
        approval_threshold=container.approval_threshold,
        cache_ttl_seconds=container.cache_ttl_seconds,
    )


def get_application_status_use_case(
    repository: LoanApplicationRepository = Depends(get_application_repository),
    cache: ApplicationStatusCache = Depends(get_status_cache),
) -> GetApplicationStatus:
    return GetApplicationStatus(repository=repository, cache=cache)


async def cleanup_container(instance: AppContainer) -> None:
    status_cache = instance.status_cache
    event_publisher = instance.event_publisher

    if isinstance(status_cache, RedisStatusCache):
        await status_cache.close()
    if isinstance(event_publisher, KafkaApplicationEventPublisher):
        await event_publisher.close()
    if instance.repository_backend == "postgres":
        await dispose_engine()
