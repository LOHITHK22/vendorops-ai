from tests.conftest import TestAppContext


def test_analytics_dashboard_answers_operational_questions(test_app: TestAppContext) -> None:
    client = test_app.client
    headers = test_app.auth_headers()

    upload_response = client.post(
        "/v1/files",
        headers=headers,
        files={
            "file": (
                "analytics-invoice.txt",
                b"Vendor: Analyst Systems\nInvoice Number: INV-ANALYTICS\nTotal: 250.00 USD",
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 201
    file_id = upload_response.json()["file_id"]

    extraction_response = client.post(f"/v1/files/{file_id}/extract", headers=headers)
    assert extraction_response.status_code == 200

    report_response = client.post(
        "/v1/reports",
        headers=headers,
        json={"report_type": "summary", "format": "json"},
    )
    assert report_response.status_code == 201

    analytics_response = client.get("/v1/analytics/dashboard", headers=headers)
    assert analytics_response.status_code == 200
    payload = analytics_response.json()

    assert payload["processed_volume"]["all_time"] == 1
    assert payload["processed_volume"]["today"] == 1
    assert payload["kpis"]
    assert any(kpi["label"] == "Extraction accuracy" for kpi in payload["kpis"])
    assert payload["extraction_accuracy_over_time"]
    assert payload["llm_cost"]["mock_records"] == 1
    assert payload["business_reports"] == [
        {"label": "summary", "value": 1.0, "detail": "generated reports"}
    ]
    assert payload["analyst_notes"]
