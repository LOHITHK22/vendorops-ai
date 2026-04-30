import logging
from uuid import UUID

from fastapi import BackgroundTasks

from app.config.settings import Settings
from app.db.repositories import get_processing_job
from app.db.session import get_sessionmaker
from app.observability.logging import get_logger, log_event
from app.pipeline.document_pipeline import PipelineError, run_document_pipeline

logger = get_logger(__name__)


def enqueue_document_job(
    background_tasks: BackgroundTasks,
    *,
    settings: Settings,
    job_id: UUID,
) -> None:
    background_tasks.add_task(execute_document_job, settings=settings, job_id=job_id)


async def execute_document_job(*, settings: Settings, job_id: UUID) -> None:
    sessionmaker = get_sessionmaker(settings.database_url)
    async with sessionmaker() as session:
        job = await get_processing_job(session, job_id)
        if job is None:
            log_event(
                logger,
                logging.WARNING,
                "worker.job_missing",
                "Document job was not found",
                job_id=str(job_id),
            )
            return

        if job.status in {"running", "completed"}:
            log_event(
                logger,
                logging.INFO,
                "worker.job_skipped",
                "Document job is already active or complete",
                job_id=str(job_id),
                status=job.status,
            )
            return

        try:
            await run_document_pipeline(
                session=session,
                settings=settings,
                file_id=UUID(job.file_id),
                organization_id=UUID(job.organization_id) if job.organization_id else None,
                workspace_id=UUID(job.workspace_id) if job.workspace_id else None,
                job=job,
            )
        except PipelineError as exc:
            log_event(
                logger,
                logging.ERROR,
                "worker.job_failed",
                "Document job failed",
                job_id=str(job_id),
                error=str(exc),
            )
