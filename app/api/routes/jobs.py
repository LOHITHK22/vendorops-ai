from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_optional_context, tenant_ids
from app.api.routes.records import to_record_response
from app.api.routes.validation import to_validation_error_response
from app.api.schemas import CreateJobRequest, ExtractionRunResponse, ProcessingJobResponse
from app.auth.service import AuthContext
from app.config.settings import Settings, get_settings
from app.db.repositories import create_processing_job, get_processing_job, get_uploaded_file
from app.db.session import get_db_session
from app.pipeline.document_pipeline import PipelineError, PipelineInputError, run_document_pipeline

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    request: CreateJobRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[AuthContext | None, Depends(get_optional_context)],
) -> ProcessingJobResponse:
    organization_id, workspace_id = tenant_ids(context)
    file_record = await get_uploaded_file(
        session,
        request.file_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    if file_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{request.file_id}' was not found.",
        )

    job = await create_processing_job(
        session,
        job_id=uuid4(),
        file_id=request.file_id,
        pipeline=request.pipeline,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )

    return ProcessingJobResponse(
        job_id=UUID(job.id),
        file_id=UUID(job.file_id),
        pipeline=job.pipeline,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at,
        error_message=job.error_message,
    )


@router.get("/{job_id}", response_model=ProcessingJobResponse)
async def get_job(
    job_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[AuthContext | None, Depends(get_optional_context)],
) -> ProcessingJobResponse:
    organization_id, workspace_id = tenant_ids(context)
    job = await get_processing_job(
        session,
        job_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' was not found.",
        )

    return ProcessingJobResponse(
        job_id=UUID(job.id),
        file_id=UUID(job.file_id),
        pipeline=job.pipeline,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at,
        error_message=job.error_message,
    )


@router.post("/{job_id}/run", response_model=ExtractionRunResponse)
async def run_job(
    job_id: UUID,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[AuthContext | None, Depends(get_optional_context)],
) -> ExtractionRunResponse:
    organization_id, workspace_id = tenant_ids(context)
    job = await get_processing_job(
        session,
        job_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' was not found.",
        )

    if job.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job '{job_id}' is already running.",
        )
    if job.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job '{job_id}' has already completed.",
        )

    try:
        pipeline_result = await run_document_pipeline(
            session=session,
            settings=settings,
            file_id=UUID(job.file_id),
            organization_id=organization_id,
            workspace_id=workspace_id,
            job=job,
        )
    except PipelineInputError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PipelineError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return ExtractionRunResponse(
        job=ProcessingJobResponse(
            job_id=UUID(pipeline_result.job.id),
            file_id=UUID(pipeline_result.job.file_id),
            pipeline=pipeline_result.job.pipeline,
            status=pipeline_result.job.status,
            created_at=pipeline_result.job.created_at,
            updated_at=pipeline_result.job.updated_at,
            error_message=pipeline_result.job.error_message,
        ),
        record=to_record_response(pipeline_result.record),
        validation_errors=[
            to_validation_error_response(validation_error)
            for validation_error in pipeline_result.validation_errors
        ],
    )
