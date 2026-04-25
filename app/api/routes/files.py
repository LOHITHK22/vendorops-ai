from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.records import to_record_response
from app.api.routes.validation import to_validation_error_response
from app.api.schemas import (
    ExtractionRunResponse,
    ParsedDocumentResponse,
    ProcessingJobResponse,
    UploadedFileResponse,
)
from app.config.settings import Settings, get_settings
from app.db.repositories import (
    create_extracted_record,
    create_processing_job,
    create_uploaded_file,
    create_validation_errors,
    get_uploaded_file,
    update_processing_job_status,
)
from app.db.session import get_db_session
from app.extraction.extractor import ExtractionError, get_extractor
from app.ingestion.storage import store_upload
from app.parsers.dispatcher import parse_file
from app.parsers.models import ParserError
from app.validation.rules import validate_extracted_record

router = APIRouter(prefix="/files", tags=["files"])


@router.post(
    "",
    response_model=UploadedFileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    file: Annotated[UploadFile, File(...)],
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UploadedFileResponse:
    try:
        stored_upload = await store_upload(file, settings.local_storage_dir)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    uploaded_file = await create_uploaded_file(
        session,
        file_id=UUID(stored_upload.file_id),
        original_filename=stored_upload.original_filename,
        content_type=stored_upload.content_type,
        file_type=stored_upload.storage_path.suffix.lower().lstrip("."),
        size_bytes=stored_upload.size_bytes,
        sha256_hash=stored_upload.sha256_hash,
        storage_path=str(stored_upload.storage_path),
    )

    return UploadedFileResponse(
        file_id=UUID(uploaded_file.id),
        original_filename=uploaded_file.original_filename,
        content_type=uploaded_file.content_type,
        size_bytes=uploaded_file.size_bytes,
        sha256_hash=uploaded_file.sha256_hash,
        storage_path=uploaded_file.storage_path,
        created_at=uploaded_file.created_at,
    )


@router.get("/{file_id}/parsed", response_model=ParsedDocumentResponse)
async def parse_uploaded_file(
    file_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ParsedDocumentResponse:
    uploaded_file = await get_uploaded_file(session, file_id)
    if uploaded_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{file_id}' was not found.",
        )

    try:
        parsed_document = parse_file(uploaded_file.storage_path)
    except ParserError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return ParsedDocumentResponse(**parsed_document.model_dump())


@router.post("/{file_id}/extract", response_model=ExtractionRunResponse)
async def extract_uploaded_file(
    file_id: UUID,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExtractionRunResponse:
    uploaded_file = await get_uploaded_file(session, file_id)
    if uploaded_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{file_id}' was not found.",
        )

    job = await create_processing_job(
        session,
        job_id=uuid4(),
        file_id=file_id,
        pipeline="document_extraction",
    )
    await update_processing_job_status(session, job=job, status="running")

    try:
        parsed_document = parse_file(uploaded_file.storage_path)
        extraction_result = await get_extractor(settings).extract(parsed_document)
        record = await create_extracted_record(
            session,
            file_id=file_id,
            job_id=UUID(job.id),
            extracted=extraction_result.record,
            raw_payload=extraction_result.model_dump(mode="json"),
        )
        findings = validate_extracted_record(extraction_result.record)
        validation_errors = await create_validation_errors(
            session,
            record_id=UUID(record.id),
            job_id=UUID(job.id),
            findings=findings,
        )
        job = await update_processing_job_status(session, job=job, status="completed")
    except (ParserError, ExtractionError, ValueError) as exc:
        job = await update_processing_job_status(
            session,
            job=job,
            status="failed",
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return ExtractionRunResponse(
        job=ProcessingJobResponse(
            job_id=UUID(job.id),
            file_id=UUID(job.file_id),
            pipeline=job.pipeline,
            status=job.status,
            created_at=job.created_at,
            updated_at=job.updated_at,
            error_message=job.error_message,
        ),
        record=to_record_response(record),
        validation_errors=[
            to_validation_error_response(validation_error)
            for validation_error in validation_errors
        ],
    )
