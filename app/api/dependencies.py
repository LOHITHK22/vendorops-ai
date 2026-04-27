from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import (
    AuthContext,
    AuthenticationError,
    AuthorizationError,
    get_context_from_token,
    require_permission,
)
from app.db.session import get_db_session


def tenant_ids(context: AuthContext | None) -> tuple[UUID | None, UUID | None]:
    if context is None:
        return None, None
    return UUID(context.organization.id), UUID(context.workspace.id)


async def get_current_context(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorization: Annotated[str | None, Header()] = None,
) -> AuthContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token is required.",
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        return await get_context_from_token(session, token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


async def get_optional_context(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorization: Annotated[str | None, Header()] = None,
) -> AuthContext | None:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token is malformed.",
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        return await get_context_from_token(session, token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


def require_permission_dependency(permission: str):
    async def dependency(
        context: Annotated[AuthContext, Depends(get_current_context)],
    ) -> AuthContext:
        try:
            require_permission(context, permission)
        except AuthorizationError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            ) from exc
        return context

    return dependency
