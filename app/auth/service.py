from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import (
    create_access_token,
    hash_password,
    hash_token,
    session_expiry,
    verify_password,
)
from app.config.settings import Settings
from app.db.models import AuthSession, Membership, Organization, UserAccount, Workspace
from app.db.repositories import create_audit_log


class AuthenticationError(Exception):
    """Raised when credentials or bearer tokens are invalid."""


class AuthorizationError(Exception):
    """Raised when an authenticated user lacks a required permission."""


@dataclass(frozen=True)
class AuthContext:
    user: UserAccount
    organization: Organization
    workspace: Workspace
    membership: Membership


@dataclass(frozen=True)
class LoginResult:
    access_token: str
    expires_at: datetime
    context: AuthContext


ROLE_PERMISSIONS = {
    "owner": [
        "workspace:admin",
        "pipeline:write",
        "report:write",
        "analytics:read",
        "audit:read",
    ],
    "admin": ["pipeline:write", "report:write", "analytics:read", "audit:read"],
    "analyst": ["pipeline:write", "report:write", "analytics:read"],
    "viewer": ["analytics:read", "report:read"],
}


async def seed_default_identity(session: AsyncSession, settings: Settings) -> None:
    existing_user = await get_user_by_email(session, settings.demo_admin_email)
    if existing_user is not None:
        return

    organization = Organization(
        name=settings.default_organization_name,
        slug=slugify(settings.default_organization_name),
        plan="demo",
    )
    workspace = Workspace(
        organization=organization,
        name=settings.default_workspace_name,
        slug=slugify(settings.default_workspace_name),
    )
    user = UserAccount(
        email=settings.demo_admin_email.lower(),
        full_name="VendorOps Demo Admin",
        password_hash=hash_password(settings.demo_admin_password),
    )
    membership = Membership(
        user=user,
        organization=organization,
        workspace=workspace,
        role="owner",
    )
    session.add_all([organization, workspace, user, membership])
    await session.flush()
    await create_audit_log(
        session,
        actor="system",
        action="identity.demo_seeded",
        entity_type="organization",
        entity_id=organization.id,
        organization_id=organization.id,
        workspace_id=workspace.id,
        details={
            "user_email": user.email,
            "workspace_id": workspace.id,
            "role": membership.role,
        },
    )
    await session.commit()


async def authenticate_user(
    session: AsyncSession,
    settings: Settings,
    *,
    email: str,
    password: str,
) -> LoginResult:
    user = await get_user_by_email(session, email)
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password.")

    context = await get_primary_auth_context(session, user)
    token = create_access_token()
    expires_at = session_expiry(settings.auth_token_ttl_hours)
    auth_session = AuthSession(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=expires_at,
    )
    session.add(auth_session)
    await create_audit_log(
        session,
        actor=user.email,
        action="auth.login",
        entity_type="user_account",
        entity_id=user.id,
        organization_id=context.organization.id,
        workspace_id=context.workspace.id,
        details={
            "organization_id": context.organization.id,
            "workspace_id": context.workspace.id,
            "role": context.membership.role,
        },
    )
    await session.commit()
    return LoginResult(access_token=token, expires_at=expires_at, context=context)


async def get_context_from_token(session: AsyncSession, token: str) -> AuthContext:
    auth_session = await get_auth_session(session, token)
    if auth_session is None:
        raise AuthenticationError("Invalid or expired bearer token.")
    user = await session.get(UserAccount, auth_session.user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("Invalid or expired bearer token.")
    return await get_primary_auth_context(session, user)


def require_permission(context: AuthContext, permission: str) -> None:
    permissions = ROLE_PERMISSIONS.get(context.membership.role, [])
    if permission not in permissions:
        raise AuthorizationError(f"Role '{context.membership.role}' cannot perform '{permission}'.")


async def get_user_by_email(session: AsyncSession, email: str) -> UserAccount | None:
    result = await session.execute(
        select(UserAccount).where(UserAccount.email == email.strip().lower())
    )
    return result.scalar_one_or_none()


async def get_primary_auth_context(session: AsyncSession, user: UserAccount) -> AuthContext:
    result = await session.execute(
        select(Membership, Organization, Workspace)
        .join(Organization, Membership.organization_id == Organization.id)
        .join(Workspace, Membership.workspace_id == Workspace.id)
        .where(Membership.user_id == user.id)
        .order_by(Membership.created_at.asc())
    )
    row = result.first()
    if row is None:
        raise AuthenticationError("User is not assigned to a workspace.")
    membership, organization, workspace = row
    return AuthContext(
        user=user,
        organization=organization,
        workspace=workspace,
        membership=membership,
    )


async def get_auth_session(session: AsyncSession, token: str) -> AuthSession | None:
    now = datetime.now(UTC)
    result = await session.execute(
        select(AuthSession)
        .where(AuthSession.token_hash == hash_token(token))
        .where(AuthSession.revoked_at.is_(None))
    )
    auth_session = result.scalar_one_or_none()
    if auth_session is None:
        return None
    expires_at = auth_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= now:
        return None
    return auth_session


def permissions_for_role(role: str) -> list[str]:
    return ROLE_PERMISSIONS.get(role, [])


def slugify(value: str) -> str:
    return (
        value.lower()
        .replace("&", "and")
        .replace("/", "-")
        .replace(" ", "-")
        .replace("_", "-")
    )
