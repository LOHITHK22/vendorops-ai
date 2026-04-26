from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_context
from app.api.schemas import (
    AuthUserResponse,
    LoginRequest,
    LoginResponse,
    OrganizationSummaryResponse,
    WorkspaceSummaryResponse,
)
from app.auth.service import (
    AuthContext,
    AuthenticationError,
    authenticate_user,
    permissions_for_role,
)
from app.config.settings import Settings, get_settings
from app.db.session import get_db_session

router = APIRouter(prefix="/auth", tags=["auth"])


def to_auth_user_response(context: AuthContext) -> AuthUserResponse:
    role = context.membership.role
    return AuthUserResponse(
        user_id=UUID(context.user.id),
        email=context.user.email,
        full_name=context.user.full_name,
        organization=OrganizationSummaryResponse(
            organization_id=UUID(context.organization.id),
            name=context.organization.name,
            slug=context.organization.slug,
            plan=context.organization.plan,
        ),
        workspace=WorkspaceSummaryResponse(
            workspace_id=UUID(context.workspace.id),
            name=context.workspace.name,
            slug=context.workspace.slug,
            role=role,
        ),
        permissions=permissions_for_role(role),
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> LoginResponse:
    try:
        result = await authenticate_user(
            session,
            settings,
            email=request.email,
            password=request.password,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return LoginResponse(
        access_token=result.access_token,
        expires_at=result.expires_at,
        user=to_auth_user_response(result.context),
    )


@router.get("/me", response_model=AuthUserResponse)
async def get_me(
    context: Annotated[AuthContext, Depends(get_current_context)],
) -> AuthUserResponse:
    return to_auth_user_response(context)
