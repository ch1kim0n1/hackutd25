# Quick Backend Startup Script
# Starts the FastAPI server for development

Write-Host "`n🚀 Starting APEX Backend Server..." -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan

Set-Location src\backend

Write-Host "`n📍 Server will be available at:" -ForegroundColor Yellow
Write-Host "   http://localhost:8000" -ForegroundColor White
Write-Host "   http://localhost:8000/docs (API Documentation)" -ForegroundColor White
Write-Host "   http://localhost:8000/health (Health Check)" -ForegroundColor White

Write-Host "`n⚡ Starting uvicorn..." -ForegroundColor Yellow
Write-Host ""

python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
