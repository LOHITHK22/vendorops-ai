import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.main import app
from app.config.settings import Settings, get_settings
from app.db.models import ExtractedRecord, ProcessingJob
from app.db.session import get_sessionmaker, init_db
from app.extraction.extractor import MockExtractor
from app.parsers.dispatcher import parse_file
from tests.helpers import auth_headers, seed_demo_identity, wait_for_job


def create_test_client() -> tuple[TestClient, Settings]:
    test_root = Path(".test_storage") / str(uuid4())
    storage_dir = test_root / "storage"
    database_path = test_root / "vendorops_extract_test.db"
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


def test_mock_extractor_returns_schema_valid_record() -> None:
    parsed_document = parse_file("tests/fixtures/sample_invoice.txt")

    result = asyncio.run(MockExtractor().extract(parsed_document))

    assert result.provider == "mock"
    assert result.record.record_type == "invoice"
    assert result.record.document_id == "INV-001"
    assert result.record.total_amount == 100.0
    assert result.record.confidence >= 0.75


def test_extract_endpoint_persists_record_and_job() -> None:
    client, settings = create_test_client()
    try:
        headers = auth_headers(client, settings)
        upload_response = client.post(
            "/v1/files",
            headers=headers,
            files={
                "file": (
                    "invoice.txt",
                    b"Vendor: Acme Software LLC\nInvoice Number: INV-009\nTotal: 199.00 USD",
                    "text/plain",
                )
            },
        )
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file_id"]

        extraction_response = client.post(f"/v1/files/{file_id}/extract", headers=headers)
        assert extraction_response.status_code == 202
        job = wait_for_job(client, extraction_response.json()["job_id"], headers)
        assert job["status"] == "completed"

        records_response = client.get("/v1/records", headers=headers)
        assert records_response.status_code == 200
        records = records_response.json()
        assert len(records) == 1
        assert records[0]["record_type"] == "invoice"
        assert records[0]["vendor_name"] == "Acme Software LLC"
        assert records[0]["external_reference"] == "INV-009"
        assert records[0]["normalized_payload"]["total_amount"] == 199.0

        assert asyncio.run(count_rows(settings.database_url, ProcessingJob)) == 1
        assert asyncio.run(count_rows(settings.database_url, ExtractedRecord)) == 1
    finally:
        app.dependency_overrides.clear()
