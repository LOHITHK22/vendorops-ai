# ruff: noqa: E501
"""Initial production schema.

Revision ID: 202604270001
Revises:
Create Date: 2026-04-27 00:01:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "202604270001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if _legacy_schema_exists():
        return

    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("plan", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_organizations_slug"), "organizations", ["slug"], unique=False)

    op.create_table(
        "user_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_user_accounts_email"), "user_accounts", ["email"], unique=False)

    op.create_table(
        "uploaded_files",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=True),
        sa.Column("workspace_id", sa.String(length=36), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=32), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_files_tenant_created", "uploaded_files", ["organization_id", "workspace_id", "created_at"])
    op.create_index(op.f("ix_uploaded_files_organization_id"), "uploaded_files", ["organization_id"], unique=False)
    op.create_index(op.f("ix_uploaded_files_sha256_hash"), "uploaded_files", ["sha256_hash"], unique=False)
    op.create_index(op.f("ix_uploaded_files_workspace_id"), "uploaded_files", ["workspace_id"], unique=False)

    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_workspace_org_slug", "workspaces", ["organization_id", "slug"])
    op.create_index(op.f("ix_workspaces_organization_id"), "workspaces", ["organization_id"], unique=False)
    op.create_index(op.f("ix_workspaces_slug"), "workspaces", ["slug"], unique=False)

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_auth_sessions_token_hash"), "auth_sessions", ["token_hash"], unique=False)
    op.create_index(op.f("ix_auth_sessions_user_id"), "auth_sessions", ["user_id"], unique=False)

    op.create_table(
        "memberships",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_membership_user_workspace", "memberships", ["user_id", "workspace_id"])
    op.create_index(op.f("ix_memberships_organization_id"), "memberships", ["organization_id"], unique=False)
    op.create_index(op.f("ix_memberships_user_id"), "memberships", ["user_id"], unique=False)
    op.create_index(op.f("ix_memberships_workspace_id"), "memberships", ["workspace_id"], unique=False)

    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=True),
        sa.Column("workspace_id", sa.String(length=36), nullable=True),
        sa.Column("file_id", sa.String(length=36), nullable=False),
        sa.Column("pipeline", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["file_id"], ["uploaded_files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_jobs_file_pipeline", "processing_jobs", ["file_id", "pipeline"])
    op.create_index("idx_jobs_tenant_status", "processing_jobs", ["organization_id", "workspace_id", "status"])
    op.create_index(op.f("ix_processing_jobs_file_id"), "processing_jobs", ["file_id"], unique=False)
    op.create_index(op.f("ix_processing_jobs_organization_id"), "processing_jobs", ["organization_id"], unique=False)
    op.create_index(op.f("ix_processing_jobs_workspace_id"), "processing_jobs", ["workspace_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=True),
        sa.Column("workspace_id", sa.String(length=36), nullable=True),
        sa.Column("actor", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_organization_id"), "audit_logs", ["organization_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_workspace_id"), "audit_logs", ["workspace_id"], unique=False)

    op.create_table(
        "extracted_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=True),
        sa.Column("workspace_id", sa.String(length=36), nullable=True),
        sa.Column("file_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=True),
        sa.Column("record_type", sa.String(length=50), nullable=False),
        sa.Column("vendor_name", sa.String(length=255), nullable=True),
        sa.Column("external_reference", sa.String(length=255), nullable=True),
        sa.Column("normalized_payload", sa.JSON(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["file_id"], ["uploaded_files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["processing_jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_records_tenant_created", "extracted_records", ["organization_id", "workspace_id", "created_at"])
    op.create_index("idx_records_vendor_type", "extracted_records", ["vendor_name", "record_type"])
    op.create_index(op.f("ix_extracted_records_external_reference"), "extracted_records", ["external_reference"], unique=False)
    op.create_index(op.f("ix_extracted_records_file_id"), "extracted_records", ["file_id"], unique=False)
    op.create_index(op.f("ix_extracted_records_job_id"), "extracted_records", ["job_id"], unique=False)
    op.create_index(op.f("ix_extracted_records_organization_id"), "extracted_records", ["organization_id"], unique=False)
    op.create_index(op.f("ix_extracted_records_record_type"), "extracted_records", ["record_type"], unique=False)
    op.create_index(op.f("ix_extracted_records_vendor_name"), "extracted_records", ["vendor_name"], unique=False)
    op.create_index(op.f("ix_extracted_records_workspace_id"), "extracted_records", ["workspace_id"], unique=False)

    op.create_table(
        "extraction_errors",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=True),
        sa.Column("workspace_id", sa.String(length=36), nullable=True),
        sa.Column("job_id", sa.String(length=36), nullable=True),
        sa.Column("file_id", sa.String(length=36), nullable=True),
        sa.Column("stage", sa.String(length=100), nullable=False),
        sa.Column("error_type", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("retryable", sa.Boolean(), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["file_id"], ["uploaded_files.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["processing_jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_extraction_errors_file_id"), "extraction_errors", ["file_id"], unique=False)
    op.create_index(op.f("ix_extraction_errors_job_id"), "extraction_errors", ["job_id"], unique=False)
    op.create_index(op.f("ix_extraction_errors_organization_id"), "extraction_errors", ["organization_id"], unique=False)
    op.create_index(op.f("ix_extraction_errors_workspace_id"), "extraction_errors", ["workspace_id"], unique=False)

    op.create_table(
        "generated_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=True),
        sa.Column("workspace_id", sa.String(length=36), nullable=True),
        sa.Column("report_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generated_reports_organization_id"), "generated_reports", ["organization_id"], unique=False)
    op.create_index(op.f("ix_generated_reports_report_type"), "generated_reports", ["report_type"], unique=False)
    op.create_index(op.f("ix_generated_reports_workspace_id"), "generated_reports", ["workspace_id"], unique=False)

    op.create_table(
        "validation_errors",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=True),
        sa.Column("workspace_id", sa.String(length=36), nullable=True),
        sa.Column("record_id", sa.String(length=36), nullable=True),
        sa.Column("job_id", sa.String(length=36), nullable=True),
        sa.Column("field_name", sa.String(length=255), nullable=True),
        sa.Column("error_type", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["processing_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["record_id"], ["extracted_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_validation_errors_job_id"), "validation_errors", ["job_id"], unique=False)
    op.create_index(op.f("ix_validation_errors_organization_id"), "validation_errors", ["organization_id"], unique=False)
    op.create_index(op.f("ix_validation_errors_record_id"), "validation_errors", ["record_id"], unique=False)
    op.create_index(op.f("ix_validation_errors_workspace_id"), "validation_errors", ["workspace_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_validation_errors_workspace_id"), table_name="validation_errors")
    op.drop_index(op.f("ix_validation_errors_record_id"), table_name="validation_errors")
    op.drop_index(op.f("ix_validation_errors_organization_id"), table_name="validation_errors")
    op.drop_index(op.f("ix_validation_errors_job_id"), table_name="validation_errors")
    op.drop_table("validation_errors")
    op.drop_index(op.f("ix_generated_reports_workspace_id"), table_name="generated_reports")
    op.drop_index(op.f("ix_generated_reports_report_type"), table_name="generated_reports")
    op.drop_index(op.f("ix_generated_reports_organization_id"), table_name="generated_reports")
    op.drop_table("generated_reports")
    op.drop_index(op.f("ix_extraction_errors_workspace_id"), table_name="extraction_errors")
    op.drop_index(op.f("ix_extraction_errors_organization_id"), table_name="extraction_errors")
    op.drop_index(op.f("ix_extraction_errors_job_id"), table_name="extraction_errors")
    op.drop_index(op.f("ix_extraction_errors_file_id"), table_name="extraction_errors")
    op.drop_table("extraction_errors")
    op.drop_index(op.f("ix_extracted_records_workspace_id"), table_name="extracted_records")
    op.drop_index(op.f("ix_extracted_records_vendor_name"), table_name="extracted_records")
    op.drop_index(op.f("ix_extracted_records_record_type"), table_name="extracted_records")
    op.drop_index(op.f("ix_extracted_records_organization_id"), table_name="extracted_records")
    op.drop_index(op.f("ix_extracted_records_job_id"), table_name="extracted_records")
    op.drop_index(op.f("ix_extracted_records_file_id"), table_name="extracted_records")
    op.drop_index(op.f("ix_extracted_records_external_reference"), table_name="extracted_records")
    op.drop_index("idx_records_vendor_type", table_name="extracted_records")
    op.drop_index("idx_records_tenant_created", table_name="extracted_records")
    op.drop_table("extracted_records")
    op.drop_index(op.f("ix_audit_logs_workspace_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_organization_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_processing_jobs_workspace_id"), table_name="processing_jobs")
    op.drop_index(op.f("ix_processing_jobs_organization_id"), table_name="processing_jobs")
    op.drop_index(op.f("ix_processing_jobs_file_id"), table_name="processing_jobs")
    op.drop_index("idx_jobs_tenant_status", table_name="processing_jobs")
    op.drop_index("idx_jobs_file_pipeline", table_name="processing_jobs")
    op.drop_table("processing_jobs")
    op.drop_index(op.f("ix_memberships_workspace_id"), table_name="memberships")
    op.drop_index(op.f("ix_memberships_user_id"), table_name="memberships")
    op.drop_index(op.f("ix_memberships_organization_id"), table_name="memberships")
    op.drop_index("idx_membership_user_workspace", table_name="memberships")
    op.drop_table("memberships")
    op.drop_index(op.f("ix_auth_sessions_user_id"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_token_hash"), table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index(op.f("ix_workspaces_slug"), table_name="workspaces")
    op.drop_index(op.f("ix_workspaces_organization_id"), table_name="workspaces")
    op.drop_index("idx_workspace_org_slug", table_name="workspaces")
    op.drop_table("workspaces")
    op.drop_index(op.f("ix_uploaded_files_workspace_id"), table_name="uploaded_files")
    op.drop_index(op.f("ix_uploaded_files_sha256_hash"), table_name="uploaded_files")
    op.drop_index(op.f("ix_uploaded_files_organization_id"), table_name="uploaded_files")
    op.drop_index("idx_files_tenant_created", table_name="uploaded_files")
    op.drop_table("uploaded_files")
    op.drop_index(op.f("ix_user_accounts_email"), table_name="user_accounts")
    op.drop_table("user_accounts")
    op.drop_index(op.f("ix_organizations_slug"), table_name="organizations")
    op.drop_table("organizations")


def _legacy_schema_exists() -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "uploaded_files" not in tables:
        return False
    if bind.dialect.name == "sqlite":
        _ensure_legacy_sqlite_tenant_columns(bind)
    return True


def _ensure_legacy_sqlite_tenant_columns(bind) -> None:
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
        rows = bind.execute(sa.text(f"PRAGMA table_info({table})")).fetchall()
        if not rows:
            continue
        columns = {row[1] for row in rows}
        if "organization_id" not in columns:
            op.add_column(table, sa.Column("organization_id", sa.String(length=36)))
        if "workspace_id" not in columns:
            op.add_column(table, sa.Column("workspace_id", sa.String(length=36)))
