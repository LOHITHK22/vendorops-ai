import asyncio
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.auth.service import AuthorizationError, require_permission
from app.db.models import ExtractedRecord, ProcessingJob, UploadedFile
from app.db.session import get_sessionmaker
from tests.conftest import TestAppContext


def test_demo_admin_can_login_and_read_workspace_context(test_app: TestAppContext) -> None:
    client = test_app.client
    settings = test_app.settings

    login_response = client.post(
        "/v1/auth/login",
        json={
            "email": settings.demo_admin_email,
            "password": settings.demo_admin_password,
        },
    )

    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["token_type"] == "bearer"
    assert login_payload["access_token"]
    assert login_payload["user"]["email"] == settings.demo_admin_email
    assert login_payload["user"]["organization"]["name"] == settings.default_organization_name
    assert login_payload["user"]["workspace"]["name"] == settings.default_workspace_name
    assert login_payload["user"]["workspace"]["role"] == "owner"
    assert "workspace:admin" in login_payload["user"]["permissions"]

    me_response = client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {login_payload['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["user_id"] == login_payload["user"]["user_id"]


def test_auth_me_rejects_missing_or_invalid_token(test_app: TestAppContext) -> None:
    client = test_app.client

    missing_response = client.get("/v1/auth/me")
    assert missing_response.status_code == 401

    invalid_response = client.get(
        "/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert invalid_response.status_code == 401


def test_login_rejects_bad_password(test_app: TestAppContext) -> None:
    client = test_app.client
    settings = test_app.settings

    response = client.post(
        "/v1/auth/login",
        json={
            "email": settings.demo_admin_email,
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


def test_protected_business_endpoints_require_bearer_token(test_app: TestAppContext) -> None:
    client = test_app.client

    upload_response = client.post(
        "/v1/files",
        files={"file": ("invoice.txt", b"Invoice Number: INV-001", "text/plain")},
    )
    assert upload_response.status_code == 401

    analytics_response = client.get("/v1/analytics/dashboard")
    assert analytics_response.status_code == 401


def test_role_permissions_block_unauthorized_actions() -> None:
    viewer_context = SimpleNamespace(membership=SimpleNamespace(role="viewer"))

    require_permission(viewer_context, "analytics:read")
    with pytest.raises(AuthorizationError):
        require_permission(viewer_context, "pipeline:write")


async def get_first_row(database_url: str, model: type):
    sessionmaker = get_sessionmaker(database_url)
    async with sessionmaker() as session:
        result = await session.execute(select(model))
        return result.scalars().first()


def test_authenticated_pipeline_persists_workspace_scope(test_app: TestAppContext) -> None:
    client = test_app.client
    settings = test_app.settings

    login_response = client.post(
        "/v1/auth/login",
        json={
            "email": settings.demo_admin_email,
            "password": settings.demo_admin_password,
        },
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    headers = {"Authorization": f"Bearer {login_payload['access_token']}"}
    expected_org_id = login_payload["user"]["organization"]["organization_id"]
    expected_workspace_id = login_payload["user"]["workspace"]["workspace_id"]

    upload_response = client.post(
        "/v1/files",
        headers=headers,
        files={
            "file": (
                "workspace-invoice.txt",
                b"Vendor: Contoso Cloud\nInvoice Number: INV-456\nTotal: 249.99 USD",
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 201

    extract_response = client.post(
        f"/v1/files/{upload_response.json()['file_id']}/extract",
        headers=headers,
    )
    assert extract_response.status_code == 200

    uploaded_file = asyncio.run(get_first_row(settings.database_url, UploadedFile))
    processing_job = asyncio.run(get_first_row(settings.database_url, ProcessingJob))
    extracted_record = asyncio.run(get_first_row(settings.database_url, ExtractedRecord))

    assert uploaded_file.organization_id == expected_org_id
    assert uploaded_file.workspace_id == expected_workspace_id
    assert processing_job.organization_id == expected_org_id
    assert processing_job.workspace_id == expected_workspace_id
    assert extracted_record.organization_id == expected_org_id
    assert extracted_record.workspace_id == expected_workspace_id

    analytics_response = client.get("/v1/analytics/dashboard", headers=headers)
    assert analytics_response.status_code == 200
    assert analytics_response.json()["processed_volume"]["all_time"] == 1
