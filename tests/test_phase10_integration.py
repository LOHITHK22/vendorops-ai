from pathlib import Path

from tests.conftest import TestAppContext
from tests.helpers import wait_for_job


def test_full_api_flow_from_upload_to_report_and_audit(test_app: TestAppContext) -> None:
    client = test_app.client
    headers = test_app.auth_headers()

    upload_response = client.post(
        "/v1/files",
        headers=headers,
        files={
            "file": (
                "phase10-invoice.txt",
                b"Vendor: Phase Ten Systems\nInvoice Number: INV-1010\nTotal: 1010.25 USD",
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 201
    uploaded_file = upload_response.json()

    parse_response = client.get(f"/v1/files/{uploaded_file['file_id']}/parsed", headers=headers)
    assert parse_response.status_code == 200
    assert "Phase Ten Systems" in parse_response.json()["text"]

    extract_response = client.post(f"/v1/files/{uploaded_file['file_id']}/extract", headers=headers)
    assert extract_response.status_code == 202
    job = wait_for_job(client, extract_response.json()["job_id"], headers)
    assert job["status"] == "completed"

    records_response = client.get("/v1/records", headers=headers)
    assert records_response.status_code == 200
    assert len(records_response.json()) == 1
    extraction = records_response.json()[0]
    assert extraction["vendor_name"] == "Phase Ten Systems"
    assert extraction["external_reference"] == "INV-1010"
    assert extraction["normalized_payload"]["total_amount"] == 1010.25

    validation_response = client.get(
        f"/v1/validation-errors/records/{extraction['record_id']}",
        headers=headers,
    )
    assert validation_response.status_code == 200
    assert validation_response.json() == []

    record_response = client.get(f"/v1/records/{extraction['record_id']}", headers=headers)
    assert record_response.status_code == 200
    assert record_response.json()["record_id"] == extraction["record_id"]

    report_response = client.post(
        "/v1/reports",
        headers=headers,
        json={"report_type": "summary", "format": "json"},
    )
    assert report_response.status_code == 201
    report = report_response.json()
    assert Path(report["storage_path"]).exists()

    report_download = client.get(f"/v1/reports/{report['report_id']}/download", headers=headers)
    assert report_download.status_code == 200
    assert report_download.json()["vendor_totals"] == [
        {"vendor_name": "Phase Ten Systems", "total_amount": 1010.25}
    ]

    errors_response = client.get("/v1/extraction-errors", headers=headers)
    assert errors_response.status_code == 200
    assert errors_response.json() == []

    audit_response = client.get("/v1/audit-logs", headers=headers)
    assert audit_response.status_code == 200
    actions = {event["action"] for event in audit_response.json()}
    assert {
        "file.uploaded",
        "job.created",
        "job.status_updated",
        "record.extracted",
        "record.validated",
        "report.generated",
    }.issubset(actions)


def test_api_error_contracts_are_stable(test_app: TestAppContext) -> None:
    client = test_app.client
    headers = test_app.auth_headers()

    missing_record_response = client.get(
        "/v1/records/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert missing_record_response.status_code == 404
    assert "was not found" in missing_record_response.json()["detail"]

    invalid_report_response = client.post(
        "/v1/reports",
        headers=headers,
        json={"report_type": "summary", "format": "xlsx"},
    )
    assert invalid_report_response.status_code == 422

    missing_report_download = client.get(
        "/v1/reports/00000000-0000-0000-0000-000000000000/download",
        headers=headers,
    )
    assert missing_report_download.status_code == 404
    assert "was not found" in missing_report_download.json()["detail"]
