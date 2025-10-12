#!/usr/bin/env pwsh
# Sona 0.9.6 Verification Script - Simple Version

Write-Host ""
Write-Host "Sona 0.9.6 - Quick Verification Test" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Version Check
Write-Host "[1/5] Checking version..." -ForegroundColor Yellow
python -c "import sona; print('Version:', sona.__version__)"
Write-Host ""

# Test 2: Workspace Lock
Write-Host "[2/5] Verifying workspace integrity..." -ForegroundColor Yellow
python .sonacore_lock.py
Write-Host ""

# Test 3: Hello World
Write-Host "[3/5] Testing hello world..." -ForegroundColor Yellow
python run_sona.py test_hello.sona
Write-Host ""

# Test 4: Simple Test
Write-Host "[4/5] Testing simple features..." -ForegroundColor Yellow
python run_sona.py test_simple_096.sona
Write-Host ""

# Test 5: Stdlib Imports
Write-Host "[5/5] Testing stdlib imports..." -ForegroundColor Yellow
python test_stdlib_30.py
Write-Host ""

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Verification Complete!" -ForegroundColor Green
Write-Host ""
