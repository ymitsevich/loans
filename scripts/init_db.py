"""Helper script to initialize the PostgreSQL schema."""

from __future__ import annotations

import asyncio

from loans.infrastructure.db import initialize_database


async def main() -> None:
    await initialize_database()


if __name__ == "__main__":
    asyncio.run(main())
