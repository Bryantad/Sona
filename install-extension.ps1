#!/usr/bin/env pwsh
# install-extension.ps1 - Automated Sona VS Code Extension Installer
# This script uninstalls any existing Sona extensions and installs the working v0.9.4 VSIX

param(
    [switch]$Force,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host @"
Sona VS Code Extension Installer
=================================

This script:
1. Uninstalls any existing Sona extensions
2. Installs the working v0.9.4 VSIX from the repository
3. Verifies the installation

Usage:
    .\install-extension.ps1           # Normal installation
    .\install-extension.ps1 -Force    # Force reinstall even if already installed
    .\install-extension.ps1 -Help     # Show this help

Requirements:
- VS Code must be installed and 'code' command available in PATH
- Run from the Sona repository root directory

"@
    exit 0
}

if ($Help) {
    Show-Help
}

Write-Host "`n=== Sona VS Code Extension Installer ===" -ForegroundColor Cyan
Write-Host "Using clean v0.9.4 VSIX (no dependencies)" -ForegroundColor Green

# Check if VS Code is available
try {
    $null = & code --version 2>&1
} catch {
    Write-Host "`n❌ ERROR: VS Code 'code' command not found in PATH" -ForegroundColor Red
    Write-Host "`nPlease ensure VS Code is installed and the 'code' command is available." -ForegroundColor Yellow
    Write-Host "You may need to:" -ForegroundColor Yellow
    Write-Host "  1. Install VS Code from https://code.visualstudio.com/" -ForegroundColor Yellow
    Write-Host "  2. Open VS Code → Command Palette → 'Shell Command: Install code command in PATH'" -ForegroundColor Yellow
    exit 1
}

# Locate the VSIX file
$vsixPath = Join-Path $PSScriptRoot "sona-ai-native-programming-0.9.4\sona-ai-native-programming-0.9.4.vsix"

if (-not (Test-Path $vsixPath)) {
    Write-Host "`n❌ ERROR: VSIX file not found at:" -ForegroundColor Red
    Write-Host "  $vsixPath" -ForegroundColor Yellow
    Write-Host "`nPlease ensure you're running this script from the Sona repository root." -ForegroundColor Yellow
    exit 1
}

$vsixSize = (Get-Item $vsixPath).Length / 1KB
Write-Host "`n✓ Found VSIX: $vsixPath" -ForegroundColor Green
Write-Host "  Size: $([math]::Round($vsixSize, 2)) KB" -ForegroundColor Gray

# Check for existing Sona extensions
Write-Host "`nChecking for existing Sona extensions..." -ForegroundColor Cyan
$existingExtensions = & code --list-extensions 2>&1 | Select-String -Pattern "sona" -AllMatches

if ($existingExtensions) {
    Write-Host "Found existing Sona extension(s):" -ForegroundColor Yellow
    $existingExtensions | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    
    Write-Host "`nUninstalling existing Sona extensions..." -ForegroundColor Cyan
    foreach ($ext in $existingExtensions) {
        $extId = $ext.ToString().Trim()
        Write-Host "  Uninstalling: $extId" -ForegroundColor Gray
        & code --uninstall-extension $extId 2>&1 | Out-Null
    }
    Write-Host "✓ Uninstalled existing extensions" -ForegroundColor Green
} else {
    Write-Host "✓ No existing Sona extensions found" -ForegroundColor Green
}

# Install the v0.9.4 VSIX
Write-Host "`nInstalling Sona v0.9.4 extension..." -ForegroundColor Cyan
try {
    $installOutput = & code --install-extension $vsixPath 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Extension installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "⚠ Installation completed with warnings:" -ForegroundColor Yellow
        Write-Host $installOutput -ForegroundColor Gray
    }
} catch {
    Write-Host "`n❌ ERROR: Failed to install extension" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    exit 1
}

# Verify installation
Write-Host "`nVerifying installation..." -ForegroundColor Cyan
$installed = & code --list-extensions 2>&1 | Select-String -Pattern "waycoreinc.sona-ai-native-programming"

if ($installed) {
    Write-Host "✓ Extension verified: $installed" -ForegroundColor Green
} else {
    Write-Host "⚠ Warning: Extension may not be installed correctly" -ForegroundColor Yellow
    Write-Host "  Run 'code --list-extensions' to check manually" -ForegroundColor Gray
}

# Success message
Write-Host "`n" + ("="*50) -ForegroundColor Cyan
Write-Host "✅ Sona v0.9.4 Extension Installation Complete!" -ForegroundColor Green
Write-Host ("="*50) -ForegroundColor Cyan

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. Restart VS Code (if it's currently running)" -ForegroundColor White
Write-Host "2. Open or create a .sona file to activate the extension" -ForegroundColor White
Write-Host "3. Check syntax highlighting is working" -ForegroundColor White

Write-Host "`nTo test the extension:" -ForegroundColor Cyan
Write-Host "  - Create a test file: test.sona" -ForegroundColor White
Write-Host "  - Add code: print(`"Hello from Sona!`")" -ForegroundColor White
Write-Host "  - Verify syntax highlighting appears" -ForegroundColor White

Write-Host "`nExtension Features:" -ForegroundColor Cyan
Write-Host "  ✓ Syntax highlighting for .sona files" -ForegroundColor Green
Write-Host "  ✓ Language configuration (auto-close, comments)" -ForegroundColor Green
Write-Host "  ✓ Code snippets" -ForegroundColor Green
Write-Host "  ✓ Custom file icons" -ForegroundColor Green

Write-Host "`nFor more info, see: INSTALL_EXTENSION.md`n" -ForegroundColor Gray
