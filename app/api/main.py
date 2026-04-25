from fastapi import FastAPI

from app.api.routes import files, health, jobs
from app.config.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
        description="AI-powered data pipeline for document ingestion and extraction.",
    )

    app.include_router(health.router)
    app.include_router(files.router, prefix=settings.api_prefix)
    app.include_router(jobs.router, prefix=settings.api_prefix)

    return app


app = create_app()

