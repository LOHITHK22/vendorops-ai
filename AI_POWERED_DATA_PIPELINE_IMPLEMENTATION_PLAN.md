# AI-Powered Data Pipeline Implementation Plan

Research date: April 25, 2026

## Sources Used

- OpenAI Structured Outputs: https://platform.openai.com/docs/guides/structured-outputs
- OpenAI Responses API structured output reference: https://platform.openai.com/docs/api-reference/responses/create
- Prefect workflow/retry docs: https://docs.prefect.io/v3/how-to-guides/workflows/retries
- Prefect overview: https://docs.prefect.io/
- FastAPI package/project description: https://pypi.org/project/fastapi/
- PostgreSQL JSON/JSONB docs: https://www.postgresql.org/docs/current/static/datatype-json.html
- SQLAlchemy asyncio docs: https://docs.sqlalchemy.org/20/orm/extensions/asyncio.html
- OpenTelemetry docs: https://opentelemetry.io/docs/
- Redis Streams docs: https://redis.io/docs/latest/develop/data-types/streams/
- Streamlit docs: https://docs.streamlit.io/
- Apache Superset docs: https://superset.apache.org/
- PyMuPDF docs: https://pymupdf.readthedocs.io/en/latest/the-basics.html
- pdfplumber GitHub/docs: https://github.com/jsvine/pdfplumber
- Contract extraction market/pricing reference: https://www.contractdataextraction.com/
- Contract OCR market signal: https://ventureworld.org/press-release/2026-04-01/31140/contractocr-com-launches-ai-platform-for-contract-data-extraction

## 1. Project Ideas

### Idea 1: VendorOps AI - Contract and Invoice Intelligence Pipeline

Problem statement:
Small and mid-market finance/procurement teams receive contracts, invoices, renewal notices, vendor emails, and CSV exports. Key terms live in scattered documents, causing missed renewals, manual AP checks, duplicate invoices, late payments, and poor vendor visibility.

Target users/businesses:
SMB finance teams, accounting firms, procurement teams, fractional CFOs, operations managers, managed service providers.

Why it matters:
Manual document review is expensive and error-prone. Existing tools show that businesses pay for contract data extraction, API access, compliance controls, and spreadsheet/API exports. A credible system must prove auditability, source-grounded extraction, validation, reporting, and operational reliability.

Input data sources:
Vendor contracts, invoices, email attachments, purchase orders, payment CSVs, vendor master CSVs, renewal notices.

Output deliverables:
Structured vendor, contract, invoice, obligation, renewal, and exception records; validation errors; spend reports; renewal calendar; CSV/XLSX/PDF reports; dashboard; REST API.

Business value:
Find renewal deadlines, detect invoice-contract mismatches, reduce manual data entry, produce audit-ready vendor records, and give finance leadership a live vendor-risk dashboard.

Monetization potential:
High. Package as a document intelligence setup for accounting/procurement teams. Charge setup plus monthly support, or price by document volume.

### Idea 2: Claims Intake AI Pipeline for Insurance/Healthcare Operations

Problem statement:
Claims teams receive PDFs, forms, emails, photos, medical invoices, and CSV status exports. Intake data must be extracted, validated, classified, and routed.

Target users/businesses:
Small insurers, TPAs, clinics, billing services, medical/legal admin teams.

Why it matters:
Claims intake has high volume, high compliance risk, and measurable cycle-time savings.

Input data sources:
Claim forms, scanned PDFs, emails, images, CSV exports, billing documents.

Output deliverables:
Claim records, missing-information reports, fraud/risk flags, SLA dashboard, case summaries.

Business value:
Faster intake, fewer missed fields, better triage, operational reporting.

Monetization potential:
Strong but higher compliance burden. Healthcare data brings HIPAA/security expectations, which is harder for a portfolio MVP.

### Idea 3: SupportOps AI Analytics Pipeline

Problem statement:
Companies have support tickets, chat transcripts, product feedback, bug reports, and CSV exports. They need structured issue taxonomy, sentiment, root causes, SLA risks, and weekly executive reports.

Target users/businesses:
B2B SaaS support teams, product managers, customer success teams.

Why it matters:
Support data is noisy and high-volume. LLM extraction can turn conversations into structured product and operations signals.

Input data sources:
Zendesk/Freshdesk exports, Intercom chats, emails, CSV tickets, call transcripts.

Output deliverables:
Topic clusters, escalation flags, churn signals, SLA reports, trend dashboards, product feedback summaries.

Business value:
Better triage, product roadmap insights, reduced manual reporting.

Monetization potential:
Medium-high. Crowded space, but easier demo data. Less obviously "data engineering" than document pipelines unless you emphasize scale and orchestration.

### Best Idea

Pick Idea 1: VendorOps AI - Contract and Invoice Intelligence Pipeline.

Why:
It combines unstructured document extraction, cross-document validation, relational data modeling, reporting, audit logs, and real monetization. It is specific enough to build and sell, but broad enough to demonstrate data engineering, backend engineering, LLM orchestration, and AI product thinking.

