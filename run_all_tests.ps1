#!/usr/bin/env pwsh
# Sona 0.9.6 Test Suite Runner for PowerShell
# Runs all test files sequentially

Write-Host "========================================"
Write-Host "Sona 0.9.6 - Test Suite Runner"
Write-Host "========================================"
Write-Host ""

Write-Host "[1/8] Running complete verification test..."
sona test_all_096.sona
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: test_all_096.sona failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "[2/8] Running basic modules test..."
sona test_stdlib_basics.sona
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: test_stdlib_basics.sona failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "[3/8] Running data processing test..."
sona test_stdlib_data.sona
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: test_stdlib_data.sona failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "[4/8] Running collections test..."
sona test_stdlib_collections.sona
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: test_stdlib_collections.sona failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "[5/8] Running time and random test..."
sona test_stdlib_time.sona
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: test_stdlib_time.sona failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "[6/8] Running filesystem test..."
sona test_stdlib_filesystem.sona
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: test_stdlib_filesystem.sona failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "[7/8] Running regex test..."
sona test_stdlib_regex.sona
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: test_stdlib_regex.sona failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "[8/8] Running simple arithmetic test..."
sona test.sona
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: test.sona failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "========================================"
Write-Host "ALL TESTS COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "========================================"
Write-Host ""
Write-Host "Sona 0.9.6 is fully operational." -ForegroundColor Green
Write-Host ""
