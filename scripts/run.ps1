# APEX Demo Run Script (Windows PowerShell)
# Starts backend + frontend for local demo

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  APEX Demo - Starting Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if setup was run
if (-not (Test-Path "src\backend\venv")) {
    Write-Host "✗ Backend not set up. Run: .\scripts\setup.ps1" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "client\front\node_modules")) {
    Write-Host "✗ Frontend not set up. Run: .\scripts\setup.ps1" -ForegroundColor Red
    exit 1
}

Write-Host "Starting backend on http://localhost:8000 ..." -ForegroundColor Yellow
Write-Host "Starting frontend on http://localhost:5173 ..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Gray
Write-Host ""

# Start backend in background
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location "src\backend"
    & ".\venv\Scripts\Activate.ps1"
    $env:PYTHONUNBUFFERED = "1"
    uvicorn server:app --reload --host 0.0.0.0 --port 8000
}

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start frontend in background
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location "client\front"
    npm run dev
}

# Display status
Start-Sleep -Seconds 2
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Services Running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  Demo:     http://localhost:5173/demo" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop..." -ForegroundColor Gray
Write-Host ""

# Stream logs
try {
    while ($true) {
        Receive-Job -Job $backendJob -ErrorAction SilentlyContinue
        Receive-Job -Job $frontendJob -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 100
    }
} finally {
    Write-Host ""
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Stop-Job -Job $backendJob,$frontendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob,$frontendJob -Force -ErrorAction SilentlyContinue
    Write-Host "✓ Services stopped" -ForegroundColor Green
}
