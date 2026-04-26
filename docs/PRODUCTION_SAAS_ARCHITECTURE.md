# VendorOps AI Production SaaS Architecture

VendorOps AI is designed as a production-first document intelligence platform. The MVP uses SQLite,
local storage, and mock extraction by default, but the application boundaries are intentionally shaped
for a sellable multi-tenant SaaS.

## Production Principles

- Tenant isolation is a first-class data boundary.
- Every file, extraction, validation finding, report, and administrative action is auditable.
- Storage is pluggable: local disk in MVP, object storage in production.
- Database access is repository/service based so SQLite can move to PostgreSQL without rewriting APIs.
- Extraction is provider-based so mock, OpenAI, OCR, and fallback strategies can be swapped.
- Analytics are derived from operational tables, not front-end-only vanity state.
- Cost monitoring is part of the product surface, not a billing afterthought.

## Target SaaS Modules

### Identity And Access

Production target:

- `users`
- `organizations`
- `workspaces`
- `memberships`
- `roles`
- `permissions`
- `api_keys`
- `sessions`

Access model:

- `owner`: billing, security, workspace, and member administration.
- `admin`: workspace settings, pipeline configuration, and report governance.
- `analyst`: document upload, extraction review, validation, and reporting.
- `viewer`: dashboard and report read-only access.

Every tenant-owned table should include `organization_id` and optionally `workspace_id`.

### Multi-Tenant Data Boundary

Production tables should be scoped like this:

```text
organizations
  workspaces
    uploaded_files
    processing_jobs
    extracted_records
    validation_errors
    extraction_errors
    generated_reports
    audit_logs
    usage_events
```

The API layer should resolve the active organization and workspace from the authenticated user context,
then inject those IDs into repository queries. No route should accept arbitrary tenant IDs without an
authorization check.

### Storage

MVP:

- Local filesystem for uploads and generated reports.

Production:

- S3, Azure Blob Storage, or GCS.
- Server-side encryption.
- Pre-signed upload/download URLs.
- Virus scanning before parsing.
- File size and MIME validation.
- Retention policies per workspace.

### Database

MVP:

- SQLite through SQLAlchemy async.

Production:

- PostgreSQL.
- Alembic migrations.
- Row-level tenant scoping.
- Indexes on `organization_id`, `workspace_id`, `created_at`, `status`, `record_type`, and `vendor_name`.
- Read replicas for analytics-heavy workloads when needed.

### OCR And Document Splitting

Production extraction pipeline:

```text
Upload
  -> MIME validation
  -> object storage
  -> parser detection
  -> text PDF parser
  -> OCR fallback for scanned pages
  -> document splitter
  -> document-type classifier
  -> document-specific LLM prompt
  -> strict JSON schema
  -> validation and dedupe
  -> storage
  -> reports and analytics
```

OCR engines:

- AWS Textract, Azure Document Intelligence, Google Document AI, or Tesseract for local fallback.

Splitting strategy:

- Detect invoice/contract/report boundaries by page markers, invoice IDs, vendor names, dates, and
  semantic classifier results.
- Store parent-child file relationships for multi-document PDFs.

### LLM Extraction

Document-specific prompt families:

- Invoice extraction
- Contract obligation extraction
- Vendor onboarding extraction
- Email/ticket classification
- CSV normalization
- Report summarization

Production controls:

- Strict JSON schema output.
- Source evidence required for high-value fields.
- Retry on malformed JSON and provider transient errors.
- Confidence threshold routing to manual review.
- Prompt/version metadata stored with every extraction.
- Cost and token usage captured as `usage_events`.

### Validation And Deduplication

Validation engine should support:

- Required field checks.
- Type and range checks.
- Cross-field checks, such as due date after invoice date.
- Duplicate detection by hash, vendor, document ID, amount, and date.
- Tenant-level uniqueness policies.
- Severity levels: `info`, `warning`, `error`, `blocking`.

### Compliance And Audit

Audit events must cover:

- Login/logout.
- File upload/download/delete.
- Extraction start/complete/failure.
- Manual field edits.
- Validation overrides.
- Report generation/download.
- Role and permission changes.
- API key creation/revocation.

Audit logs should be immutable in production and exportable for customer review.

### Usage And Cost Tracking

Track usage by organization, workspace, provider, model, pipeline, and document type:

- Uploaded bytes.
- Parsed pages.
- OCR pages.
- Input tokens.
- Output tokens.
- LLM cost.
- Retry count.
- Report count.

The current analytics dashboard already includes estimated LLM cost and mock-vs-billable records. In
production, this should use provider usage metadata instead of estimates.

### Deployment

Current deployment foundation:

- Backend Dockerfile.
- Frontend Dockerfile.
- Docker Compose.
- Nginx frontend/API proxy.
- GitHub Actions CI.

Production target:

- Managed PostgreSQL.
- Managed object storage.
- Secret manager.
- Container platform such as Render, Fly.io, ECS, Azure Container Apps, or Kubernetes.
- HTTPS termination.
- Health checks and structured logs.
- Error monitoring through Sentry/OpenTelemetry.

## Implementation Order

1. Authentication, organizations, workspaces, memberships, and RBAC.
2. PostgreSQL plus Alembic migrations.
3. Tenant-scoped repositories and API dependencies.
4. Cloud object storage provider abstraction.
5. OCR and multi-document splitting.
6. Usage events and real provider cost tracking.
7. Admin settings and workspace controls.
8. Compliance exports and audit hardening.
