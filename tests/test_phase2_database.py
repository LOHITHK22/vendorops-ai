import asyncio
from pathlib import Path
from uuid import uuid4

from sqlalchemy import inspect

from app.db.models import (
    AuditLog,
    ExtractedRecord,
    GeneratedReport,
    ProcessingJob,
    UploadedFile,
    ValidationError,
)
from app.db.session import get_engine, init_db


def test_phase2_database_tables_are_created() -> None:
    database_path = Path(".test_storage") / str(uuid4()) / "schema_test.db"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"

    asyncio.run(init_db(database_url))
    engine = get_engine(database_url)

    async def inspect_tables() -> set[str]:
        async with engine.connect() as connection:
            return await connection.run_sync(
                lambda sync_connection: set(inspect(sync_connection).get_table_names())
            )

    tables = asyncio.run(inspect_tables())

    assert UploadedFile.__tablename__ in tables
    assert ProcessingJob.__tablename__ in tables
    assert ExtractedRecord.__tablename__ in tables
    assert ValidationError.__tablename__ in tables
    assert AuditLog.__tablename__ in tables
    assert GeneratedReport.__tablename__ in tables

