import asyncio
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.config.settings import Settings, get_settings
from app.db.session import init_db


@dataclass(frozen=True)
class TestAppContext:
    __test__ = False

    client: TestClient
    settings: Settings
    root: Path


@pytest.fixture
def test_app() -> Iterator[TestAppContext]:
    test_root = Path(".test_storage") / str(uuid4())
    storage_dir = test_root / "storage"
    reports_dir = test_root / "reports"
    database_path = test_root / "vendorops_test.db"
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
    with TestClient(app) as client:
        yield TestAppContext(client=client, settings=settings, root=test_root)

    app.dependency_overrides.clear()
