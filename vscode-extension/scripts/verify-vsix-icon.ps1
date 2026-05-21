param(
    [string]$VsixPath = "",
    [switch]$SkipVsix
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression.FileSystem

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$pkgPath = Join-Path $root "package.json"
if (-not (Test-Path $pkgPath)) {
    throw "Missing package.json at $pkgPath"
}

$pkg = Get-Content $pkgPath -Raw | ConvertFrom-Json
if (-not $pkg.icon) {
    throw "package.json is missing the 'icon' field."
}

$iconRel = [string]$pkg.icon
$iconFsPath = Join-Path $root $iconRel
if (-not (Test-Path $iconFsPath)) {
    throw "Icon file missing: $iconFsPath"
}

$iconHash = (Get-FileHash -Algorithm SHA256 $iconFsPath).Hash
$iconBytes = [System.IO.File]::ReadAllBytes($iconFsPath)
if ($iconBytes.Length -lt 8) {
    throw "Icon file is too small to be a PNG: $iconFsPath"
}
$pngSignature = [byte[]](137,80,78,71,13,10,26,10)
for ($i = 0; $i -lt 8; $i++) {
    if ($iconBytes[$i] -ne $pngSignature[$i]) {
        throw "Icon file is not a valid PNG signature: $iconFsPath"
    }
}

if ($SkipVsix) {
    Write-Host "Icon source check passed: $iconRel"
    return
}

if (-not $VsixPath) {
    $vsixName = "{0}-{1}.vsix" -f $pkg.name, $pkg.version
    $VsixPath = Join-Path $root $vsixName
}

if (-not (Test-Path $VsixPath)) {
    throw "VSIX file not found: $VsixPath"
}

$entryPath = "extension/" + ($iconRel -replace "\\", "/")
$zip = [System.IO.Compression.ZipFile]::OpenRead($VsixPath)
try {
    $entry = $zip.Entries | Where-Object { $_.FullName -eq $entryPath } | Select-Object -First 1
    if (-not $entry) {
        throw "VSIX is missing icon entry: $entryPath"
    }
    if ($entry.Length -le 0) {
        throw "VSIX icon entry is empty: $entryPath"
    }

    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ([System.IO.Path]::GetRandomFileName())
    try {
        $inStream = $entry.Open()
        $outStream = [System.IO.File]::Create($tmp)
        try {
            $inStream.CopyTo($outStream)
        } finally {
            $outStream.Dispose()
            $inStream.Dispose()
        }
        $vsixHash = (Get-FileHash -Algorithm SHA256 $tmp).Hash
        if ($vsixHash -ne $iconHash) {
            throw "VSIX icon does not match source icon hash."
        }
    } finally {
        if (Test-Path $tmp) {
            Remove-Item -Force $tmp
        }
    }
} finally {
    $zip.Dispose()
}

Write-Host "Icon verification passed for: $VsixPath"
