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


class ParsedPageResponse(BaseModel):
    page_number: int
    text: str


class ParsedTableResponse(BaseModel):
    name: str
    columns: list[str]
    rows: list[dict]


class ParsedDocumentResponse(BaseModel):
    source_path: str
    file_type: str
    text: str
    metadata: dict
    pages: list[ParsedPageResponse]
    tables: list[ParsedTableResponse]


class ExtractedRecordResponse(BaseModel):
    record_id: UUID
    file_id: UUID
    job_id: UUID | None = None
    record_type: str
    vendor_name: str | None = None
    external_reference: str | None = None
    confidence: float | None = None
    normalized_payload: dict
    raw_payload: dict | None = None
    created_at: datetime


class ValidationErrorResponse(BaseModel):
    validation_error_id: UUID
    record_id: UUID | None = None
    job_id: UUID | None = None
    field_name: str | None = None
    error_type: str
    message: str
    severity: str
    created_at: datetime


class ExtractionRunResponse(BaseModel):
    job: ProcessingJobResponse
    record: ExtractedRecordResponse
    validation_errors: list[ValidationErrorResponse]


class CreateReportRequest(BaseModel):
    report_type: str = Field(default="summary", pattern="^(summary|records)$")
    format: str = Field(default="json", pattern="^(json|csv)$")


class GeneratedReportResponse(BaseModel):
    report_id: UUID
    report_type: str
    status: str
    parameters: dict
    storage_path: str | None = None
    created_at: datetime
