from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_backend_dockerfile_defines_api_runtime() -> None:
    dockerfile = PROJECT_ROOT / "Dockerfile"

    assert dockerfile.exists()
    contents = dockerfile.read_text(encoding="utf-8")
    assert "FROM python:3.12-slim" in contents
    assert "python -m pip install ." in contents
    assert "uvicorn" in contents
    assert "HEALTHCHECK" in contents
    assert (
        "DATABASE_URL=postgresql+asyncpg://vendorops:vendorops@postgres:5432/vendorops"
        in contents
    )
    assert "alembic upgrade head" in contents


def test_frontend_dockerfile_and_nginx_proxy_exist() -> None:
    dockerfile = PROJECT_ROOT / "frontend" / "Dockerfile"
    nginx_config = PROJECT_ROOT / "deploy" / "nginx" / "frontend.conf"

    assert dockerfile.exists()
    assert nginx_config.exists()

    dockerfile_contents = dockerfile.read_text(encoding="utf-8")
    nginx_contents = nginx_config.read_text(encoding="utf-8")

    assert "npm ci" in dockerfile_contents
    assert "npm run build" in dockerfile_contents
    assert "nginx:1.27-alpine" in dockerfile_contents
    assert "proxy_pass http://backend:8000/v1/" in nginx_contents
    assert "try_files $uri $uri/ /index.html" in nginx_contents


def test_docker_compose_defines_backend_frontend_and_volumes() -> None:
    compose_file = PROJECT_ROOT / "docker-compose.yml"

    assert compose_file.exists()
    contents = compose_file.read_text(encoding="utf-8")
    assert "backend:" in contents
    assert "frontend:" in contents
    assert "postgres:" in contents
    assert "vendorops_postgres:" in contents
    assert "vendorops_storage:" in contents
    assert "vendorops_reports:" in contents
    assert "postgresql+asyncpg://vendorops:vendorops@postgres:5432/vendorops" in contents
    assert "OPENAI_API_KEY: ${OPENAI_API_KEY:-}" in contents
