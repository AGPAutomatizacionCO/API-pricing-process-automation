$ErrorActionPreference = "Stop"

$RootPath = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path $RootPath "backend"
$FrontendPath = Join-Path $RootPath "frontend"
$BackendPython = Join-Path $BackendPath ".venv\Scripts\python.exe"

$BackendOutLog = Join-Path $BackendPath "logs\backend-dev.out.log"
$BackendErrLog = Join-Path $BackendPath "logs\backend-dev.err.log"
$FrontendOutLog = Join-Path $BackendPath "logs\frontend-dev.out.log"
$FrontendErrLog = Join-Path $BackendPath "logs\frontend-dev.err.log"

Write-Host "Starting Pricing Process Automation..." -ForegroundColor Cyan

if (!(Test-Path $BackendPython)) {
    Write-Host "Backend Python not found: $BackendPython" -ForegroundColor Red
    exit 1
}

if (!(Test-Path (Join-Path $FrontendPath "package.json"))) {
    Write-Host "Frontend package.json not found: $FrontendPath" -ForegroundColor Red
    exit 1
}

Start-Process -FilePath $BackendPython `
    -WorkingDirectory $BackendPath `
    -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000" `
    -RedirectStandardOutput $BackendOutLog `
    -RedirectStandardError $BackendErrLog `
    -WindowStyle Hidden

Start-Sleep -Seconds 3

Start-Process -FilePath "npm.cmd" `
    -WorkingDirectory $FrontendPath `
    -ArgumentList "run dev -- --host 127.0.0.1 --port 5173" `
    -RedirectStandardOutput $FrontendOutLog `
    -RedirectStandardError $FrontendErrLog `
    -WindowStyle Hidden

Start-Sleep -Seconds 5

Start-Process "http://localhost:5173"

Write-Host "Application started." -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173"
Write-Host "Backend:  http://localhost:8000"
Write-Host "Backend logs:"
Write-Host "  $BackendOutLog"
Write-Host "  $BackendErrLog"
Write-Host "Frontend logs:"
Write-Host "  $FrontendOutLog"
Write-Host "  $FrontendErrLog"