## 2. Final Project Recommendation

Build: VendorOps AI, an AI-powered vendor document intelligence platform.

The system ingests contracts, invoices, purchase orders, emails, and vendor CSVs. It extracts structured records using LLM Structured Outputs, validates them against schemas and business rules, stores raw files and normalized data, generates finance/procurement reports, exposes a dashboard/API, and tracks every job with audit logs, retries, source citations, and validation results.

Core demo scenario:
Upload 100 vendor documents. The app extracts vendor names, contract values, renewal dates, termination notice periods, invoice line items, invoice totals, payment terms, tax, currency, and obligations. It flags invoices that exceed contract terms, contracts expiring within 90 days, duplicate invoices, missing W-9/compliance fields, and low-confidence extractions.

## 3. Professional Design Document

### Title

VendorOps AI: Production-Grade AI Data Pipeline for Vendor Contracts, Invoices, and Finance Reporting

### Problem Statement

Finance and procurement teams rely on contracts, invoices, emails, and spreadsheet exports that do not share a clean structure. Important operational fields are buried in PDFs and attachments. Manual review causes slow reporting, duplicate work, missed renewals, payment mistakes, and weak audit trails.

### Goals

- Ingest PDFs, emails, CSVs, and images.
- Parse document text and metadata.
- Extract structured vendor, contract, invoice, obligation, and payment fields.
- Validate outputs using schema, business rules, cross-document checks, and source evidence.
- Store raw files, parsed text, extracted records, validation results, jobs, errors, reports, and audit logs.
- Expose a REST API and dashboard.
- Generate automated weekly/monthly reports.
- Provide production features: retries, idempotency, observability, audit logs, access controls, and cost tracking.

### Non-Goals

- Replacing a full ERP, CLM, or AP automation suite.
- Providing legal advice.
- Fully automated payment execution.
- Training a custom foundation model.
- Supporting every possible document type in the MVP.

### Users

- Finance manager: wants invoice exceptions and monthly vendor spend.
- Procurement lead: wants renewal and obligation visibility.
- Accounting firm: wants client document processing.
- Operations leader: wants a clean dashboard and reports.
- Developer/integrator: wants API/webhooks.

### Functional Requirements

- Upload documents via API and dashboard.
- Support PDFs, CSVs, email `.eml`, images, and simple text files.
- Classify document type.
- Extract structured JSON with confidence and source spans.
- Validate required fields, types, dates, totals, and cross-document consistency.
- Track processing job status.
- Allow human review/correction.
- Generate reports by vendor, month, contract, invoice, risk, and renewal window.
- Export CSV, XLSX, PDF, and JSON.
- Provide audit trail for every extraction, validation, user correction, and report.

### Non-Functional Requirements

- Idempotent processing using file hash and job keys.
- Recoverable pipeline tasks.
- Observability across API, worker, LLM calls, validation, and DB writes.
- Secure object storage and database access.
- P95 upload request under 2 seconds, with async processing after upload.
- Process 100 documents in an MVP batch without manual intervention.
- Store source evidence for extracted fields.
- Redact sensitive values in logs.

### System Architecture

Use FastAPI for the API, Prefect for orchestration, Redis Streams or Celery/Redis for async job dispatch, PostgreSQL for normalized data plus JSONB extraction payloads, S3-compatible object storage for raw files, OpenAI Structured Outputs for schema-constrained extraction, Pydantic for app-level validation, and Streamlit or React for the dashboard.

### Data Flow

1. User uploads file.
2. API stores file in object storage and creates `uploaded_files` and `processing_jobs`.
3. Queue emits `document.uploaded`.
4. Worker parses document text/tables/images.
5. Classifier identifies document type.
6. Chunker creates extraction chunks with page and character offsets.
7. LLM extracts structured JSON with source citations.
8. Validator checks schema, field rules, math totals, and cross-document consistency.
9. Database stores normalized records, raw extraction JSON, evidence spans, validation results, errors, and audit events.
10. Reporting service generates scheduled reports.
11. Dashboard/API exposes status, records, exceptions, and reports.
12. Monitoring collects traces, metrics, logs, LLM token cost, and error rates.

### Tech Stack

- Backend: Python, FastAPI.
- ORM/database: SQLAlchemy 2.x async, Alembic, PostgreSQL.
- Orchestration: Prefect for pipeline flows and retries.
- Queue: Redis Streams for MVP, Celery/Redis if task distribution needs grow.
- Object storage: MinIO locally, S3 in production.
- LLM provider: OpenAI Responses API with Structured Outputs.
- Validation: Pydantic, JSON Schema, custom business-rule validators.
- Parsing: PyMuPDF for text extraction, pdfplumber for tables, Tesseract/AWS Textract optional for scanned docs, Python email parser for `.eml`, pandas for CSV.
- Dashboard: Streamlit for fast portfolio MVP, React/Next.js for monetizable product.
- Reporting: pandas, Jinja2 templates, WeasyPrint or Playwright PDF export, XLSX export.
- Monitoring: OpenTelemetry, Prometheus, Grafana, Loki, Sentry.
- Deployment: Docker Compose for local, Render/Fly.io/AWS ECS for MVP SaaS, Kubernetes later.

