# VendorOps AI Deployment

This folder contains production-oriented deployment support for VendorOps AI.

## Docker Compose

From the project root:

```powershell
docker compose up --build
```

Open:

```text
http://127.0.0.1:5173
```

The backend remains available directly at:

```text
http://127.0.0.1:8000/docs
```

## Runtime Storage

Compose creates persistent Docker volumes for:

- SQLite database: `/app/data/vendorops.db`
- Uploaded files: `/app/storage`
- Generated reports: `/app/reports_out`

## LLM Configuration

The app uses the mock extractor when `OPENAI_API_KEY` is empty.

To use OpenAI extraction:

```powershell
Copy-Item .env.docker.example .env
```

Then edit `.env` and set:

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

Restart the stack:

```powershell
docker compose up --build
```

## Production Notes

- Put the frontend behind HTTPS in production.
- Store secrets in the deployment platform, not in `.env` files committed to Git.
- Use managed PostgreSQL before multi-user production rollout.
- Replace local Docker volumes with managed object storage for uploaded documents and reports.
- Add authentication before exposing upload and report APIs publicly.
