from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.state import app_state
from app.config.settings import Settings, get_settings


@pytest.fixture
def client() -> Iterator[TestClient]:
    app_state.reset()
    storage_dir = Path(".test_storage") / str(uuid4())

    def override_settings() -> Settings:
        return Settings(local_storage_dir=storage_dir)

    app.dependency_overrides[get_settings] = override_settings
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    app_state.reset()


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
