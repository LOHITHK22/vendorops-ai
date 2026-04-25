$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$FrontendRoot = Join-Path $ProjectRoot "frontend"

if (-not (Test-Path $BackendPython)) {
    throw "Backend virtual environment not found at $BackendPython."
}

if (-not (Test-Path (Join-Path $FrontendRoot "node_modules"))) {
    throw "Frontend dependencies are missing. Run 'npm install' from $FrontendRoot first."
}

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$ProjectRoot'; & '$BackendPython' -m uvicorn app.api.main:app --reload"
) -WindowStyle Normal

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$FrontendRoot'; npm run dev"
) -WindowStyle Normal

Write-Host "Backend:  http://127.0.0.1:8000/docs"
Write-Host "Frontend: http://127.0.0.1:5173"

