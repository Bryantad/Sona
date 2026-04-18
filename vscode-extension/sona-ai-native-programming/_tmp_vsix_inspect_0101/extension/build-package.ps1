# Sona VS Code Extension - v0.9.6 Package Builder
# Automated build and verification script

param(
    [switch]$SkipCompile,
    [switch]$SkipTests,
    [switch]$Publish
)

$ErrorActionPreference = "Stop"

Write-Host "`n" -NoNewline
Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Sona VS Code Extension - v0.9.6 Package Builder                  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verify we're in the right directory
if (!(Test-Path "package.json")) {
    Write-Host "[ERROR] package.json not found. Please run from extension directory." -ForegroundColor Red
    exit 1
}

# Read package.json
$pkg = Get-Content package.json | ConvertFrom-Json
Write-Host "📦 Extension: $($pkg.displayName)" -ForegroundColor Yellow
Write-Host "   Version: $($pkg.version)" -ForegroundColor Green
Write-Host "   Publisher: $($pkg.publisher)" -ForegroundColor White
Write-Host ""

# Step 1: Check Node dependencies
Write-Host "[1/6] Checking dependencies..." -ForegroundColor Cyan
if (!(Test-Path "node_modules")) {
    Write-Host "   → Installing npm packages..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] npm install failed" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "   ✓ Dependencies installed" -ForegroundColor Green
}

# Step 2: Compile TypeScript
if (!$SkipCompile) {
    Write-Host "`n[2/6] Compiling TypeScript..." -ForegroundColor Cyan
    npm run compile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Compilation failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "   ✓ Compilation successful" -ForegroundColor Green
}
else {
    Write-Host "`n[2/6] Skipping compilation..." -ForegroundColor Yellow
}

# Step 3: Verify output files
Write-Host "`n[3/6] Verifying compiled files..." -ForegroundColor Cyan
$jsFiles = Get-ChildItem out -Recurse -Filter *.js -ErrorAction SilentlyContinue
if ($jsFiles.Count -eq 0) {
    Write-Host "[ERROR] No compiled JavaScript files found in out/" -ForegroundColor Red
    Write-Host "   Run without -SkipCompile to compile first" -ForegroundColor Yellow
    exit 1
}
Write-Host "   ✓ Found $($jsFiles.Count) compiled files" -ForegroundColor Green

# Step 4: Check for VSCE
Write-Host "`n[4/6] Checking for VSCE..." -ForegroundColor Cyan
$vsceInstalled = $null -ne (Get-Command vsce -ErrorAction SilentlyContinue)
if (!$vsceInstalled) {
    Write-Host "   → Installing VSCE globally..." -ForegroundColor Yellow
    npm install -g @vscode/vsce
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] VSCE installation failed" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "   ✓ VSCE is installed" -ForegroundColor Green
}

# Step 5: Package extension
Write-Host "`n[5/6] Packaging extension..." -ForegroundColor Cyan
$vsixFile = "$($pkg.name)-$($pkg.version).vsix"

# Backup old VSIX if exists
if (Test-Path $vsixFile) {
    $backupName = "$($pkg.name)-$($pkg.version)-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss').vsix"
    Write-Host "   → Backing up existing VSIX to $backupName" -ForegroundColor Yellow
    Move-Item $vsixFile $backupName -Force
}

vsce package
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Packaging failed" -ForegroundColor Red
    exit 1
}

if (!(Test-Path $vsixFile)) {
    Write-Host "[ERROR] VSIX file not created" -ForegroundColor Red
    exit 1
}

$vsixSize = (Get-Item $vsixFile).Length / 1MB
Write-Host "   ✓ Package created: $vsixFile" -ForegroundColor Green
Write-Host "   ✓ Size: $([math]::Round($vsixSize, 2)) MB" -ForegroundColor Green

# Step 6: Verify package contents
Write-Host "`n[6/6] Verifying package contents..." -ForegroundColor Cyan
$tempDir = ".\vsix-verify-temp"
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
Expand-Archive $vsixFile -DestinationPath $tempDir -Force

$requiredFiles = @(
    "extension/package.json",
    "extension/README.md",
    "extension/syntaxes/sona.tmLanguage.json"
)

$allPresent = $true
foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $tempDir $file
    if (Test-Path $fullPath) {
        Write-Host "   ✓ $file" -ForegroundColor Green
    }
    else {
        Write-Host "   ✗ $file MISSING" -ForegroundColor Red
        $allPresent = $false
    }
}

Remove-Item $tempDir -Recurse -Force

if (!$allPresent) {
    Write-Host "`n[WARNING] Some required files are missing from package" -ForegroundColor Yellow
}

# Summary
Write-Host "`n" -NoNewline
Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Build Complete!                                                  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "📦 Package: $vsixFile" -ForegroundColor Green
Write-Host "📏 Size: $([math]::Round($vsixSize, 2)) MB" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test locally:" -ForegroundColor White
Write-Host "     code --install-extension $vsixFile" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Publish to Marketplace:" -ForegroundColor White
Write-Host "     vsce publish" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Create GitHub release:" -ForegroundColor White
Write-Host "     - Tag: v$($pkg.version)" -ForegroundColor Gray
Write-Host "     - Attach: $vsixFile" -ForegroundColor Gray
Write-Host ""

if ($Publish) {
    Write-Host "[INFO] Publishing to marketplace..." -ForegroundColor Cyan
    vsce publish
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Published successfully!" -ForegroundColor Green
    }
    else {
        Write-Host "[ERROR] Publishing failed" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ Packaging complete!`n" -ForegroundColor Green
exit 0
