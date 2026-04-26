from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import Settings, get_settings
from app.db.base import Base


@lru_cache
def get_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, echo=False, future=True)


@lru_cache
def get_sessionmaker(database_url: str) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_engine(database_url),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def init_db(database_url: str) -> None:
    engine = get_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        if database_url.startswith("sqlite"):
            await connection.run_sync(_ensure_sqlite_tenant_columns)


async def drop_db(database_url: str) -> None:
    engine = get_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


async def get_db_session(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncIterator[AsyncSession]:
    sessionmaker = get_sessionmaker(settings.database_url)
    async with sessionmaker() as session:
        yield session


def _ensure_sqlite_tenant_columns(connection) -> None:  # type: ignore[no-untyped-def]
    tenant_tables = [
        "uploaded_files",
        "processing_jobs",
        "extracted_records",
        "validation_errors",
        "audit_logs",
        "extraction_errors",
        "generated_reports",
    ]
    for table in tenant_tables:
        columns = {
            row[1]
            for row in connection.execute(text(f"PRAGMA table_info({table})")).fetchall()
        }
        if "organization_id" not in columns:
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN organization_id VARCHAR(36)"))
        if "workspace_id" not in columns:
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN workspace_id VARCHAR(36)"))
