import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.main import app
from app.config.settings import Settings, get_settings
from app.db.models import ExtractedRecord, ProcessingJob
from app.db.session import get_sessionmaker, init_db
from tests.helpers import auth_headers, seed_demo_identity, wait_for_job


def create_test_client() -> tuple[TestClient, Settings]:
    test_root = Path(".test_storage") / str(uuid4())
    storage_dir = test_root / "storage"
    database_path = test_root / "vendorops_pipeline_test.db"
    test_root.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    asyncio.run(init_db(database_url))
    settings = Settings(
        local_storage_dir=storage_dir,
        database_url=database_url,
        openai_api_key=None,
    )

    def override_settings() -> Settings:
        return settings

    app.dependency_overrides[get_settings] = override_settings
    seed_demo_identity(database_url, settings)
    return TestClient(app), settings


async def count_rows(database_url: str, model: type) -> int:
    sessionmaker = get_sessionmaker(database_url)
    async with sessionmaker() as session:
        result = await session.execute(select(model))
        return len(result.scalars().all())


def test_queued_job_runs_document_pipeline_once() -> None:
    client, settings = create_test_client()
    try:
        headers = auth_headers(client, settings)
        upload_response = client.post(
            "/v1/files",
            headers=headers,
            files={
                "file": (
                    "invoice.txt",
                    b"Vendor: Northwind Labs\nInvoice Number: INV-777\nTotal: 425.50 USD",
                    "text/plain",
                )
            },
        )
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file_id"]

        job_response = client.post(
            "/v1/jobs",
            headers=headers,
            json={"file_id": file_id, "pipeline": "document_extraction"},
        )
        assert job_response.status_code == 201
        job_id = job_response.json()["job_id"]
        assert job_response.json()["status"] == "queued"

        run_response = client.post(f"/v1/jobs/{job_id}/run", headers=headers)
        assert run_response.status_code == 202
        payload = run_response.json()

        assert payload["job_id"] == job_id
        completed_job = wait_for_job(client, job_id, headers)
        assert completed_job["status"] == "completed"

        records_response = client.get("/v1/records", headers=headers)
        assert records_response.status_code == 200
        record = records_response.json()[0]
        assert record["job_id"] == job_id
        assert record["external_reference"] == "INV-777"
        assert record["normalized_payload"]["total_amount"] == 425.5

        assert asyncio.run(count_rows(settings.database_url, ProcessingJob)) == 1
        assert asyncio.run(count_rows(settings.database_url, ExtractedRecord)) == 1

        rerun_response = client.post(f"/v1/jobs/{job_id}/run", headers=headers)
        assert rerun_response.status_code == 409
    finally:
        app.dependency_overrides.clear()