### Database Schema

Core entities:
`uploaded_files`, `processing_jobs`, `parsed_documents`, `vendors`, `contracts`, `invoices`, `extracted_records`, `validation_results`, `extraction_errors`, `audit_logs`, `generated_reports`, `llm_calls`, `source_evidence`.

### API Design

Core REST resources:
`/files`, `/jobs`, `/records`, `/validation-errors`, `/reports`, `/audit-logs`, `/health`.

### LLM Extraction Strategy

- Use deterministic document-type-specific schemas.
- Run document classification first.
- Use OpenAI Structured Outputs with strict JSON schema where possible.
- Extract in chunks, then reconcile into one document-level record.
- Require source citations for every important field.
- Store confidence, evidence text, page number, and extraction rationale.
- Never trust LLM output directly. Validate and mark review status.

### Prompting Strategy

- System prompt defines role, schema discipline, source-grounding, and uncertainty handling.
- User prompt includes document type, extraction schema summary, business rules, and chunk text.
- Instruct the model to return `null` when evidence is missing.
- Ask for `evidence_quote`, `page_number`, `confidence`, and `needs_review`.
- Use few-shot examples only for tricky fields such as termination notice periods or invoice totals.

### Validation Strategy

- Pydantic type validation.
- Required field validation by document type.
- Date normalization and timezone handling.
- Currency normalization.
- Invoice math: subtotal + tax + fees - discount = total.
- Duplicate invoice detection by vendor, invoice number, amount, and date.
- Contract-invoice matching by vendor, payment terms, contract value, currency, and effective dates.
- Evidence verification: extracted value should appear or be inferable from cited source text.
- Human review queue for low confidence or failed rules.

### Error Handling

- Separate parse errors, classification errors, LLM errors, schema errors, validation errors, storage errors, and report-generation errors.
- Store all errors in `extraction_errors`.
- Mark job status as `failed`, `retrying`, `completed_with_errors`, or `requires_review`.
- Do not lose raw files if downstream processing fails.

### Retry Strategy

- Retry transient parser/storage/LLM/network failures with exponential backoff and jitter.
- Do not retry deterministic validation failures.
- For bad LLM JSON/schema mismatch, retry with a repair prompt and lower temperature.
- For low confidence, send to human review rather than infinite retries.
- Use idempotency keys to avoid duplicate records on retry.

### Observability and Logging

- Correlate API request ID, job ID, file ID, flow run ID, and LLM call ID.
- Capture task duration, retry count, queue latency, token usage, model, cost estimate, parse success rate, extraction confidence, validation failure type, and report generation time.
- Use OpenTelemetry traces for API and worker flows.
- Use structured logs with redacted sensitive fields.
- Build a dashboard for pipeline throughput, failures, LLM spend, and review backlog.

### Security and Privacy

- Encrypt files at rest in S3/MinIO and database disk storage.
- Use TLS in production.
- Store secrets in environment manager or cloud secrets manager.
- Role-based access: admin, reviewer, viewer, API client.
- Audit every file view, extraction correction, report download, and API key use.
- Redact PII/tax IDs in logs.
- Optional retention policy: delete raw files after N days while keeping structured metadata.
- Add tenant isolation before monetization.

### Scalability Plan

- Start with one API container, one worker, one Postgres, one Redis, one MinIO.
- Scale workers horizontally by queue depth.
- Partition large documents by page/chunk.
- Use batch LLM processing where latency is not critical.
- Cache parsed text and embeddings.
- Add tenant-level rate limits.
- Move reports to async jobs.
- Add read replicas and materialized reporting views when needed.

### Cost Optimization

- Parse text locally before using vision models.
- Classify cheaply before heavy extraction.
- Use smaller models for classification and simple extraction.
- Use larger models only for complex contracts and reconciliation.
- Skip LLM calls for CSVs and clean invoice formats when deterministic parsing works.
- Cache extraction by file hash.
- Store prompt/completion token usage per call.
- Let users configure retention and report schedules.

### Testing Strategy

- Unit tests for parsers, chunkers, validators, schema models, and report builders.
- Golden-file tests for sample contracts and invoices.
- Integration tests with Postgres, Redis, and MinIO.
- LLM contract tests using mocked responses.
- End-to-end test: upload sample documents, run pipeline, verify records, validation, and report output.
- Load test: 100 documents batch.
- Security tests: unauthorized access, tenant isolation, sensitive log redaction.

### Deployment Plan

- Local: Docker Compose with API, worker, Postgres, Redis, MinIO, Streamlit, Grafana.
- MVP cloud: Render/Fly.io/Railway for API/worker, managed Postgres, object storage.
- Production: AWS ECS/Fargate or Kubernetes, RDS Postgres, S3, ElastiCache Redis, CloudWatch/Grafana/Sentry.
- CI/CD: GitHub Actions for lint, tests, Docker build, migrations, deploy.

