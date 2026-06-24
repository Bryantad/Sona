param(
    [switch]$SkipVsix
)

$root = Split-Path -Parent $PSScriptRoot
$icon = Join-Path $root "assets/icon.png"

if (-not (Test-Path -LiteralPath $icon)) {
    Write-Error "Missing extension icon: $icon"
    exit 1
}

Write-Host "Extension icon found: $icon"

if (-not $SkipVsix) {
    Write-Host "VSIX package inspection skipped by this lightweight verifier."
}
