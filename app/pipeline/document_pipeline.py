from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.db.models import ExtractedRecord, ProcessingJob, ValidationError
from app.db.repositories import (
    create_extracted_record,
    create_processing_job,
    create_validation_errors,
    get_uploaded_file,
    update_processing_job_status,
)
from app.extraction.extractor import ExtractionError, get_extractor
from app.parsers.dispatcher import parse_file
from app.parsers.models import ParserError
from app.validation.rules import validate_extracted_record


class PipelineError(Exception):
    """Base class for document pipeline failures."""


class PipelineInputError(PipelineError):
    """Raised when the requested pipeline input is not usable."""


@dataclass(frozen=True)
class DocumentPipelineResult:
    job: ProcessingJob
    record: ExtractedRecord
    validation_errors: list[ValidationError]


async def run_document_pipeline(
    *,
    session: AsyncSession,
    settings: Settings,
    file_id: UUID,
    job: ProcessingJob | None = None,
) -> DocumentPipelineResult:
    uploaded_file = await get_uploaded_file(session, file_id)
    if uploaded_file is None:
        raise PipelineInputError(f"File '{file_id}' was not found.")

    if job is None:
        job = await create_processing_job(
            session,
            job_id=uuid4(),
            file_id=file_id,
            pipeline="document_extraction",
        )
    elif job.pipeline != "document_extraction":
        raise PipelineInputError(f"Unsupported pipeline '{job.pipeline}'.")

    job = await update_processing_job_status(session, job=job, status="running")

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
        await update_processing_job_status(
            session,
            job=job,
            status="failed",
            error_message=str(exc),
        )
        raise PipelineError(str(exc)) from exc

    return DocumentPipelineResult(
        job=job,
        record=record,
        validation_errors=validation_errors,
    )

