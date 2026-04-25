import asyncio
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.main import app
from app.config.settings import Settings, get_settings
from app.db.models import AuditLog, ProcessingJob, UploadedFile
from app.db.session import get_sessionmaker, init_db


@pytest.fixture
def client() -> Iterator[TestClient]:
    test_root = Path(".test_storage") / str(uuid4())
    storage_dir = test_root / "storage"
    database_path = test_root / "vendorops_test.db"
    test_root.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    asyncio.run(init_db(database_url))

    def override_settings() -> Settings:
        return Settings(local_storage_dir=storage_dir, database_url=database_url)

    app.dependency_overrides[get_settings] = override_settings
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


async def count_rows(database_url: str, model: type) -> int:
    sessionmaker = get_sessionmaker(database_url)
    async with sessionmaker() as session:
        result = await session.execute(select(model))
        return len(result.scalars().all())


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app_name"] == "VendorOps AI"


def test_upload_file_and_create_job(client: TestClient) -> None:
    upload_response = client.post(
        "/v1/files",
        files={"file": ("invoice.txt", b"Invoice Number: INV-001\nTotal: 100.00", "text/plain")},
    )

    assert upload_response.status_code == 201
    uploaded_file = upload_response.json()
    assert uploaded_file["original_filename"] == "invoice.txt"
    assert uploaded_file["size_bytes"] > 0
    assert Path(uploaded_file["storage_path"]).exists()

    job_response = client.post(
        "/v1/jobs",
        json={"file_id": uploaded_file["file_id"], "pipeline": "document_extraction"},
    )

    assert job_response.status_code == 201
    job = job_response.json()
    assert job["file_id"] == uploaded_file["file_id"]
    assert job["status"] == "queued"

    status_response = client.get(f"/v1/jobs/{job['job_id']}")
    assert status_response.status_code == 200
    assert status_response.json()["job_id"] == job["job_id"]

    settings = app.dependency_overrides[get_settings]()
    assert asyncio.run(count_rows(settings.database_url, UploadedFile)) == 1
    assert asyncio.run(count_rows(settings.database_url, ProcessingJob)) == 1
    assert asyncio.run(count_rows(settings.database_url, AuditLog)) == 2


def test_upload_rejects_unsupported_file_type(client: TestClient) -> None:
    response = client.post(
        "/v1/files",
        files={"file": ("image.png", b"not supported", "image/png")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_create_job_requires_existing_file(client: TestClient) -> None:
    response = client.post(
        "/v1/jobs",
        json={
            "file_id": "00000000-0000-0000-0000-000000000000",
            "pipeline": "document_extraction",
        },
    )

    assert response.status_code == 404
