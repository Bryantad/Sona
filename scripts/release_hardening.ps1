param(
    [string]$ExpectedVersion = "0.15.0"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-Condition {
    param(
        [bool]$Condition,
        [string]$Message
    )
    if (-not $Condition) {
        throw $Message
    }
}

function Invoke-Checked {
    param(
        [string]$FilePath,
        [string[]]$ArgumentList = @(),
        [string]$WorkingDirectory = ""
    )

    if ($WorkingDirectory) {
        Push-Location $WorkingDirectory
        try {
            & $FilePath @ArgumentList
            $exitCode = $LASTEXITCODE
        } finally {
            Pop-Location
        }
    } else {
        & $FilePath @ArgumentList
        $exitCode = $LASTEXITCODE
    }

    if ($exitCode -ne 0) {
        throw "Command failed with exit code ${exitCode}: $FilePath $($ArgumentList -join ' ')"
    }
}

function Invoke-CheckedOutput {
    param(
        [string]$FilePath,
        [string[]]$ArgumentList = @(),
        [string]$WorkingDirectory = ""
    )

    if ($WorkingDirectory) {
        Push-Location $WorkingDirectory
        try {
            $output = & $FilePath @ArgumentList 2>&1
            $exitCode = $LASTEXITCODE
        } finally {
            Pop-Location
        }
    } else {
        $output = & $FilePath @ArgumentList 2>&1
        $exitCode = $LASTEXITCODE
    }

    if ($exitCode -ne 0) {
        $text = ($output | Out-String).Trim()
        throw "Command failed with exit code ${exitCode}: $FilePath $($ArgumentList -join ' ')`n$text"
    }
    return ($output | Out-String).Trim()
}

function Reset-Directory {
    param([string]$Path)
    if (Test-Path $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Get-ArtifactInfo {
    param([System.IO.FileInfo]$File)
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $File.FullName).Hash.ToLowerInvariant()
    [PSCustomObject]@{
        Path = $File.FullName
        Size = $File.Length
        Sha256 = $hash
    }
}

function Invoke-PythonInspector {
    param(
        [string]$Script,
        [string[]]$Arguments
    )
    $Script | & python - @Arguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "Python artifact inspector failed with exit code $exitCode."
    }
}

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$DistDir = Join-Path $RepoRoot "dist-pypi-$ExpectedVersion"
$HardeningDir = Join-Path $RepoRoot "build\release-hardening\$ExpectedVersion"
$ExternalSmokeRoot = Join-Path ([System.IO.Path]::GetTempPath()) "sona-release-hardening-$ExpectedVersion"
$WheelVenvDir = Join-Path $ExternalSmokeRoot "wheel-venv"
$SdistVenvDir = Join-Path $ExternalSmokeRoot "sdist-venv"
$WheelSmokeDir = Join-Path $ExternalSmokeRoot "wheel-smoke-workdir"
$SdistSmokeDir = Join-Path $ExternalSmokeRoot "sdist-smoke-workdir"
$resolvedRepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
$resolvedExternalSmokeRoot = [System.IO.Path]::GetFullPath($ExternalSmokeRoot)
Assert-Condition (-not $resolvedExternalSmokeRoot.StartsWith($resolvedRepoRoot, [System.StringComparison]::OrdinalIgnoreCase)) "Clean-install smoke root must be outside the repository: $ExternalSmokeRoot"

Write-Host "== Phase 1: fast release gate =="
Invoke-Checked "powershell" @(
    "-ExecutionPolicy", "Bypass",
    "-File", (Join-Path $RepoRoot "scripts\release_gate.ps1")
) $RepoRoot

Write-Host "== Phase 2: clean Python artifact build =="
Invoke-Checked "python" @("-m", "build", "--version") $RepoRoot
Reset-Directory $DistDir
Reset-Directory $HardeningDir
Reset-Directory $ExternalSmokeRoot
New-Item -ItemType Directory -Force -Path $WheelSmokeDir | Out-Null
New-Item -ItemType Directory -Force -Path $SdistSmokeDir | Out-Null
Invoke-Checked "python" @("-m", "build", "--wheel", "--sdist", "--no-isolation", "--outdir", $DistDir) $RepoRoot

$wheelFiles = @(Get-ChildItem -LiteralPath $DistDir -File | Where-Object { $_.Name -like "*.whl" })
$sdistFiles = @(Get-ChildItem -LiteralPath $DistDir -File | Where-Object { $_.Name -like "*.tar.gz" })
Assert-Condition ($wheelFiles.Count -eq 1) "Expected exactly one wheel in $DistDir; found $($wheelFiles.Count)."
Assert-Condition ($sdistFiles.Count -eq 1) "Expected exactly one sdist in $DistDir; found $($sdistFiles.Count)."
$Wheel = $wheelFiles[0]
$Sdist = $sdistFiles[0]
Assert-Condition ($Wheel.Name -like "*$ExpectedVersion*") "Wheel name does not contain ${ExpectedVersion}: $($Wheel.Name)"
Assert-Condition ($Sdist.Name -like "*$ExpectedVersion*") "Sdist name does not contain ${ExpectedVersion}: $($Sdist.Name)"

Write-Host "== Phase 3: Python archive inspection =="
$pythonArchiveInspector = @'
import email.parser
import sys
import tarfile
import zipfile

wheel_path, sdist_path, expected_version = sys.argv[1:4]

foundation_modules = {
    "queue", "stack", "sort", "search", "statistics", "matrix", "graph",
    "permissions", "hashing", "random", "uuid", "secrets", "password", "jwt",
    "crypto",
}
forbidden_roots = {
    "docs", "examples", "tests", "extensions", "vscode-extension", "scratch",
}
forbidden_suffixes = (".vsix", ".pyc", ".pyo", ".tmp", ".bak")


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def normalize_sdist_name(name: str) -> str:
    name = name.replace("\\", "/").lstrip("./")
    parts = [part for part in name.split("/") if part]
    if len(parts) > 1:
        return "/".join(parts[1:])
    return "/".join(parts)


def reject_forbidden(paths: set[str], label: str) -> None:
    for path in paths:
        normalized = path.strip("/")
        if not normalized:
            continue
        parts = normalized.split("/")
        root = parts[0]
        leaf = parts[-1]
        if root in forbidden_roots:
            fail(f"{label} contains forbidden root content: {path}")
        if "__pycache__" in parts:
            fail(f"{label} contains __pycache__: {path}")
        if leaf == ".DS_Store" or leaf.endswith(forbidden_suffixes):
            fail(f"{label} contains forbidden file: {path}")


def require_path(paths: set[str], required: str, label: str) -> None:
    if required not in paths:
        fail(f"{label} missing required path: {required}")


def require_stdlib_sources(paths: set[str], label: str) -> None:
    for module in sorted(foundation_modules):
        candidates = {f"stdlib/{module}.smod", f"sona/stdlib/{module}.smod"}
        if not (paths & candidates):
            fail(f"{label} missing packaged .smod source for {module}")


with zipfile.ZipFile(wheel_path) as wheel:
    wheel_paths = {info.filename.replace("\\", "/").strip("/") for info in wheel.infolist()}
    reject_forbidden(wheel_paths, "wheel")
    require_path(wheel_paths, "sona/stdlib/MANIFEST.json", "wheel")
    require_path(wheel_paths, "sona/stdlib/native_intrinsics.py", "wheel")
    require_stdlib_sources(wheel_paths, "wheel")
    metadata_names = [name for name in wheel_paths if name.endswith(".dist-info/METADATA")]
    if len(metadata_names) != 1:
        fail(f"wheel expected exactly one METADATA file; found {len(metadata_names)}")
    metadata = email.parser.Parser().parsestr(
        wheel.read(metadata_names[0]).decode("utf-8", errors="replace")
    )
    if metadata.get("Version") != expected_version:
        fail(f"wheel metadata version {metadata.get('Version')!r} != {expected_version!r}")

with tarfile.open(sdist_path, "r:gz") as sdist:
    raw_paths = {member.name.replace("\\", "/").strip("/") for member in sdist.getmembers()}
    sdist_paths = {normalize_sdist_name(name) for name in raw_paths}
    reject_forbidden(sdist_paths, "sdist")
    require_path(sdist_paths, "sona/stdlib/MANIFEST.json", "sdist")
    require_path(sdist_paths, "sona/stdlib/native_intrinsics.py", "sdist")
    require_stdlib_sources(sdist_paths, "sdist")

print("Python archive inspection passed.")
'@
Invoke-PythonInspector $pythonArchiveInspector @($Wheel.FullName, $Sdist.FullName, $ExpectedVersion)

function Invoke-InstallSmoke {
    param(
        [System.IO.FileInfo]$Artifact,
        [string]$Label,
        [string]$VenvDir,
        [string]$SmokeDir
    )

    Write-Host "== Phase 4: fresh $Label installation =="
    Invoke-Checked "python" @("-m", "venv", $VenvDir) $RepoRoot | Out-Host
    if ($env:OS -eq "Windows_NT") {
        $venvPython = Join-Path $VenvDir "Scripts\python.exe"
    } else {
        $venvPython = Join-Path $VenvDir "bin/python"
    }
    Assert-Condition (Test-Path $venvPython) "Venv Python not found: $venvPython"
    Invoke-Checked $venvPython @("-m", "pip", "install", "--disable-pip-version-check", $Artifact.FullName) $SmokeDir | Out-Host
    $versionOutput = Invoke-CheckedOutput $venvPython @("-m", "sona", "--version") $SmokeDir
    Assert-Condition ($versionOutput -match [regex]::Escape($ExpectedVersion)) "$Label version output missing ${ExpectedVersion}: $versionOutput"
    Invoke-Checked $venvPython @("-m", "sona", "probe", "stdlib") $SmokeDir | Out-Host
    Invoke-Checked $venvPython @("-m", "sona", "probe", "stdlib", "--category", "accessibility") $SmokeDir | Out-Host
    Invoke-Checked $venvPython @("-m", "sona", "probe", "stdlib", "--category", "resilience") $SmokeDir | Out-Host
    Invoke-Checked $venvPython @("-m", "sona", "build-info") $SmokeDir | Out-Host
    $importPath = Invoke-CheckedOutput $venvPython @("-c", "import pathlib, sona; print(pathlib.Path(sona.__file__).resolve())") $SmokeDir
    $resolvedImportPath = [System.IO.Path]::GetFullPath($importPath)
    $resolvedVenvPath = [System.IO.Path]::GetFullPath($VenvDir)
    Assert-Condition ($resolvedImportPath.StartsWith($resolvedVenvPath, [System.StringComparison]::OrdinalIgnoreCase)) "$Label sona.__file__ is not inside the temp venv: $resolvedImportPath"

    $stableImportScript = @'
from pathlib import Path
from sona.interpreter import SonaUnifiedInterpreter
stable_modules = [
    "path", "format", "color", "assert", "uuid", "url", "csv", "pipe",
    "intent", "focus", "log", "profile", "simplify", "breadcrumb", "flow",
    "explain", "pace", "affirm", "chunk", "timer", "noise", "tone",
    "readability", "linewidth", "mirror", "chunk_read", "contract",
    "boundary", "routine", "strict", "certainty", "sensory", "guardian",
]
interp = SonaUnifiedInterpreter(project_root=Path.cwd())
for name in stable_modules:
    interp.module_system.import_module(name)
for hidden in ["native_bridge", "native_intrinsics", "intrinsics"]:
    try:
        interp.module_system.import_module(hidden)
    except Exception:
        continue
    raise SystemExit(f"hidden module import unexpectedly succeeded: {hidden}")
print("stable imports and hidden-module checks passed")
'@
    Push-Location $SmokeDir
    try {
        $stableImportScript | & $venvPython - | Out-Host
        if ($LASTEXITCODE -ne 0) {
            throw "$Label stable import smoke failed with exit code $LASTEXITCODE."
        }
    } finally {
        Pop-Location
    }

    $guardianRoot = Join-Path $SmokeDir "guardian-fixture"
    New-Item -ItemType Directory -Force -Path $guardianRoot | Out-Null
    try {
        Set-Content -LiteralPath (Join-Path $guardianRoot "app.sona") -Value 'print("guardian fixture")' -Encoding UTF8
        Invoke-Checked $venvPython @("-m", "sona", "guard", "init", "--project-root", $guardianRoot) $SmokeDir | Out-Host
        Invoke-Checked $venvPython @("-m", "sona", "guard", "status", "--project-root", $guardianRoot) $SmokeDir | Out-Host
        Invoke-Checked $venvPython @("-m", "sona", "guard", "verify", "--project-root", $guardianRoot) $SmokeDir | Out-Host
        Invoke-Checked $venvPython @("-m", "sona", "guard", "doctor", "--project-root", $guardianRoot) $SmokeDir | Out-Host
    } finally {
        if (Test-Path $guardianRoot) {
            Remove-Item -LiteralPath $guardianRoot -Recurse -Force
        }
    }

    [PSCustomObject]@{
        Label = $Label
        VersionOutput = $versionOutput
        ImportPath = $resolvedImportPath
    }
}

$WheelSmoke = Invoke-InstallSmoke $Wheel "wheel" $WheelVenvDir $WheelSmokeDir
$SdistSmoke = Invoke-InstallSmoke $Sdist "sdist" $SdistVenvDir $SdistSmokeDir

& python -c "import importlib.util; raise SystemExit(0 if importlib.util.find_spec('twine') else 1)"
$twineExit = $LASTEXITCODE
if ($twineExit -eq 0) {
    Write-Host "== Optional: twine metadata check =="
    Invoke-Checked "python" @("-m", "twine", "check", "--strict", (Join-Path $DistDir "*")) $RepoRoot
} else {
    Write-Host "Skipping optional twine check; twine is not installed."
}

Write-Host "== Phase 7: artifact integrity summary =="
$WheelInfo = Get-ArtifactInfo $Wheel
$SdistInfo = Get-ArtifactInfo $Sdist

Write-Host "Release hardening passed for Sona $ExpectedVersion"
Write-Host ("Wheel: {0}" -f $WheelInfo.Path)
Write-Host ("  Size: {0}" -f $WheelInfo.Size)
Write-Host ("  SHA-256: {0}" -f $WheelInfo.Sha256)
Write-Host ("Sdist: {0}" -f $SdistInfo.Path)
Write-Host ("  Size: {0}" -f $SdistInfo.Size)
Write-Host ("  SHA-256: {0}" -f $SdistInfo.Sha256)
Write-Host ("Confirmed wheel runtime version: {0}" -f $WheelSmoke.VersionOutput)
Write-Host ("Confirmed sdist runtime version: {0}" -f $SdistSmoke.VersionOutput)
Write-Host ("Wheel smoke-test import path: {0}" -f $WheelSmoke.ImportPath)
Write-Host ("Sdist smoke-test import path: {0}" -f $SdistSmoke.ImportPath)
Write-Host ("External smoke root: {0}" -f $ExternalSmokeRoot)
