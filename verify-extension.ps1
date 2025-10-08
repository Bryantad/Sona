#!/usr/bin/env pwsh
# verify-extension.ps1 - Verify Sona VS Code Extension Installation

$ErrorActionPreference = "Continue"

Write-Host "`n=== Sona Extension Verification ===`n" -ForegroundColor Cyan

# Check if code command exists
try {
    $null = & code --version 2>&1
    $codeAvailable = $true
} catch {
    Write-Host "❌ VS Code 'code' command not found" -ForegroundColor Red
    Write-Host "Cannot verify extension without VS Code CLI" -ForegroundColor Yellow
    exit 1
}

# Test 1: Check if extension is installed
Write-Host "Test 1: Extension Installation" -ForegroundColor Cyan
$installed = & code --list-extensions 2>&1 | Select-String -Pattern "waycoreinc.sona-ai-native-programming"

$extensionInstalled = $false
if ($installed) {
    Write-Host "✓ Extension installed: $installed" -ForegroundColor Green
    $extensionInstalled = $true
} else {
    Write-Host "✗ Extension not installed" -ForegroundColor Red
    Write-Host "  Run: .\install-extension.ps1" -ForegroundColor Yellow
}

# Test 2: Check extension directory
Write-Host "`nTest 2: Extension Files" -ForegroundColor Cyan
$extDir = Join-Path $env:USERPROFILE ".vscode\extensions\waycoreinc.sona-ai-native-programming-0.9.4"

$extDirValid = $false
if (Test-Path $extDir) {
    Write-Host "✓ Extension directory found" -ForegroundColor Green
    Write-Host "  Location: $extDir" -ForegroundColor Gray
    $extDirValid = $true
    
    # Check key files
    $packageJson = Join-Path $extDir "package.json"
    if (Test-Path $packageJson) {
        Write-Host "  ✓ package.json present" -ForegroundColor Green
    } else {
        Write-Host "  ✗ package.json missing" -ForegroundColor Red
        $extDirValid = $false
    }
    
    $extensionJs = Join-Path $extDir "extension.js"
    if (Test-Path $extensionJs) {
        Write-Host "  ✓ extension.js present" -ForegroundColor Green
    } else {
        Write-Host "  ✗ extension.js missing" -ForegroundColor Red
        $extDirValid = $false
    }
    
    $syntaxFile = Join-Path $extDir "syntaxes\sona.tmLanguage.json"
    if (Test-Path $syntaxFile) {
        Write-Host "  ✓ Syntax highlighting grammar present" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Syntax grammar missing" -ForegroundColor Red
        $extDirValid = $false
    }
} else {
    Write-Host "⚠ Extension directory not found at expected location" -ForegroundColor Yellow
    Write-Host "  Expected: $extDir" -ForegroundColor Gray
}

# Test 3: Check VSIX source file
Write-Host "`nTest 3: Source VSIX File" -ForegroundColor Cyan
$vsixPath = Join-Path $PSScriptRoot "sona-ai-native-programming-0.9.4\sona-ai-native-programming-0.9.4.vsix"

$vsixValid = $false
if (Test-Path $vsixPath) {
    $vsixSize = [math]::Round((Get-Item $vsixPath).Length / 1KB, 2)
    Write-Host "✓ Source VSIX found" -ForegroundColor Green
    Write-Host "  Location: $vsixPath" -ForegroundColor Gray
    Write-Host "  Size: $vsixSize KB" -ForegroundColor Gray
    $vsixValid = $true
} else {
    Write-Host "✗ Source VSIX not found" -ForegroundColor Red
    Write-Host "  Expected: $vsixPath" -ForegroundColor Yellow
}

# Test 4: Create test file
Write-Host "`nTest 4: Language Association Test" -ForegroundColor Cyan
$testFile = Join-Path $env:TEMP "test_sona_ext_$([guid]::NewGuid().ToString().Substring(0,8)).sona"

$testContent = @"
// Sona test file
print("Hello from Sona!")

let x = 42;
let name = "World";

function greet(name) {
    return "Hello, " + name;
}
"@

Set-Content -Path $testFile -Value $testContent -Encoding UTF8
Write-Host "✓ Created test file: $testFile" -ForegroundColor Green
Write-Host "  To test syntax highlighting:" -ForegroundColor Gray
Write-Host "    code $testFile" -ForegroundColor Gray

# Summary
Write-Host "`n=== Summary ===`n" -ForegroundColor Cyan

$passCount = 0
$totalTests = 3

if ($extensionInstalled) { $passCount++ }
if ($extDirValid) { $passCount++ }
if ($vsixValid) { $passCount++ }

Write-Host "Tests passed: $passCount/$totalTests"

if ($passCount -eq $totalTests) {
    Write-Host "`n✅ Extension verification PASSED!" -ForegroundColor Green
    Write-Host "`nNext Steps:" -ForegroundColor Cyan
    Write-Host "  1. Open VS Code: " -NoNewline; Write-Host "code" -ForegroundColor Gray
    Write-Host "  2. Open test file: " -NoNewline; Write-Host "code $testFile" -ForegroundColor Gray
    Write-Host "  3. Verify syntax highlighting works"
    Write-Host "  4. Check status bar for extension indicator"
    exit 0
} else {
    Write-Host "`n⚠ Some tests failed" -ForegroundColor Yellow
    Write-Host "`nTo fix:" -ForegroundColor Cyan
    Write-Host "  1. Run installation script: " -NoNewline; Write-Host ".\install-extension.ps1" -ForegroundColor Gray
    Write-Host "  2. Restart VS Code"
    Write-Host "  3. Run verification again"
    exit 1
}
