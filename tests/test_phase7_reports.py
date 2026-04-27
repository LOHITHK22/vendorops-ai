import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.main import app
from app.config.settings import Settings, get_settings
from app.db.session import init_db
from tests.helpers import auth_headers, seed_demo_identity


def create_test_client() -> TestClient:
    test_root = Path(".test_storage") / str(uuid4())
    storage_dir = test_root / "storage"
    reports_dir = test_root / "reports"
    database_path = test_root / "vendorops_reports_test.db"
    test_root.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    asyncio.run(init_db(database_url))
    settings = Settings(
        local_storage_dir=storage_dir,
        reports_dir=reports_dir,
        database_url=database_url,
        openai_api_key=None,
    )

    def override_settings() -> Settings:
        return settings

    app.dependency_overrides[get_settings] = override_settings
    seed_demo_identity(database_url, settings)
    return TestClient(app)


def seed_extracted_record(client: TestClient, headers: dict[str, str]) -> None:
    upload_response = client.post(
        "/v1/files",
        headers=headers,
        files={
            "file": (
                "invoice.txt",
                b"Vendor: Globex Finance\nInvoice Number: INV-880\nTotal: 880.00 USD",
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 201
    file_id = upload_response.json()["file_id"]
    extraction_response = client.post(f"/v1/files/{file_id}/extract", headers=headers)
    assert extraction_response.status_code == 200


def test_generate_json_and_csv_reports() -> None:
    client = create_test_client()
    try:
        headers = auth_headers(client, app.dependency_overrides[get_settings]())
        seed_extracted_record(client, headers)

        json_response = client.post(
            "/v1/reports",
            headers=headers,
            json={"report_type": "summary", "format": "json"},
        )
        assert json_response.status_code == 201
        json_report = json_response.json()
        assert json_report["report_type"] == "summary"
        assert Path(json_report["storage_path"]).exists()

        download_response = client.get(
            f"/v1/reports/{json_report['report_id']}/download",
            headers=headers,
        )
        assert download_response.status_code == 200
        assert download_response.json()["record_count"] == 1

        csv_response = client.post(
            "/v1/reports",
            headers=headers,
            json={"report_type": "records", "format": "csv"},
        )
        assert csv_response.status_code == 201
        csv_report = csv_response.json()
        assert Path(csv_report["storage_path"]).exists()

        csv_download = client.get(
            f"/v1/reports/{csv_report['report_id']}/download",
            headers=headers,
        )
        assert csv_download.status_code == 200
        assert "Globex Finance" in csv_download.text

        list_response = client.get("/v1/reports", headers=headers)
        assert list_response.status_code == 200
        assert len(list_response.json()) == 2
    finally:
        app.dependency_overrides.clear()
