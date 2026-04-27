param(
    [string]$Revision = "head"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonPath)) {
    throw "Virtual environment not found at $PythonPath. Run: python -m venv .venv"
}

Set-Location $ProjectRoot
& $PythonPath -m alembic upgrade $Revision
