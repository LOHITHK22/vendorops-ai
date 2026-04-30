from uuid import UUID

from app.api.schemas import ProcessingJobResponse
from app.db.models import ProcessingJob


def to_processing_job_response(job: ProcessingJob) -> ProcessingJobResponse:
    return ProcessingJobResponse(
        job_id=UUID(job.id),
        file_id=UUID(job.file_id),
        pipeline=job.pipeline,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at,
        error_message=job.error_message,
    )
