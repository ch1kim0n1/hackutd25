# Quick Frontend Startup Script
# Starts the React development server

Write-Host "`n🚀 Starting APEX Frontend..." -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan

Set-Location frontend

Write-Host "`n📍 Frontend will be available at:" -ForegroundColor Yellow
Write-Host "   http://localhost:3000" -ForegroundColor White

Write-Host "`n⚡ Starting React dev server..." -ForegroundColor Yellow
Write-Host ""

npm start