### Future Improvements

- Human-in-the-loop review UI.
- Vendor portal.
- ERP/QuickBooks/NetSuite integrations.
- Email inbox ingestion.
- Webhooks.
- Multi-tenant SaaS billing.
- Contract clause risk scoring.
- RAG search over vendor documents.
- Active-learning dataset from reviewer corrections.

## 4. Architecture

Components:

- Ingestion layer: accepts API uploads, dashboard uploads, email inbox ingestion, and CSV imports.
- File parser layer: extracts text, tables, metadata, page numbers, and OCR text where needed.
- LLM extraction layer: classifies document type and extracts fields into strict JSON schemas.
- Validation layer: checks schema, math, business rules, duplicates, and source evidence.
- Data storage layer: stores raw files in object storage and structured records in PostgreSQL.
- Reporting layer: creates renewal, spend, exception, and audit reports.
- Dashboard/API layer: exposes upload, status, records, review, and report workflows.
- Monitoring layer: tracks logs, metrics, traces, token cost, errors, and audit events.

ASCII diagram:

```text
             +-------------------+
             | Dashboard / API   |
             | FastAPI/Streamlit |
             +---------+---------+
                       |
                       v
             +-------------------+        +------------------+
             | Ingestion Layer   +------->| Object Storage   |
             | upload/email/csv  |        | S3 / MinIO       |
             +---------+---------+        +------------------+
                       |
                       v
             +-------------------+
             | Queue             |
             | Redis Streams     |
             +---------+---------+
                       |
                       v
             +-------------------+
             | Orchestrator      |
             | Prefect flows     |
             +---------+---------+
                       |
       +---------------+----------------+
       v                                v
+--------------+                +---------------+
| Parser Layer |                | Audit Logging |
| PDF/CSV/EML  |                | events        |
+------+-------+                +-------+-------+
       |                                |
       v                                v
+--------------+    +-------------+    +----------------+
| LLM Extract  +--->| Validation  +--->| PostgreSQL     |
| JSON schema  |    | rules/evidence   | records/jsonb  |
+------+-------+    +------+------+    +-------+--------+
       |                   |                   |
       v                   v                   v
+--------------+    +-------------+    +----------------+
| LLM Call Log |    | Review Queue|    | Reporting      |
| cost/tokens  |    | exceptions  |    | PDF/XLSX/CSV   |
+--------------+    +-------------+    +-------+--------+
                                                |
                                                v
                                      +------------------+
                                      | Monitoring       |
                                      | OTel/Grafana     |
                                      +------------------+
```

## 5. Recommended Tech Stack

| Area | Recommendation | Why |
|---|---|---|
| Backend | FastAPI | Python-native, async-friendly, OpenAPI docs, strong fit for data/LLM apps. |
| LLM | OpenAI Responses API with Structured Outputs | Schema-constrained extraction reduces malformed JSON and simplifies downstream validation. |
| Orchestration | Prefect | Pythonic workflows, retries, state tracking, monitoring, easy local-to-cloud path. |
| Vector DB | pgvector later, not MVP | Only needed for semantic document search or RAG. Start without it. |
| Relational DB | PostgreSQL | Reliable relational modeling plus JSONB for raw extraction payloads and flexible querying. |
| Object Storage | MinIO locally, S3 in production | Keeps raw documents out of the DB and mirrors production architecture. |
| Queue | Redis Streams | Lightweight async events and consumer groups; good MVP complexity/value ratio. |
| Dashboard | Streamlit MVP, React later | Streamlit is fastest for a data portfolio dashboard; React is better for SaaS polish. |
| Reports | pandas + Jinja2 + WeasyPrint/Playwright + openpyxl | Clean CSV/XLSX/PDF generation. |
| Monitoring | OpenTelemetry + Grafana + Loki + Sentry | Traces, metrics, logs, and app errors. |
| Deployment | Docker Compose, then AWS ECS/Fargate | Simple local demo, credible production path. |

## 6. Implementation Roadmap

### Phase 1: MVP

Features:
- Upload PDF/CSV files.
- Store files in MinIO.
- Parse PDF text and CSV rows.
- Extract invoice and contract fields with LLM.
- Store records in Postgres.
- Basic API for upload, job status, records.

Files/modules:
- `app/api/routes/files.py`
- `app/api/routes/jobs.py`
- `app/ingestion/storage.py`
- `app/parsers/pdf_parser.py`
- `app/parsers/csv_parser.py`
- `app/extraction/schemas.py`
- `app/extraction/llm_client.py`
- `app/db/models.py`
- `app/db/session.py`
- `app/workers/pipeline.py`

Difficulty:
Medium.

Expected output:
User uploads 5 sample documents and sees structured invoice/contract records.

Testing checklist:
- Upload succeeds.
- Duplicate upload detected by hash.
- PDF text parsed.
- LLM JSON validates.
- Records saved.
- Job status transitions correctly.

