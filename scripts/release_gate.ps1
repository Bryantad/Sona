param(
    [string]$ExpectedVersion = "0.15.0"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Read-ProjectVersion {
    $line = (Get-Content pyproject.toml | Where-Object { $_ -match '^version\s*=' } | Select-Object -First 1)
    if (-not $line) {
        throw "Could not find version in pyproject.toml"
    }
    if ($line -match '"([^"]+)"') {
        return $Matches[1]
    }
    throw "Could not parse version line in pyproject.toml: $line"
}

function Read-InitVersion {
    $line = (Get-Content sona/__init__.py | Where-Object { $_ -match '^__version__\s*=' } | Select-Object -First 1)
    if (-not $line) {
        throw "Could not find __version__ in sona/__init__.py"
    }
    if ($line -match '"([^"]+)"') {
        return $Matches[1]
    }
    throw "Could not parse __version__ line in sona/__init__.py: $line"
}

function Assert-Exists([string]$Path) {
    if (-not (Test-Path $Path)) {
        throw "Missing required file: $Path"
    }
}

Write-Host "== Sona release gate =="

$projectVersion = Read-ProjectVersion
$initVersion = Read-InitVersion

if ($projectVersion -ne $ExpectedVersion) {
    throw "pyproject.toml version '$projectVersion' does not match expected '$ExpectedVersion'"
}
if ($initVersion -ne $ExpectedVersion) {
    throw "sona/__init__.py version '$initVersion' does not match expected '$ExpectedVersion'"
}

Assert-Exists "RELEASE_NOTES_v0.15.0.md"

Write-Host "Version checks passed ($ExpectedVersion)."
Write-Host "Running smoke/test gates..."

python tools/validate_release_metadata.py --version $ExpectedVersion
if ($LASTEXITCODE -ne 0) { throw "validate_release_metadata.py failed with exit code $LASTEXITCODE" }

python -m sona --version
if ($LASTEXITCODE -ne 0) { throw "python -m sona --version failed with exit code $LASTEXITCODE" }

python -m pytest -q tests -x
if ($LASTEXITCODE -ne 0) { throw "pytest failed with exit code $LASTEXITCODE" }

python -m sona probe stdlib
if ($LASTEXITCODE -ne 0) { throw "python -m sona probe stdlib failed with exit code $LASTEXITCODE" }

python -m sona build-info
if ($LASTEXITCODE -ne 0) { throw "python -m sona build-info failed with exit code $LASTEXITCODE" }

python tools/run_examples.py
if ($LASTEXITCODE -ne 0) { throw "tools/run_examples.py failed with exit code $LASTEXITCODE" }

Write-Host "Release gate passed."
