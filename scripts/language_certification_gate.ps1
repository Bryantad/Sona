param(
    [string]$ExpectedVersion = "0.15.3",
    [switch]$SkipPackaging,
    [string]$CertRoot = $env:SONA_CERT_ROOT
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))

if ($ExpectedVersion -ne "0.15.3") {
    throw "The schema-2 language gate is defined only for Sona 0.15.3."
}
if ([string]::IsNullOrWhiteSpace($CertRoot)) {
    throw "Set SONA_CERT_ROOT or pass -CertRoot with an absolute path outside the repository."
}
$ResolvedCertRoot = [System.IO.Path]::GetFullPath($CertRoot)
$env:SONA_CERT_ROOT = $ResolvedCertRoot

# -SkipPackaging remains accepted for command-line compatibility. Packaging is
# performed by the separate aggregate hardening wrapper.
$null = $SkipPackaging

Push-Location $RepoRoot
try {
    & python tools/release/certify_0153.py `
        --cert-root $ResolvedCertRoot `
        --phases python,gates
    if ($LASTEXITCODE -ne 0) {
        throw "Sona 0.15.3 language certification failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}
