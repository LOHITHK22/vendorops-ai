from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ValidationErrorResponse
from app.db.repositories import list_validation_errors, list_validation_errors_for_record
from app.db.session import get_db_session

router = APIRouter(prefix="/validation-errors", tags=["validation"])


def to_validation_error_response(validation_error) -> ValidationErrorResponse:
    return ValidationErrorResponse(
        validation_error_id=UUID(validation_error.id),
        record_id=UUID(validation_error.record_id) if validation_error.record_id else None,
        job_id=UUID(validation_error.job_id) if validation_error.job_id else None,
        field_name=validation_error.field_name,
        error_type=validation_error.error_type,
        message=validation_error.message,
        severity=validation_error.severity,
        created_at=validation_error.created_at,
    )


@router.get("", response_model=list[ValidationErrorResponse])
async def get_validation_errors(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ValidationErrorResponse]:
    validation_errors = await list_validation_errors(session)
    return [to_validation_error_response(error) for error in validation_errors]


@router.get("/records/{record_id}", response_model=list[ValidationErrorResponse])
async def get_record_validation_errors(
    record_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ValidationErrorResponse]:
    validation_errors = await list_validation_errors_for_record(session, record_id)
    return [to_validation_error_response(error) for error in validation_errors]