### Phase 2: Reliable Pipeline

Features:
- Prefect orchestration.
- Redis queue.
- Retries with backoff.
- Idempotency.
- Error tables.
- Validation engine.
- Source evidence storage.

Files/modules:
- `app/orchestration/flows.py`
- `app/queue/redis_streams.py`
- `app/validation/rules.py`
- `app/validation/evidence.py`
- `app/db/repositories.py`
- `app/observability/logging.py`
- `app/observability/tracing.py`

Difficulty:
Medium-hard.

Expected output:
Batch processing can survive transient LLM/parser failures and show validation failures clearly.

Testing checklist:
- Simulated LLM timeout retries.
- Bad JSON handled.
- Validation failure does not crash job.
- Re-running same job does not duplicate records.
- Audit event emitted for each state transition.

### Phase 3: Dashboard and Reporting

Features:
- Streamlit dashboard.
- Vendor spend summary.
- Expiring contracts report.
- Invoice exception report.
- CSV/XLSX/PDF report generation.
- Report download API.

Files/modules:
- `dashboard/app.py`
- `app/reports/builders.py`
- `app/reports/templates/renewals.html`
- `app/reports/templates/exceptions.html`
- `app/api/routes/reports.py`

Difficulty:
Medium.

Expected output:
A polished dashboard showing pipeline health, records, validation errors, and downloadable reports.

Testing checklist:
- Report generated from seeded data.
- Download endpoint works.
- Dashboard filters by vendor/date/status.
- Report job creates audit event.

### Phase 4: Production-Grade Features

Features:
- Authentication.
- Role-based access.
- OpenTelemetry instrumentation.
- LLM cost tracking.
- Human review queue.
- File retention policy.
- Email ingestion.
- Docker Compose full stack.

Files/modules:
- `app/auth/`
- `app/review/`
- `app/email_ingestion/`
- `deploy/docker-compose.yml`
- `deploy/Dockerfile.api`
- `deploy/Dockerfile.worker`
- `deploy/grafana/`

Difficulty:
Hard.

Expected output:
Credible production demo with monitoring, security basics, and review workflow.

Testing checklist:
- Unauthorized users blocked.
- Reviewer can edit extracted fields.
- Changes create audit logs.
- Trace ID links API request to worker job.
- Sensitive values redacted in logs.

### Phase 5: Monetizable Version

Features:
- Multi-tenancy.
- API keys.
- Webhooks.
- Billing tiers.
- Admin dashboard.
- QuickBooks/NetSuite/Google Drive integration stubs.
- Customer onboarding docs.

Files/modules:
- `app/tenancy/`
- `app/api/routes/api_keys.py`
- `app/api/routes/webhooks.py`
- `app/billing/`
- `docs/customer_onboarding.md`
- `docs/security_overview.md`

Difficulty:
Hard.

Expected output:
Sellable pilot product for one niche: accounting firms or SMB procurement teams.

Testing checklist:
- Tenant A cannot access Tenant B data.
- API keys scoped.
- Webhook retries on failure.
- Usage metering works.
- Billing limits enforced.

## 7. Folder Structure

```text
vendorops-ai/
  app/
    api/
      main.py
      dependencies.py
      routes/
        files.py
        jobs.py
        records.py
        validation.py
        reports.py
        audit.py
        health.py
    auth/
      models.py
      service.py
      permissions.py
    config/
      settings.py
      logging.yaml
    db/
      base.py
      models.py
      session.py
      repositories.py
      migrations/
    ingestion/
      storage.py
      file_hasher.py
      email_loader.py
      csv_loader.py
    parsers/
      pdf_parser.py
      table_parser.py
      csv_parser.py
      email_parser.py
      ocr_parser.py
      chunker.py
    extraction/
      document_classifier.py
      llm_client.py
      prompts.py
      schemas.py
      reconciliation.py
    validation/
      rules.py
      evidence.py
      duplicate_detection.py
      contract_invoice_match.py
    orchestration/
      flows.py
      tasks.py
      schedules.py
    queue/
      redis_streams.py
      events.py
    reports/
      builders.py
      exporters.py
      templates/
    observability/
      logging.py
      tracing.py
      metrics.py
    utils/
      dates.py
      currency.py
      ids.py
  dashboard/
    app.py
    pages/
  tests/
    unit/
    integration/
    e2e/
    fixtures/
      contracts/
      invoices/
      csv/
  deploy/
    Dockerfile.api
    Dockerfile.worker
    docker-compose.yml
    grafana/
    prometheus/
  scripts/
    seed_demo_data.py
    run_pipeline.py
  docs/
    README.md
    architecture.md
    api_examples.md
  pyproject.toml
  .env.example
  README.md
```

## 8. Database Design

