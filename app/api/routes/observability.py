from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import AuditLogResponse, ExtractionErrorResponse
from app.db.models import AuditLog, ExtractionErrorLog
from app.db.repositories import list_audit_logs, list_extraction_errors
from app.db.session import get_db_session

router = APIRouter(tags=["observability"])


def to_audit_log_response(audit_log: AuditLog) -> AuditLogResponse:
    return AuditLogResponse(
        audit_log_id=UUID(audit_log.id),
        actor=audit_log.actor,
        action=audit_log.action,
        entity_type=audit_log.entity_type,
        entity_id=audit_log.entity_id,
        details=audit_log.details,
        created_at=audit_log.created_at,
    )


def to_extraction_error_response(error_log: ExtractionErrorLog) -> ExtractionErrorResponse:
    return ExtractionErrorResponse(
        error_id=UUID(error_log.id),
        job_id=UUID(error_log.job_id) if error_log.job_id else None,
        file_id=UUID(error_log.file_id) if error_log.file_id else None,
        stage=error_log.stage,
        error_type=error_log.error_type,
        message=error_log.message,
        retryable=error_log.retryable,
        attempt=error_log.attempt,
        details=error_log.details,
        created_at=error_log.created_at,
    )


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[AuditLogResponse]:
    audit_logs = await list_audit_logs(session, limit=limit)
    return [to_audit_log_response(audit_log) for audit_log in audit_logs]


@router.get("/extraction-errors", response_model=list[ExtractionErrorResponse])
async def get_extraction_errors(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ExtractionErrorResponse]:
    error_logs = await list_extraction_errors(session, limit=limit)
    return [to_extraction_error_response(error_log) for error_log in error_logs]
