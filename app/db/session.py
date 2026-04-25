from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
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

