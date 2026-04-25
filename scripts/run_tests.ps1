$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonPath)) {
    Write-Error "Virtual environment not found. Run: python -m venv .venv"
}

& $PythonPath -m ruff check .
& $PythonPath -m pytest

Push-Location (Join-Path $ProjectRoot "frontend")
try {
    npm run build
}
finally {
    Pop-Location
}
