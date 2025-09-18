Param(
    [string]$PrevTag = "v0.9.2",
    [switch]$Apply
)

# Collect tracked changes in working tree vs tag (A/M), and include untracked files
$diff = git diff --name-status "$PrevTag" | Where-Object { $_ -match '^(A|M|R)\s' }
$changed = @()
foreach ($line in $diff) {
    # Handle name-status outputs: A\tpath, M\tpath, R100\told\tnew
    $cols = $line -split "\t"
    if ($cols.Count -ge 2) {
        if ($cols[0] -match "^R") {
            # For renames, take the new path (last column)
            $changed += $cols[-1]
        }
        else {
            $changed += $cols[1]
        }
    }
}

# Untracked files
$untracked = git ls-files -o --exclude-standard
$allChanged = @()
$allChanged += $changed
$allChanged += $untracked
$allChanged = $allChanged | Sort-Object -Unique

$allow = @(
    "src/**", "sona/**",
    "pyproject.toml", "setup.cfg", "ruff.toml", "tox.ini",
    "vscode-extension/**",
    "security/**", ".sona-policy.json",
    "README.md", "CHANGELOG.md", "FEATURE_FLAGS.md", "RESEARCH_AUDIT.md", "SECURITY.md", "docs/**",
    "release-0.9.3/**",
    "tests/**",
    "scripts/**", ".github/**"
)

$deny = @(
    ".venv/**", "venv/**", ".mypy_cache/**", ".pytest_cache/**", "dist/**", "build/**", "*.egg-info/**",
    "node_modules/**", "**/node_modules/**",
    "out/**", "**/out/**",
    "*.vsix", "**/*.vsix",
    "vscode-extension/_extracted/**",
    "docs/Sona.wiki/**",
    "*.log", "*.jsonl", "*.tmp", "*.bak", "*.swp", "*.ipynb", "nohup.out",
    ".idea/**", ".vscode/**", "*.code-workspace",
    "coverage/**", "htmlcov/**", ".coverage*",
    "data/**", "datasets/**", "local/**", "experiments/**", "playground/**", "scratch/**", "notes/**",
    "*.bin", "*.pt", "*.safetensors", "*.zip", "*.tar*", "*.7z"
)

function MatchesGlob($path, $patterns) {
    foreach ($g in $patterns) {
        if ([System.Management.Automation.WildcardPattern]::new($g, 'IgnoreCase').IsMatch($path)) { return $true }
    }
    return $false
}

$keep = @()
foreach ($f in $allChanged) {
    if (-not (MatchesGlob $f $allow)) { continue }
    if (MatchesGlob $f $deny) { continue }
    $keep += $f
}

# Create categorized lists
$categories = @{
    "Core/CLI"          = @();
    "VS Code"           = @();
    "Policies/Security" = @();
    "Docs"              = @();
    "Tests"             = @();
    "Scripts/CI"        = @();
    "Other"             = @();
}

foreach ($f in $keep) {
    if (($f -match "^src/") -or ($f -match "^sona/") -or ($f -match "pyproject\.toml") -or ($f -match "setup\.cfg") -or ($f -match "ruff\.toml") -or ($f -match "tox\.ini")) {
        $categories["Core/CLI"] += $f
    }
    elseif ($f -match "^vscode-extension/") {
        $categories["VS Code"] += $f
    }
    elseif (($f -match "^security/") -or ($f -match "\.sona-policy\.json")) {
        $categories["Policies/Security"] += $f
    }
    elseif (($f -match "README\.md") -or ($f -match "CHANGELOG\.md") -or ($f -match "FEATURE_FLAGS\.md") -or 
        ($f -match "RESEARCH_AUDIT\.md") -or ($f -match "SECURITY\.md") -or ($f -match "^docs/")) {
        $categories["Docs"] += $f
    }
    elseif ($f -match "^tests/") {
        $categories["Tests"] += $f
    }
    elseif (($f -match "^scripts/") -or ($f -match "^\.github/")) {
        $categories["Scripts/CI"] += $f
    }
    else {
        $categories["Other"] += $f
    }
}

Write-Host "=== Sona v0.9.3 Release Staging Plan ===" -ForegroundColor Cyan
Write-Host "Files to stage by category ($($keep.Count) total):`n" -ForegroundColor Green

foreach ($category in $categories.Keys) {
    $files = $categories[$category]
    if ($files.Count -gt 0) {
        Write-Host "$category ($($files.Count) files):" -ForegroundColor Yellow
        $files | ForEach-Object { Write-Host "  - $_" }
        Write-Host ""
    }
}

# Generate git add commands
Write-Host "=== Git Add Commands ===" -ForegroundColor Cyan
Write-Host "# Run these commands to stage the release:" -ForegroundColor Green
foreach ($f in $keep) {
    Write-Host "git add -- `"$f`""
}

Write-Host "`n=== Draft Commit Message ===" -ForegroundColor Cyan
$commitMsg = @"
release: v0.9.3 (infra, flags, policy, diagnostics)

- CLI: Added doctor, build-info, and ai-* command stubs
- Infrastructure: Implemented policy engine and circuit breaker pattern
- Configuration: Added feature flag system for staged rollout
- VS Code: Added Focus Mode toggle with ADHD/dyslexia profile stubs
- Documentation: Updated for v0.9.3 features and infrastructure

Refs: #release-0.9.3
"@

Write-Host $commitMsg -ForegroundColor Green

Write-Host "`n=== Tag Command ===" -ForegroundColor Cyan
Write-Host "git tag -a v0.9.3 -m `"Sona v0.9.3`"" -ForegroundColor Green

Write-Host "`nInstructions:" -ForegroundColor Magenta
Write-Host "1. Review the files to be staged" -ForegroundColor White
Write-Host "2. Run the git add commands (or use the -Apply switch when running this script)" -ForegroundColor White
Write-Host "3. Run sanity checks: pytest -q, ruff check ." -ForegroundColor White
Write-Host "4. Verify staged files: git diff --cached --name-status" -ForegroundColor White
Write-Host "5. Commit and tag when ready" -ForegroundColor White

# Apply changes if requested
if ($PSBoundParameters.ContainsKey('Apply') -and $Apply) {
    Write-Host "`nApplying changes..." -ForegroundColor Yellow
    foreach ($f in $keep) {
        git add -- $f
    }
  
    Write-Host "`nStaged set:" -ForegroundColor Green
    git diff --cached --name-status
}
