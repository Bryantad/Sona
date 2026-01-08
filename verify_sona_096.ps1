# Sona 0.9.6 Verification Script
# Quick smoke test to ensure everything is working

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Sona 0.9.6 - Quick Verification Smoke Test            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$TestCount = 0

function Test-SonaCommand {
    param (
        [string]$Name,
        [string]$Command
    )
    
    $script:TestCount++
    Write-Host "[$script:TestCount] Testing: $Name" -ForegroundColor Yellow
    
    try {
        Invoke-Expression $Command 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE) {
            Write-Host "    ✓ PASS" -ForegroundColor Green
        }
        else {
            Write-Host "    ✗ FAIL (exit code: $LASTEXITCODE)" -ForegroundColor Red
            $script:ErrorCount++
        }
    }
    catch {
        Write-Host "    ✗ FAIL (exception: $_)" -ForegroundColor Red
        $script:ErrorCount++
    }
    Write-Host ""
}

# Test 1: Version Check
Write-Host "Checking Sona version..." -ForegroundColor Cyan
try {
    $version = python -c "import sona; print(sona.__version__)" 2>&1
    if ($version -eq "0.9.6") {
        Write-Host "✓ Version: $version" -ForegroundColor Green
    }
    else {
        Write-Host "✗ Version mismatch: expected 0.9.6, got $version" -ForegroundColor Red
        $ErrorCount++
    }
}
catch {
    Write-Host "✗ Could not verify version" -ForegroundColor Red
    $ErrorCount++
}
Write-Host ""

# Test 2: Hello World
Test-SonaCommand "Hello World" "python run_sona.py tests/sona/test_hello.sona"

# Test 3: Simple Features
Test-SonaCommand "Simple Features (0.9.6)" "python run_sona.py tests/sona/test_simple_096.sona"

# Test 4: Demo Test
Test-SonaCommand "Demo Test" "python run_sona.py tests/sona/test_demo_simple_096.sona"

# Test 5: Standard Library Imports (Python)
Test-SonaCommand "Stdlib Module Imports" "python test_stdlib_30.py"

# Summary
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
if ($ErrorCount -eq 0) {
    Write-Host "🎉 ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "Sona 0.9.6 is fully operational!" -ForegroundColor Green
}
else {
    Write-Host "⚠️  $ErrorCount test(s) failed" -ForegroundColor Red
    exit 1
}
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Workspace: $(Get-Location)" -ForegroundColor Gray
$dateStr = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "Date: $dateStr" -ForegroundColor Gray
