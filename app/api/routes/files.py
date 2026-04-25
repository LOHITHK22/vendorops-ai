from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.schemas import FileRecord, UploadedFileResponse
from app.api.state import InMemoryState, get_app_state
from app.config.settings import Settings, get_settings
from app.ingestion.storage import store_upload

router = APIRouter(prefix="/files", tags=["files"])


@router.post(
    "",
    response_model=UploadedFileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    file: Annotated[UploadFile, File(...)],
    settings: Annotated[Settings, Depends(get_settings)],
    state: Annotated[InMemoryState, Depends(get_app_state)],
) -> UploadedFileResponse:
    try:
        stored_upload = await store_upload(file, settings.local_storage_dir)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    file_record = FileRecord(
        file_id=UUID(stored_upload.file_id),
        original_filename=stored_upload.original_filename,
        content_type=stored_upload.content_type,
        size_bytes=stored_upload.size_bytes,
        sha256_hash=stored_upload.sha256_hash,
        storage_path=str(stored_upload.storage_path),
        created_at=datetime.now(UTC),
    )
    state.add_file(file_record)

    return UploadedFileResponse(**file_record.model_dump())
