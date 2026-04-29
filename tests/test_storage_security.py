from pathlib import Path
from uuid import uuid4

import pytest

from app.ingestion.storage import sanitize_filename, validate_upload_filename
from app.storage.backends import LocalObjectStorage, StorageError


def test_upload_filename_is_sanitized_and_restricted() -> None:
    assert sanitize_filename("../../Vendor Invoice 001.pdf") == "Vendor_Invoice_001.pdf"
    assert sanitize_filename("weird#$ name.txt") == "weird_name.txt"

    with pytest.raises(ValueError):
        validate_upload_filename("malware.exe")


def test_local_storage_blocks_paths_outside_root() -> None:
    test_root = Path(".test_storage") / str(uuid4())
    storage = LocalObjectStorage(test_root / "objects")

    stored = storage.put_bytes(
        key="uploads/file-id/invoice.txt",
        content=b"hello",
        content_type="text/plain",
    )

    assert storage.exists(stored.uri)
    assert storage.read_bytes(stored.uri) == b"hello"

    with pytest.raises(StorageError):
        storage.put_bytes(
            key="../escape.txt",
            content=b"bad",
            content_type="text/plain",
        )
