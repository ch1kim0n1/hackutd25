# APEX Phase 1 Quick Start
# Run this script to set up and test Phase 1 components

Write-Host "`n🚀 APEX PHASE 1 SETUP" -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan

# Step 1: Check Python
Write-Host "`n📦 Step 1: Checking Python..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Python found" -ForegroundColor Green

# Step 2: Install backend dependencies
Write-Host "`n📦 Step 2: Installing Python packages..." -ForegroundColor Yellow
Set-Location src\backend
python -m pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python packages installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some packages failed to install (continuing...)" -ForegroundColor Yellow
}

# Step 3: Check for .env file
Write-Host "`n🔑 Step 3: Checking environment variables..." -ForegroundColor Yellow
Set-Location ..\..
if (Test-Path ".env") {
    Write-Host "✅ .env file exists" -ForegroundColor Green
} else {
    Write-Host "⚠️  No .env file found" -ForegroundColor Yellow
    Write-Host "   Creating from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "   Please edit .env and add your API keys!" -ForegroundColor Yellow
}

# Step 4: Check Redis
Write-Host "`n🗄️  Step 4: Checking Redis..." -ForegroundColor Yellow
try {
    $redis = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    if ($redis.TcpTestSucceeded) {
        Write-Host "✅ Redis is running" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Redis not running (will use in-memory mode)" -ForegroundColor Yellow
        Write-Host "   To start Redis: docker run -d -p 6379:6379 redis" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️  Could not check Redis (will use in-memory mode)" -ForegroundColor Yellow
}

# Step 5: Download historical data
Write-Host "`n📊 Step 5: Checking historical market data..." -ForegroundColor Yellow
if (Test-Path "data\historical-markets\2008_crisis.json") {
    Write-Host "✅ Historical data already downloaded" -ForegroundColor Green
} else {
    Write-Host "📥 Downloading crash scenarios..." -ForegroundColor Yellow
    Set-Location src\backend
    python services\historical_data.py download
    Set-Location ..\..
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Historical data downloaded" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Data download incomplete (can retry later)" -ForegroundColor Yellow
    }
}

# Step 6: Run setup tests
Write-Host "`n🧪 Step 6: Running setup tests..." -ForegroundColor Yellow
Set-Location src\backend
python test_setup.py
$testResult = $LASTEXITCODE
Set-Location ..\..

# Step 7: Install frontend dependencies
Write-Host "`n📦 Step 7: Checking frontend dependencies..." -ForegroundColor Yellow
Set-Location frontend
if (Test-Path "node_modules") {
    Write-Host "✅ Node modules already installed" -ForegroundColor Green
} else {
    Write-Host "📥 Installing npm packages..." -ForegroundColor Yellow
    npm install --silent
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Some npm packages failed (continuing...)" -ForegroundColor Yellow
    }
}
Set-Location ..

# Summary
Write-Host "`n" + "="*70 -ForegroundColor Cyan
if ($testResult -eq 0) {
    Write-Host "✅ PHASE 1 SETUP COMPLETE!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "  1. Edit .env and add your API keys" -ForegroundColor White
    Write-Host "  2. Start backend:  cd src\backend; python -m uvicorn server:app --reload" -ForegroundColor White
    Write-Host "  3. Start frontend: cd frontend; npm start" -ForegroundColor White
    Write-Host "  4. Open http://localhost:3000" -ForegroundColor White
} else {
    Write-Host "⚠️  PHASE 1 INCOMPLETE" -ForegroundColor Yellow
    Write-Host "`nPlease check warnings above and:" -ForegroundColor Yellow
    Write-Host "  1. Add API keys to .env file" -ForegroundColor White
    Write-Host "  2. Start Redis (optional): docker run -d -p 6379:6379 redis" -ForegroundColor White
    Write-Host "  3. Re-run this script or see PHASE1_SETUP.md" -ForegroundColor White
}
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""
