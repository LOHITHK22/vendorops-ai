from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

ALLOWED_FILE_EXTENSIONS = {".csv", ".eml", ".pdf", ".txt"}


@dataclass(frozen=True)
class StoredUpload:
    file_id: str
    original_filename: str
    content_type: str
    size_bytes: int
    sha256_hash: str
    storage_path: Path


def validate_upload_filename(filename: str | None) -> str:
    if not filename:
        raise ValueError("Uploaded file must include a filename.")

    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_FILE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_FILE_EXTENSIONS))
        raise ValueError(f"Unsupported file type '{suffix}'. Allowed types: {allowed}.")

    return Path(filename).name


async def store_upload(upload_file: UploadFile, storage_dir: Path) -> StoredUpload:
    original_filename = validate_upload_filename(upload_file.filename)
    content = await upload_file.read()

    if not content:
        raise ValueError("Uploaded file is empty.")

    file_id = str(uuid4())
    digest = sha256(content).hexdigest()
    target_dir = storage_dir / file_id
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / original_filename
    target_path.write_bytes(content)

    return StoredUpload(
        file_id=file_id,
        original_filename=original_filename,
        content_type=upload_file.content_type or "application/octet-stream",
        size_bytes=len(content),
        sha256_hash=digest,
        storage_path=target_path,
    )