```sql
CREATE TABLE uploaded_files (
    id UUID PRIMARY KEY,
    tenant_id UUID,
    original_filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    content_type TEXT,
    storage_uri TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    uploaded_by UUID,
    status TEXT NOT NULL DEFAULT 'uploaded',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, sha256_hash)
);

CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY,
    tenant_id UUID,
    file_id UUID REFERENCES uploaded_files(id),
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    attempt_count INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 3,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, idempotency_key)
);

CREATE TABLE extracted_records (
    id UUID PRIMARY KEY,
    tenant_id UUID,
    file_id UUID REFERENCES uploaded_files(id),
    job_id UUID REFERENCES processing_jobs(id),
    record_type TEXT NOT NULL,
    vendor_name TEXT,
    document_date DATE,
    external_reference TEXT,
    normalized_payload JSONB NOT NULL,
    raw_llm_payload JSONB,
    confidence NUMERIC(5,4),
    review_status TEXT NOT NULL DEFAULT 'pending_validation',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_extracted_records_payload_gin
ON extracted_records USING GIN (normalized_payload);

CREATE TABLE extraction_errors (
    id UUID PRIMARY KEY,
    tenant_id UUID,
    file_id UUID REFERENCES uploaded_files(id),
    job_id UUID REFERENCES processing_jobs(id),
    stage TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    retryable BOOLEAN NOT NULL DEFAULT false,
    raw_context JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE validation_results (
    id UUID PRIMARY KEY,
    tenant_id UUID,
    record_id UUID REFERENCES extracted_records(id),
    rule_name TEXT NOT NULL,
    severity TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    message TEXT,
    field_path TEXT,
    expected_value TEXT,
    actual_value TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE source_evidence (
    id UUID PRIMARY KEY,
    tenant_id UUID,
    record_id UUID REFERENCES extracted_records(id),
    field_path TEXT NOT NULL,
    page_number INT,
    char_start INT,
    char_end INT,
    evidence_text TEXT NOT NULL,
    confidence NUMERIC(5,4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    tenant_id UUID,
    actor_id UUID,
    actor_type TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    before_state JSONB,
    after_state JSONB,
    request_id TEXT,
    ip_address INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE generated_reports (
    id UUID PRIMARY KEY,
    tenant_id UUID,
    report_type TEXT NOT NULL,
    status TEXT NOT NULL,
    parameters JSONB NOT NULL,
    storage_uri TEXT,
    generated_by UUID,
    generated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE llm_calls (
    id UUID PRIMARY KEY,
    tenant_id UUID,
    job_id UUID REFERENCES processing_jobs(id),
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    purpose TEXT NOT NULL,
    prompt_tokens INT,
    completion_tokens INT,
    estimated_cost_usd NUMERIC(12,6),
    latency_ms INT,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 9. API Design

### Upload file

`POST /v1/files`

Request: multipart form-data with `file`, optional `document_type`.

Response:

```json
{
  "file_id": "4c68b0e6-7e59-4d20-9b35-3c1f6b79e123",
  "job_id": "b4cde7ef-1538-4020-a58f-f49d1e013c31",
  "status": "queued"
}
```

### Trigger pipeline run

`POST /v1/jobs`

```json
{
  "file_id": "4c68b0e6-7e59-4d20-9b35-3c1f6b79e123",
  "pipeline": "document_extraction"
}
```

Response:

```json
{
  "job_id": "fd128707-b94e-47fd-b471-6e972f468ce2",
  "status": "queued"
}
```

### Check job status

`GET /v1/jobs/{job_id}`

```json
{
  "job_id": "fd128707-b94e-47fd-b471-6e972f468ce2",
  "status": "completed_with_errors",
  "attempt_count": 2,
  "records_created": 1,
  "validation_failures": 2
}
```

### View extracted records

`GET /v1/records?record_type=invoice&vendor=Acme`

```json
{
  "items": [
    {
      "record_id": "9dd15d32-9daa-4af5-b7ac-a6d3013afa60",
      "record_type": "invoice",
      "vendor_name": "Acme Software LLC",
      "confidence": 0.94,
      "review_status": "validated",
      "payload": {
        "invoice_number": "INV-1044",
        "invoice_date": "2026-03-31",
        "total_amount": 12400.00,
        "currency": "USD"
      }
    }
  ]
}
```

### View validation errors

`GET /v1/validation-errors?severity=high`

```json
{
  "items": [
    {
      "record_id": "9dd15d32-9daa-4af5-b7ac-a6d3013afa60",
      "rule_name": "invoice_total_matches_line_items",
      "severity": "high",
      "message": "Line items sum to 12200.00 but invoice total is 12400.00"
    }
  ]
}
```

### Generate report

`POST /v1/reports`

```json
{
  "report_type": "renewal_risk",
  "format": "xlsx",
  "parameters": {
    "renewal_window_days": 90
  }
}
```

Response:

```json
{
  "report_id": "6f46f7d5-8d98-45f4-b088-719d8b8b5fb4",
  "status": "queued"
}
```

### Download report

`GET /v1/reports/{report_id}/download`

Returns a signed URL or binary file response.

## 10. LLM Extraction Design

### Chunking

- Parse each page into blocks with page number and character offsets.
- Keep chunks under model context limits, but prefer semantic chunks: contract header, payment terms, renewal clause, invoice summary, line items.
- Use overlap only for long clauses, not for every page.
- Store `chunk_id`, `page_start`, `page_end`, `char_start`, `char_end`.
- For contracts, run clause-targeted extraction: parties, dates, term/renewal, payment, termination, liability, obligations.
- For invoices, keep summary fields and line-item tables together.

### Field Extraction

Use document-specific schemas:
- `ContractExtraction`
- `InvoiceExtraction`
- `PurchaseOrderExtraction`
- `VendorEmailExtraction`

Each important field includes:
- `value`
- `normalized_value`
- `confidence`
- `evidence_text`
- `page_number`
- `needs_review`

### Force JSON Output

Use Structured Outputs with strict JSON schema. OpenAI docs distinguish Structured Outputs from older JSON mode because schema adherence is enforced, while JSON mode only guarantees valid JSON.

### Validate LLM Output

- Parse into Pydantic model.
- Reject unknown enum values.
- Normalize dates/currency.
- Check required fields by document type.
- Check source evidence.
- Run business rules.

### Handle Hallucinations

- Require evidence for every field.
- If evidence is missing, set value to `null`.
- Compare extracted values against source spans.
- Mark inferred values separately from directly quoted values.
- Penalize confidence when evidence is weak or conflicting.

### Retry Bad Outputs

Retry categories:
- Schema mismatch: retry with schema repair prompt.
- Missing required fields with obvious evidence: retry targeted field extraction.
- Low confidence: route to review.
- Source conflict: run reconciliation prompt over conflicting chunks.

### Compare Extracted Data with Source Text

- Direct string match for invoice numbers, dates, vendor names, amounts.
- Normalized match for currency and dates.
- Fuzzy match for company names.
- Numeric tolerance for totals.
- Evidence span must come from parsed document text, not model memory.

### Example Extraction Prompt

System:

```text
You extract structured business data from vendor documents.
Use only the provided source text. Do not guess.
If a value is not present, return null.
Every non-null field must include page_number, evidence_text, and confidence.
Return output that matches the provided JSON schema exactly.
```

User:

```text
Document type: invoice

