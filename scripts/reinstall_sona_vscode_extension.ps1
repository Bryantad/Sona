param(
  [string]$VsixPath = "F:\SonaMinimal\vscode-extension\sona-ai-native-programming\sona-ai-native-programming-0.9.9.vsix",
  [string]$CodeCliPath = "",
  [switch]$AlsoUninstallRootExtension
)

$ErrorActionPreference = 'Stop'

function Resolve-CodeCliPath {
  param([string]$Provided)

  if ($Provided -and (Test-Path $Provided)) {
    return (Resolve-Path $Provided).Path
  }

  $cmd = Get-Command code.cmd -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }

  $candidates = @(
    "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd",
    "$env:ProgramFiles\Microsoft VS Code\bin\code.cmd",
    "$env:ProgramFiles(x86)\Microsoft VS Code\bin\code.cmd"
  )

  foreach ($p in $candidates) {
    if ($p -and (Test-Path $p)) { return (Resolve-Path $p).Path }
  }

  throw "VS Code CLI not found. Install VS Code and enable 'code' command in PATH, or pass -CodeCliPath."
}

$code = Resolve-CodeCliPath -Provided $CodeCliPath

if (-not (Test-Path $VsixPath)) {
  throw "VSIX not found: $VsixPath"
}

$aiExtId = 'Waycoreinc.sona-ai-native-programming'
$rootExtId = 'bryantad.sona-language-support'

Write-Host "Using VS Code CLI: $code"
Write-Host "Installing VSIX: $VsixPath"

Write-Host "\nListing current installed extensions (filtered)..."
& $code --list-extensions | Where-Object { $_ -match 'sona' } | ForEach-Object { Write-Host "  $_" }

Write-Host "\nUninstalling $aiExtId (ignore errors if not installed)..."
try { & $code --uninstall-extension $aiExtId } catch { Write-Host "  (uninstall warning) $($_.Exception.Message)" }

if ($AlsoUninstallRootExtension) {
  Write-Host "\nUninstalling $rootExtId (ignore errors if not installed)..."
  try { & $code --uninstall-extension $rootExtId } catch { Write-Host "  (uninstall warning) $($_.Exception.Message)" }
}

Write-Host "\nInstalling VSIX (forced)..."
& $code --install-extension $VsixPath --force

Write-Host "\nDone. Installed extensions (filtered):"
& $code --list-extensions | Where-Object { $_ -match 'sona' } | ForEach-Object { Write-Host "  $_" }

Write-Host "\nNext step in VS Code: run 'Developer: Reload Window', then open a .sona file and check Output -> 'Sona LSP'."
