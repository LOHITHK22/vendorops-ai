from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog, ProcessingJob, UploadedFile


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