Extract:
- vendor name
- invoice number
- invoice date
- due date
- payment terms
- currency
- subtotal
- tax
- total amount
- line items

Rules:
- total_amount must be the invoice grand total, not a line item.
- If multiple totals exist, choose the final amount due and cite the evidence.
- Do not infer due date unless payment terms and invoice date are both explicit.

Source text:
<PAGE 1>
{{chunk_text}}
```

Example contract clause prompt:

```text
Extract renewal and termination information from this contract section.
Return null for missing fields.
For auto_renews, return true only if the text explicitly says the agreement renews automatically.
For notice_period_days, convert "30 days prior written notice" to 30.
Quote the exact phrase supporting each answer.

Source:
{{contract_chunk}}
```

## 11. Business Use Case

Who would pay:
- Accounting firms managing client AP documents.
- SMB finance teams with vendor sprawl.
- Procurement consultants.
- SaaS companies with many vendor renewals.
- Managed service providers handling contracts/invoices for clients.

Pain solved:
- Manual document entry.
- Missed renewal deadlines.
- Duplicate or incorrect invoices.
- No single vendor spend/contract view.
- Poor audit trail for finance operations.

Pricing:
- Portfolio/free demo: open-source self-hosted.
- Freelance pilot: $3,000 to $10,000 setup for one workflow.
- Monthly managed service: $500 to $3,000/month depending on document volume.
- Usage pricing: $0.10 to $1.00 per page/document for extraction plus platform fee.
- Enterprise/custom: $15,000+ implementation if ERP/SSO/security requirements exist.

Freelance/consulting package:
"I build a secure AI document pipeline that turns your invoices and contracts into validated reports, flags exceptions, and exports data to your accounting workflow."

Offer tiers:
- Starter: 1 document type, CSV export, dashboard.
- Pro: invoices + contracts, validation rules, reports.
- Enterprise pilot: API, auth, audit logs, cloud deployment, custom integration.

Resume positioning:
Emphasize production pipeline design, LLM extraction reliability, validation, observability, and business reporting.

Interview explanation:
"I built an end-to-end AI data pipeline that ingests unstructured finance documents, extracts structured records with schema-constrained LLM outputs, validates them against business rules and source evidence, stores them in Postgres, and generates operational reports through a FastAPI/Streamlit interface. The important part was not the prompt; it was reliability, idempotency, auditability, and data quality."

## 12. Resume Bullets

- Architected an AI-powered document pipeline for vendor contracts and invoices processing 100+ sample files with schema-constrained LLM extraction, Postgres storage, and automated exception reporting.
- Built a FastAPI and Prefect-based ETL system that converted unstructured PDFs, CSVs, and emails into validated finance records with retries, audit logs, and job-level observability.
- Implemented LLM extraction workflows using JSON Schema, Pydantic validation, source evidence checks, and confidence scoring to reduce malformed outputs and flag low-trust records for review.
- Designed PostgreSQL schemas and reporting views for contracts, invoices, validation errors, processing jobs, and generated reports, enabling vendor spend, renewal, and invoice-risk dashboards.
- Deployed a containerized AI data platform with Redis queues, S3-compatible object storage, structured logging, and monitoring to demonstrate production-grade backend and data engineering practices.

## 13. GitHub README Outline

```md
# VendorOps AI

