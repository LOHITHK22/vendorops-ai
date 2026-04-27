import asyncio
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.config.settings import Settings, get_settings
from app.db.session import init_db
from tests.helpers import auth_headers, seed_demo_identity


@pytest.fixture
def client() -> Iterator[TestClient]:
    test_root = Path(".test_storage") / str(uuid4())
    storage_dir = test_root / "storage"
    reports_dir = test_root / "reports"
    database_path = test_root / "vendorops_observability_test.db"
    test_root.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    asyncio.run(init_db(database_url))

    settings = Settings(
        local_storage_dir=storage_dir,
        reports_dir=reports_dir,
        database_url=database_url,
        openai_api_key=None,
        extraction_retry_base_seconds=0,
    )

    def override_settings() -> Settings:
        return settings

    app.dependency_overrides[get_settings] = override_settings
    seed_demo_identity(database_url, settings)
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_request_logging_middleware_returns_request_id(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "phase-8-request"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "phase-8-request"


def test_failed_pipeline_persists_error_and_audit_events(client: TestClient) -> None:
    headers = auth_headers(client, app.dependency_overrides[get_settings]())
    upload_response = client.post(
        "/v1/files",
        headers=headers,
        files={
            "file": (
                "invoice.txt",
                b"Vendor: Lost File LLC\nInvoice Number: INV-MISSING\nTotal: 25.00 USD",
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 201
    uploaded_file = upload_response.json()
    Path(uploaded_file["storage_path"]).unlink()

    job_response = client.post(
        "/v1/jobs",
        headers=headers,
        json={"file_id": uploaded_file["file_id"], "pipeline": "document_extraction"},
    )
    assert job_response.status_code == 201
    job_id = job_response.json()["job_id"]

    run_response = client.post(f"/v1/jobs/{job_id}/run", headers=headers)
    assert run_response.status_code == 422

    job_status_response = client.get(f"/v1/jobs/{job_id}", headers=headers)
    assert job_status_response.status_code == 200
    assert job_status_response.json()["status"] == "failed"

    errors_response = client.get("/v1/extraction-errors", headers=headers)
    assert errors_response.status_code == 200
    errors = errors_response.json()
    assert len(errors) == 1
    assert errors[0]["job_id"] == job_id
    assert errors[0]["file_id"] == uploaded_file["file_id"]
    assert errors[0]["stage"] == "parse"
    assert errors[0]["retryable"] is False

    audit_response = client.get("/v1/audit-logs", headers=headers)
    assert audit_response.status_code == 200
    actions = {event["action"] for event in audit_response.json()}
    assert "pipeline.error_recorded" in actions
    assert "job.status_updated" in actions
