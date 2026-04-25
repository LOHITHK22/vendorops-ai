# VendorOps AI

VendorOps AI is a production-style AI data pipeline for ingesting vendor documents, extracting structured data with an LLM or mock extractor, validating the output, storing results, and generating operational reports.

The initial MVP uses Python, FastAPI, SQLAlchemy, SQLite, Pydantic, pytest, and Docker. The design stays PostgreSQL-ready so the project can grow from a local portfolio build into a credible service architecture.

## Project Goals

- Ingest PDFs, CSVs, text files, and email-like files.
- Extract structured vendor, invoice, and contract data.
- Validate required fields, data types, confidence scores, duplicates, and malformed outputs.
- Store files, jobs, extracted records, validation errors, audit logs, and reports.
- Provide FastAPI endpoints for upload, pipeline runs, job status, records, errors, and reports.
- Generate JSON and CSV reports.
- Include structured logging, retries, error tracking, Docker support, and tests.

## Phase Roadmap

- Phase 0: Project setup.
- Phase 1: FastAPI backend with health check, file upload, and job creation.
- Phase 2: Database layer.
- Phase 3: File parsing.
- Phase 4: LLM extraction with mock fallback.
- Phase 5: Validation layer.
- Phase 6: Pipeline orchestration.
- Phase 7: Reporting.
- Phase 8: Observability.
- Phase 9: Docker and deployment.
- Phase 10: Testing.
- Phase 11: GitHub polish.

## Current Status

Phase 3 is complete:

- Repository structure created.
- Python dependencies defined in `pyproject.toml`.
- Environment template added in `.env.example`.
- `.gitignore` added.
- README skeleton added.
- FastAPI app factory added.
- Health endpoint added.
- File upload endpoint added for `.csv`, `.eml`, `.pdf`, and `.txt`.
- Job creation and job status endpoints added.
- Local file storage added for uploaded files.
- Phase 1 API tests added.
- SQLAlchemy async database layer added.
- SQLite-backed tables added for uploaded files, processing jobs, extracted records, validation errors, audit logs, and generated reports.
- Upload and job endpoints now persist to the database.
- Audit events are created for file uploads and job creation.
- Parser layer added for TXT, CSV, PDF, and EML/email-like files.
- Uploaded files can be parsed through `GET /v1/files/{file_id}/parsed`.

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Create your local environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

## Planned API Examples

Implemented endpoints:

```text
GET  /health
POST /v1/files
GET  /v1/files/{file_id}/parsed
POST /v1/jobs
GET  /v1/jobs/{job_id}
```

Planned endpoints:

```text
GET  /v1/records
GET  /v1/validation-errors
POST /v1/reports
GET  /v1/reports/{report_id}/download
```

## Run The API

```bash
uvicorn app.api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## API Examples

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Upload a file:

```bash
curl -X POST http://127.0.0.1:8000/v1/files \
  -F "file=@tests/fixtures/sample_invoice.txt"
```

Create a job:

```bash
curl -X POST http://127.0.0.1:8000/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"file_id":"<FILE_ID>","pipeline":"document_extraction"}'
```

Check job status:

```bash
curl http://127.0.0.1:8000/v1/jobs/<JOB_ID>
```

Parse an uploaded file:

```bash
curl http://127.0.0.1:8000/v1/files/<FILE_ID>/parsed
```

## Planned Architecture

```text
Files / Emails / CSVs
        |
        v
FastAPI Ingestion API
        |
        v
Local Storage + Processing Job
        |
        v
Parser -> Extractor -> Validator
        |
        v
SQLite/PostgreSQL
        |
        v
Reports + API Responses
```

## Database

The MVP defaults to SQLite:

```env
DATABASE_URL=sqlite+aiosqlite:///./vendorops.db
```

The database layer uses SQLAlchemy async models and is designed so the URL can later be changed to PostgreSQL with minimal application-code changes.

Current tables:

- `uploaded_files`
- `processing_jobs`
- `extracted_records`
- `validation_errors`
- `audit_logs`
- `generated_reports`

## Parser Layer

The parser dispatcher normalizes supported file types into one shape:

- `text`: extracted text for downstream LLM extraction.
- `metadata`: source-specific metadata such as filename, row count, columns, headers, or page count.
- `pages`: PDF page-level text.
- `tables`: CSV rows and columns.

Supported parsers:

- TXT: UTF-8 text extraction.
- CSV: header/row extraction using Python's standard `csv` module.
- EML: subject/from/to/date headers and plain-text body extraction.
- PDF: text extraction using PyMuPDF.

## Testing

Run the current test suite:

```bash
pytest
```

## Resume Positioning

VendorOps AI demonstrates backend engineering, data engineering, AI extraction workflows, structured validation, pipeline reliability, and production-style API design.
