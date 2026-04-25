import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.main import app
from app.config.settings import Settings, get_settings
from app.db.session import init_db
from app.extraction.schemas import ExtractedBusinessRecord, ExtractedRecordType
from app.validation.rules import validate_extracted_record


def create_test_client() -> TestClient:
    test_root = Path(".test_storage") / str(uuid4())
    storage_dir = test_root / "storage"
    database_path = test_root / "vendorops_validation_test.db"
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
    return TestClient(app)


def test_validation_rules_flag_missing_invoice_fields() -> None:
    record = ExtractedBusinessRecord(
        record_type=ExtractedRecordType.invoice,
        summary="Incomplete invoice extraction.",
        confidence=0.42,
        needs_review=True,
    )

    findings = validate_extracted_record(record)
    finding_types = {finding.error_type for finding in findings}

    assert "required_field_missing" in finding_types
    assert "low_confidence" in finding_types


def test_validation_errors_endpoint_lists_persisted_findings() -> None:
    client = create_test_client()
    try:
        upload_response = client.post(
            "/v1/files",
            files={
                "file": (
                    "ambiguous.txt",
                    b"This is a short vendor note without invoice totals.",
                    "text/plain",
                )
            },
        )
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file_id"]

        extraction_response = client.post(f"/v1/files/{file_id}/extract")
        assert extraction_response.status_code == 200
        validation_errors = extraction_response.json()["validation_errors"]

        assert validation_errors
        assert any(error["error_type"] == "low_confidence" for error in validation_errors)

        list_response = client.get("/v1/validation-errors")
        assert list_response.status_code == 200
        assert len(list_response.json()) == len(validation_errors)

        record_id = extraction_response.json()["record"]["record_id"]
        record_response = client.get(f"/v1/validation-errors/records/{record_id}")
        assert record_response.status_code == 200
        assert len(record_response.json()) == len(validation_errors)
    finally:
        app.dependency_overrides.clear()
