# PowerShell shim for Sona CLI
# Forwards arguments reliably to the project's Python interpreter.
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    $RemainingArgs
)

function Resolve-PythonExe {
    # Prefer virtualenv python if present
    $venvPath = Join-Path -Path $PSScriptRoot -ChildPath ".venv\Scripts\python.exe"
    if (Test-Path $venvPath) { return $venvPath }

    # Try common venv path
    $venvPath2 = Join-Path -Path $PSScriptRoot -ChildPath "venv\Scripts\python.exe"
    if (Test-Path $venvPath2) { return $venvPath2 }

    # Prefer system 'python' if available
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $pyCmd) { return "python" }

    # Fallback to Python Launcher 'py -3' if available
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $pyLauncher) { return @("py", "-3") }

    # Last resort, attempt 'python' anyway (may fail)
    return "python"
}

$pythonExe = Resolve-PythonExe

# Convert RemainingArgs (an array) to a list (avoid clobbering $args automatic var)
if ($null -eq $RemainingArgs) {
    $forwardArgs = @()
}
elseif ($RemainingArgs -is [System.Array]) {
    $forwardArgs = $RemainingArgs
}
else {
    $forwardArgs = @($RemainingArgs)
}

# debug prints removed

if ($forwardArgs.Count -ge 2 -and $forwardArgs[0] -eq "-m") {
    # module name is the second token
    $module = $forwardArgs[1]
    if ([string]::IsNullOrEmpty($module)) {
        Write-Error "Missing module name after -m"
        exit 2
    }
    if ($forwardArgs.Count -gt 2) {
        $moduleArgs = $forwardArgs[2..($forwardArgs.Count - 1)]
    }
    else {
        $moduleArgs = @()
    }
    # Check if the module is importable in the chosen python executable
    function Test-ModuleExists {
        param($pyExe, $mod)
        # Use Start-Process to capture exit code; expand $mod into the Python command string
        $pyCmd = "import importlib,sys; sys.exit(0 if importlib.util.find_spec('$mod') else 1)"
        & $pyExe -c $pyCmd
        return ($LASTEXITCODE -eq 0)
    }

    $selectedPython = $pythonExe
    if (-not (Test-ModuleExists $selectedPython $module)) {
        Write-Host "Module '$module' not found in $selectedPython; trying system 'python'..."
        if (Test-ModuleExists "python" $module) {
            $selectedPython = "python"
        }
        else {
            Write-Error "Module '$module' is not installed in the virtualenv or system python. Please install it (e.g. pip install $module) or run tests with an interpreter that has it." 
            exit 3
        }
    }

    if ($selectedPython -is [System.Array]) {
        & $selectedPython[0] $selectedPython[1] -m $module @moduleArgs
    }
    else {
        & $selectedPython -m $module @moduleArgs
    }
    exit $LASTEXITCODE
}
else {
    # Run the CLI script directly
    $cliPath = Join-Path $PSScriptRoot "cli.py"
    if ($pythonExe -is [System.Array]) {
        & $pythonExe[0] $pythonExe[1] $cliPath @forwardArgs
    }
    else {
        & $pythonExe $cliPath @forwardArgs
    }
    exit $LASTEXITCODE
}
