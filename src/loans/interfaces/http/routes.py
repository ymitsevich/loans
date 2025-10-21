"""Route registrations for the FastAPI application."""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from ...application import (
    ApplicationNotFoundError,
    ApplicationStatusResult,
    GetApplicationStatus,
    SubmitApplication,
    SubmitApplicationCommand,
)
from ..http.dependencies import get_application_status_use_case, get_submit_application_use_case

LOGGER = logging.getLogger("loans.api.routes")

loans_router = APIRouter(prefix="/loans", tags=["loans"])
applications_router = APIRouter(prefix="/application", tags=["applications"])


class SubmitApplicationRequest(BaseModel):
    """Request body for POST /application."""

    applicant_id: str = Field(..., description="Unique applicant identifier")
    amount: Decimal = Field(..., gt=Decimal("0"), description="Requested loan amount")
    term_months: int = Field(..., ge=1, le=60, description="Repayment term in months")


class SubmitApplicationResponse(BaseModel):
    """Response for a submitted loan application."""

    applicant_id: str
    status: str = Field(default="pending")


class ApplicationStatusResponse(BaseModel):
    """Response model returned by GET /application/{applicant_id}."""

    applicant_id: str
    status: str
    amount: Decimal
    term_months: int
    updated_at: datetime


@applications_router.post("", response_model=SubmitApplicationResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_application(
    payload: SubmitApplicationRequest,
    use_case: SubmitApplication = Depends(get_submit_application_use_case),
) -> SubmitApplicationResponse:
    await use_case.execute(
        SubmitApplicationCommand(
            applicant_id=payload.applicant_id,
            amount=payload.amount,
            term_months=payload.term_months,
        )
    )
    LOGGER.info(
        "application_submitted",
        extra={
            "extra_data": {
                "applicant_id": payload.applicant_id,
                "amount": str(payload.amount),
                "term_months": payload.term_months,
            }
        },
    )
    return SubmitApplicationResponse(applicant_id=payload.applicant_id)


@applications_router.get(
    "/{applicant_id}",
    response_model=ApplicationStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_application_status(
    applicant_id: str,
    use_case: GetApplicationStatus = Depends(get_application_status_use_case),
) -> ApplicationStatusResponse:
    try:
        result: ApplicationStatusResult = await use_case.execute(applicant_id)
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    response = ApplicationStatusResponse(
        applicant_id=result.applicant_id,
        status=result.status.value,
        amount=result.amount,
        term_months=result.term_months,
        updated_at=result.updated_at,
    )
    LOGGER.info(
        "application_status_fetched",
        extra={
                "extra_data": {
                    "applicant_id": response.applicant_id,
                    "status": response.status,
                    "amount": str(response.amount),
                    "term_months": response.term_months,
                }
        },
    )
    return response


@loans_router.get("/health", status_code=status.HTTP_200_OK)
async def healthcheck() -> dict[str, str]:
    """Lightweight readiness indicator used for container health checks."""
    return {"status": "ok"}


def register_routes(app: FastAPI) -> None:
    """Attach routers to the FastAPI application."""
    app.include_router(loans_router)
    app.include_router(applications_router)
