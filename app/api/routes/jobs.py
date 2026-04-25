from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas import CreateJobRequest, JobRecord, ProcessingJobResponse
from app.api.state import InMemoryState, get_app_state

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    request: CreateJobRequest,
    state: Annotated[InMemoryState, Depends(get_app_state)],
) -> ProcessingJobResponse:
    file_record = state.get_file(request.file_id)
    if file_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{request.file_id}' was not found.",
        )

    now = datetime.now(UTC)
    job_record = JobRecord(
        job_id=uuid4(),
        file_id=request.file_id,
        pipeline=request.pipeline,
        status="queued",
        created_at=now,
        updated_at=now,
    )
    state.add_job(job_record)

    return ProcessingJobResponse(**job_record.model_dump())


@router.get("/{job_id}", response_model=ProcessingJobResponse)
async def get_job(
    job_id: UUID,
    state: Annotated[InMemoryState, Depends(get_app_state)],
) -> ProcessingJobResponse:
    job_record = state.get_job(job_id)
    if job_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' was not found.",
        )

    return ProcessingJobResponse(**job_record.model_dump())
