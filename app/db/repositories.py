from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog, ExtractedRecord, ProcessingJob, UploadedFile
from app.extraction.schemas import ExtractedBusinessRecord


async def create_uploaded_file(
    session: AsyncSession,
    *,
    file_id: UUID,
    original_filename: str,
    content_type: str,
    file_type: str,
    size_bytes: int,
    sha256_hash: str,
    storage_path: str,
) -> UploadedFile:
    uploaded_file = UploadedFile(
        id=str(file_id),
        original_filename=original_filename,
        content_type=content_type,
        file_type=file_type,
        size_bytes=size_bytes,
        sha256_hash=sha256_hash,
        storage_path=storage_path,
    )
    session.add(uploaded_file)
    await create_audit_log(
        session,
        action="file.uploaded",
        entity_type="uploaded_file",
        entity_id=str(file_id),
        details={
            "original_filename": original_filename,
            "content_type": content_type,
            "size_bytes": size_bytes,
            "sha256_hash": sha256_hash,
        },
    )
    await session.commit()
    await session.refresh(uploaded_file)
    return uploaded_file


async def get_uploaded_file(session: AsyncSession, file_id: UUID) -> UploadedFile | None:
    return await session.get(UploadedFile, str(file_id))


async def create_processing_job(
    session: AsyncSession,
    *,
    job_id: UUID,
    file_id: UUID,
    pipeline: str,
) -> ProcessingJob:
    job = ProcessingJob(
        id=str(job_id),
        file_id=str(file_id),
        pipeline=pipeline,
        status="queued",
    )
    session.add(job)
    await create_audit_log(
        session,
        action="job.created",
        entity_type="processing_job",
        entity_id=str(job_id),
        details={"file_id": str(file_id), "pipeline": pipeline},
    )
    await session.commit()
    await session.refresh(job)
    return job


async def get_processing_job(session: AsyncSession, job_id: UUID) -> ProcessingJob | None:
    return await session.get(ProcessingJob, str(job_id))


async def update_processing_job_status(
    session: AsyncSession,
    *,
    job: ProcessingJob,
    status: str,
    error_message: str | None = None,
) -> ProcessingJob:
    job.status = status
    job.error_message = error_message
    await create_audit_log(
        session,
        action="job.status_updated",
        entity_type="processing_job",
        entity_id=job.id,
        details={"status": status, "error_message": error_message},
    )
    await session.commit()
    await session.refresh(job)
    return job


async def create_extracted_record(
    session: AsyncSession,
    *,
    file_id: UUID,
    job_id: UUID | None,
    extracted: ExtractedBusinessRecord,
    raw_payload: dict,
) -> ExtractedRecord:
    record = ExtractedRecord(
        file_id=str(file_id),
        job_id=str(job_id) if job_id else None,
        record_type=extracted.record_type.value,
        vendor_name=extracted.vendor_name,
        external_reference=extracted.document_id,
        normalized_payload=extracted.model_dump(mode="json"),
        raw_payload=raw_payload,
        confidence=extracted.confidence,
    )
    session.add(record)
    await session.flush()
    await create_audit_log(
        session,
        action="record.extracted",
        entity_type="extracted_record",
        entity_id=record.id,
        details={
            "file_id": str(file_id),
            "job_id": str(job_id) if job_id else None,
            "record_type": extracted.record_type.value,
            "confidence": extracted.confidence,
            "provider": raw_payload.get("provider"),
        },
    )
    await session.commit()
    await session.refresh(record)
    return record


async def list_extracted_records(session: AsyncSession) -> list[ExtractedRecord]:
    result = await session.execute(
        select(ExtractedRecord).order_by(ExtractedRecord.created_at.desc())
    )
    return list(result.scalars().all())


async def get_extracted_record(session: AsyncSession, record_id: UUID) -> ExtractedRecord | None:
    return await session.get(ExtractedRecord, str(record_id))


async def create_audit_log(
    session: AsyncSession,
    *,
    action: str,
    entity_type: str,
    entity_id: str | None,
    details: dict | None = None,
    actor: str = "system",
) -> AuditLog:
    audit_log = AuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    session.add(audit_log)
    return audit_log


async def count_audit_logs(session: AsyncSession) -> int:
    result = await session.execute(select(AuditLog))
    return len(result.scalars().all())
