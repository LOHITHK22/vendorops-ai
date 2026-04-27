FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=container \
    APP_DEBUG=false \
    DATABASE_URL=postgresql+asyncpg://vendorops:vendorops@postgres:5432/vendorops \
    LOCAL_STORAGE_DIR=/app/storage \
    REPORTS_DIR=/app/reports_out \
    LOG_FORMAT=json \
    CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173

WORKDIR /app

RUN python -m pip install --upgrade pip

COPY pyproject.toml README.md alembic.ini ./
COPY app ./app
COPY alembic ./alembic

RUN python -m pip install .

RUN mkdir -p /app/data /app/storage /app/reports_out

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["sh", "-c", "alembic upgrade head && python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000"]
