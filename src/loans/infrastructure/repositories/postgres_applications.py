"""PostgreSQL-backed repository for loan applications."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ...application.ports import LoanApplicationRepository
from ...domain import LoanApplication
from ..db.models import LoanApplicationModel


class PostgresLoanApplicationRepository(LoanApplicationRepository):
    """Persist loan applications using SQLAlchemy with PostgreSQL."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, application: LoanApplication) -> None:
        async with self._session_factory() as session:
            await self._merge_application(session, application, create_only=True)

    async def upsert(self, application: LoanApplication) -> None:
        async with self._session_factory() as session:
            await self._merge_application(session, application, create_only=False)

    async def get_latest(self, applicant_id: str) -> LoanApplication | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(LoanApplicationModel).where(LoanApplicationModel.applicant_id == applicant_id)
            )
            record = result.scalar_one_or_none()
            if record is None:
                return None
            return record.to_domain()

    @staticmethod
    async def _merge_application(
        session: AsyncSession,
        application: LoanApplication,
        *,
        create_only: bool,
    ) -> None:
        values = {
            "applicant_id": application.applicant_id,
            "amount": application.amount,
            "term_months": application.term_months,
            "status": application.status.value,
            "created_at": application.created_at,
            "updated_at": application.updated_at,
        }

        stmt = insert(LoanApplicationModel).values(**values)

        if create_only:
            stmt = stmt.on_conflict_do_nothing(index_elements=[LoanApplicationModel.applicant_id])
        else:
            stmt = stmt.on_conflict_do_update(
                index_elements=[LoanApplicationModel.applicant_id],
                set_={
                    "amount": application.amount,
                    "term_months": application.term_months,
                    "status": application.status.value,
                    "updated_at": application.updated_at,
                },
            )

        await session.execute(stmt)
        await session.commit()
