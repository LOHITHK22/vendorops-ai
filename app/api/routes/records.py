from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ExtractedRecordResponse
from app.db.repositories import get_extracted_record, list_extracted_records
from app.db.session import get_db_session

router = APIRouter(prefix="/records", tags=["records"])


def to_record_response(record) -> ExtractedRecordResponse:
    return ExtractedRecordResponse(
        record_id=UUID(record.id),
        file_id=UUID(record.file_id),
        job_id=UUID(record.job_id) if record.job_id else None,
        record_type=record.record_type,
        vendor_name=record.vendor_name,
        external_reference=record.external_reference,
        confidence=record.confidence,
        normalized_payload=record.normalized_payload,
        raw_payload=record.raw_payload,
        created_at=record.created_at,
    )


@router.get("", response_model=list[ExtractedRecordResponse])
async def list_records(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ExtractedRecordResponse]:
    records = await list_extracted_records(session)
    return [to_record_response(record) for record in records]


@router.get("/{record_id}", response_model=ExtractedRecordResponse)
async def get_record(
    record_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExtractedRecordResponse:
    record = await get_extracted_record(session, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record '{record_id}' was not found.",
        )
    return to_record_response(record)
