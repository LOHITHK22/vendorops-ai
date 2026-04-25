from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class UploadedFileResponse(BaseModel):
    file_id: UUID
    original_filename: str
    content_type: str
    size_bytes: int
    sha256_hash: str
    storage_path: str
    created_at: datetime


class CreateJobRequest(BaseModel):
    file_id: UUID
    pipeline: str = Field(default="document_extraction", min_length=1, max_length=100)


class ProcessingJobResponse(BaseModel):
    job_id: UUID
    file_id: UUID
    pipeline: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ErrorResponse(BaseModel):
    detail: str


class DatabaseSummaryResponse(BaseModel):
    tables: list[str]
