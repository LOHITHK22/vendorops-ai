import asyncio

from fastapi.testclient import TestClient

from app.auth.service import seed_default_identity
from app.config.settings import Settings
from app.db.session import get_sessionmaker


def seed_demo_identity(database_url: str, settings: Settings) -> None:
    async def seed() -> None:
        sessionmaker = get_sessionmaker(database_url)
        async with sessionmaker() as session:
            await seed_default_identity(session, settings)

    asyncio.run(seed())


def auth_headers(client: TestClient, settings: Settings) -> dict[str, str]:
    response = client.post(
        "/v1/auth/login",
        json={
            "email": settings.demo_admin_email,
            "password": settings.demo_admin_password,
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
