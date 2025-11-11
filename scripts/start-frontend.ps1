# Quick Frontend Startup Script
# Starts the React development server

Write-Host "`n🚀 Starting APEX Frontend..." -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan

Set-Location client/front

Write-Host "`n📍 Frontend will be available at:" -ForegroundColor Yellow
Write-Host "   http://localhost:5173 (Vite)" -ForegroundColor White

Write-Host "`n⚡ Starting Vite dev server..." -ForegroundColor Yellow
Write-Host ""

npm run dev
