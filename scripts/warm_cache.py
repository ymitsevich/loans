"""Warm Redis cache with the latest application statuses from PostgreSQL."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from sqlalchemy import select

from loans.interfaces.http.dependencies import AppContainer, cleanup_container
from loans.infrastructure.db.models import LoanApplicationModel


LOGGER = logging.getLogger("loans.cache_warmup")


async def warm_cache() -> None:
    container = AppContainer()

    if container.repository_backend != "postgres":
        LOGGER.info("cache_warmup_skipped", extra={"extra_data": {"reason": "repository_not_postgres"}})
        await cleanup_container(container)
        return

    if container.cache_backend != "redis":
        LOGGER.info("cache_warmup_skipped", extra={"extra_data": {"reason": "cache_not_redis"}})
        await cleanup_container(container)
        return

    session_factory = container.session_factory
    if session_factory is None:
        LOGGER.warning("cache_warmup_no_session_factory")
        await cleanup_container(container)
        return

    count = 0
    async with session_factory() as session:
        result = await session.execute(select(LoanApplicationModel))
        for record in result.scalars():
            application = record.to_domain()
            await container.status_cache.set(
                applicant_id=application.applicant_id,
                status=application.status,
                ttl_seconds=container.cache_ttl_seconds,
            )
            count += 1

    LOGGER.info("cache_warmup_complete", extra={"extra_data": {"records": count}})
    await cleanup_container(container)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(warm_cache())
