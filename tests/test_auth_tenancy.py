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
