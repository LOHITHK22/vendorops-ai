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

Phase 0 is complete:

- Repository structure created.
- Python dependencies defined in `pyproject.toml`.
- Environment template added in `.env.example`.
- `.gitignore` added.
- README skeleton added.

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

These endpoints will be implemented in later phases:

```text
GET  /health
POST /v1/files
POST /v1/jobs
GET  /v1/jobs/{job_id}
GET  /v1/records
GET  /v1/validation-errors
POST /v1/reports
GET  /v1/reports/{report_id}/download
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

## Testing

Tests will be added in Phase 10. Once available, run:

```bash
pytest
```

## Resume Positioning

VendorOps AI demonstrates backend engineering, data engineering, AI extraction workflows, structured validation, pipeline reliability, and production-style API design.

