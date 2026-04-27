param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonPath)) {
    throw "Virtual environment not found at $PythonPath. Run Phase 0 setup from the project root first."
}

Set-Location $ProjectRoot
& $PythonPath -m alembic upgrade head
& $PythonPath -m uvicorn app.api.main:app --reload --host 127.0.0.1 --port $Port
