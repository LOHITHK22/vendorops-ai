import sqlite3
from pathlib import Path
from uuid import uuid4

from alembic.config import Config

from alembic import command


def test_alembic_initial_migration_creates_core_schema(
    monkeypatch,
) -> None:
    test_root = Path(".test_storage") / str(uuid4())
    test_root.mkdir(parents=True, exist_ok=True)
    database_path = test_root / "migration_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database_path.as_posix()}")

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "select name from sqlite_master where type = 'table'"
            ).fetchall()
        }
        columns = {
            row[1]
            for row in connection.execute("pragma table_info(uploaded_files)").fetchall()
        }

    assert {
        "organizations",
        "workspaces",
        "user_accounts",
        "uploaded_files",
        "processing_jobs",
        "extracted_records",
        "validation_errors",
        "audit_logs",
        "extraction_errors",
        "generated_reports",
        "alembic_version",
    }.issubset(tables)
    assert {"organization_id", "workspace_id"}.issubset(columns)
