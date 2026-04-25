from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import UploadedFileResponse
from app.config.settings import Settings, get_settings
from app.db.repositories import create_uploaded_file
from app.db.session import get_db_session
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
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UploadedFileResponse:
    try:
        stored_upload = await store_upload(file, settings.local_storage_dir)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    uploaded_file = await create_uploaded_file(
        session,
        file_id=UUID(stored_upload.file_id),
        original_filename=stored_upload.original_filename,
        content_type=stored_upload.content_type,
        file_type=stored_upload.storage_path.suffix.lower().lstrip("."),
        size_bytes=stored_upload.size_bytes,
        sha256_hash=stored_upload.sha256_hash,
        storage_path=str(stored_upload.storage_path),
    )

    return UploadedFileResponse(
        file_id=UUID(uploaded_file.id),
        original_filename=uploaded_file.original_filename,
        content_type=uploaded_file.content_type,
        size_bytes=uploaded_file.size_bytes,
        sha256_hash=uploaded_file.sha256_hash,
        storage_path=uploaded_file.storage_path,
        created_at=uploaded_file.created_at,
    )