AI-powered data pipeline for extracting, validating, and reporting on vendor contracts, invoices, and finance documents.

## Overview
VendorOps AI ingests PDFs, CSVs, and email attachments, extracts structured records with LLMs, validates them with business rules, stores them in PostgreSQL, and generates reports/dashboards for finance and procurement teams.

## Architecture
- Ingestion API
- Object storage
- Redis queue
- Prefect pipeline
- PDF/CSV/email parsers
- LLM extraction service
- Validation engine
- PostgreSQL database
- Reporting service
- Streamlit dashboard
- Observability stack

## Features
- File upload and async processing
- PDF/CSV/email parsing
- Contract and invoice extraction
- JSON schema-constrained LLM outputs
- Validation and exception detection
- Source evidence tracking
- Audit logs
- Automated reports
- Dashboard and REST API

## Tech Stack
Python, FastAPI, Prefect, PostgreSQL, SQLAlchemy, Redis Streams, MinIO/S3, OpenAI, Pydantic, Streamlit, Docker, OpenTelemetry.

## Setup
1. Copy `.env.example` to `.env`
2. Run `docker compose up --build`
3. Run migrations
4. Start API and worker
5. Open dashboard

## Sample Inputs
- `tests/fixtures/contracts/sample_msa.pdf`
- `tests/fixtures/invoices/sample_invoice.pdf`
- `tests/fixtures/csv/vendor_master.csv`

## Sample Outputs
- Extracted invoice JSON
- Extracted contract JSON
- Validation errors
- Renewal report
- Invoice exception report

## API Examples
`POST /v1/files`
`GET /v1/jobs/{job_id}`
`GET /v1/records`
`POST /v1/reports`

## Dashboard Screenshots
TODO: Add screenshots for upload, job status, validation queue, and reports.

## Future Improvements
- Human review workflow
- Email inbox ingestion
- ERP integrations
- Webhooks
- Multi-tenant SaaS mode
- Contract risk scoring
```

## 14. Brutally Honest Advice

Hardest parts:
- Getting reliable extraction from messy PDFs.
- Handling scanned documents without spending too much on vision/OCR.
- Designing validation that catches real business issues instead of just checking types.
- Making source evidence and audit logs convincing.
- Preventing duplicate records during retries.
- Building a demo dataset that looks real without exposing sensitive data.

Beginner mistakes:
- Building a chatbot instead of a pipeline.
- Sending whole documents to an LLM without chunking, schemas, or source tracking.
- Treating LLM output as truth.
- Ignoring validation and human review.
- Only showing a JSON response instead of reports, exceptions, and dashboard workflows.
- Using too many tools before the core pipeline works.
- Calling it "production-grade" without retries, idempotency, logging, and failure states.

Overkill for MVP:
- Vector database.
- Fine-tuning.
- Kubernetes.
- Multi-agent orchestration.
- Complex RAG.
- Full React SaaS UI.
- ERP integrations.
- Custom OCR models.

Avoid:
- Generic "PDF summarizer" positioning.
- Fake claims like 99 percent accuracy without an evaluation set.
- Hiding validation failures. A good system surfaces uncertainty.
- Hardcoding sample PDFs so the demo breaks on new files.
- Logging raw invoices/contracts with sensitive values.
- Having no database schema beyond a blob table.

What makes it impressive:
- Batch upload of realistic documents.
- End-to-end async job lifecycle.
- Source-cited extraction.
- Validation failures that are business meaningful.
- Generated reports that finance/procurement teams recognize.
- Dashboard with operational metrics and review queue.
- Clear schema, tests, and Docker setup.
- Cost and token tracking.

What makes it look fake or weak:
- A single notebook.
- Only one perfect sample PDF.
- No error handling.
- No database normalization.
- No audit trail.
- No explanation of bad extraction handling.
- "AI agent" language with no measurable pipeline behavior.
- Dashboard screenshots that do not connect to real processed data.

## Immediate Build Order

1. Create FastAPI skeleton, Postgres models, MinIO file storage.
2. Add upload endpoint and file hash/idempotency.
3. Add PDF and CSV parsers.
4. Define invoice and contract Pydantic schemas.
5. Add OpenAI Structured Outputs extraction.
6. Store extracted records and raw payloads.
7. Add validation rules for invoice totals, required fields, duplicate invoices, and renewal dates.
8. Add job table and status transitions.
9. Add Prefect flow and Redis queue.
10. Build Streamlit dashboard.
11. Add reports.
12. Add audit logs, observability, and tests.

