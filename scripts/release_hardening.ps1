param(
    [string]$ExpectedVersion = "0.15.3",
    [switch]$SkipLanguageCertification,
    [string]$CertRoot = $env:SONA_CERT_ROOT
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))

if ($ExpectedVersion -ne "0.15.3") {
    throw "The external release-hardening orchestrator is defined only for Sona 0.15.3."
}
if ([string]::IsNullOrWhiteSpace($CertRoot)) {
    throw "Set SONA_CERT_ROOT or pass -CertRoot with an absolute path outside the repository."
}
$ResolvedCertRoot = [System.IO.Path]::GetFullPath($CertRoot)
$env:SONA_CERT_ROOT = $ResolvedCertRoot
$Phases = if ($SkipLanguageCertification) {
    "native,gates,extension,packaging"
} else {
    "python,native,gates,extension,packaging"
}

Push-Location $RepoRoot
try {
    & python tools/release/certify_0153.py `
        --cert-root $ResolvedCertRoot `
        --phases $Phases
    if ($LASTEXITCODE -ne 0) {
        throw "Sona 0.15.3 release hardening failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}
