param(
    [int]$Port = 5173
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$FrontendRoot = Join-Path $ProjectRoot "frontend"

if (-not (Test-Path (Join-Path $FrontendRoot "node_modules"))) {
    throw "Frontend dependencies are missing. Run 'npm install' from $FrontendRoot first."
}

Set-Location $FrontendRoot
& npm run dev -- --port $Port

