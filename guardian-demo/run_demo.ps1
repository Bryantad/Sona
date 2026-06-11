Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$DemoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutputRoot = Join-Path $DemoRoot "output"
$StateRoot = Join-Path $DemoRoot ".sona"
$AppPath = Join-Path $DemoRoot "app.sona"
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Invoke-DemoCommand {
    param(
        [string]$Name,
        [string[]]$Arguments
    )

    Write-Host "== $Name =="
    $output = & python -m sona @Arguments --project-root $DemoRoot 2>&1
    $exitCode = $LASTEXITCODE
    $text = ($output | Out-String).Trim()
    $text | Set-Content -LiteralPath (Join-Path $OutputRoot "$Name.json") -Encoding UTF8
    Write-Host $text
    if ($exitCode -ne 0) {
        throw "Command failed with exit code ${exitCode}: python -m sona $($Arguments -join ' ')"
    }
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
if (Test-Path $StateRoot) {
    Remove-Item -LiteralPath $StateRoot -Recurse -Force
}

[System.IO.File]::WriteAllText($AppPath, "print(""Guardian demo: known-good application"")`n", $Utf8NoBom)

Invoke-DemoCommand "01-init" @("guard", "init")
Invoke-DemoCommand "02-snapshot-known-good" @("guard", "snapshot", "--name", "known-good")
Invoke-DemoCommand "03-status" @("guard", "status")
Invoke-DemoCommand "04-verify-clean" @("guard", "verify")

[System.IO.File]::AppendAllText($AppPath, "print(""unexpected drift: changed after known-good snapshot"")`n", $Utf8NoBom)
Write-Host "== changed watched file =="
Write-Host "app.sona now contains an unexpected extra line."

Invoke-DemoCommand "05-verify-drift" @("guard", "verify")
Invoke-DemoCommand "06-diff" @("guard", "diff")
Invoke-DemoCommand "07-heal-apply" @("guard", "heal", "--apply")
Invoke-DemoCommand "08-status-restored" @("guard", "status")
Invoke-DemoCommand "09-verify-restored" @("guard", "verify")

Write-Host "== final app.sona =="
Get-Content -LiteralPath $AppPath
Write-Host "== demo output =="
Write-Host $OutputRoot
