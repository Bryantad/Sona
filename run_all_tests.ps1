#!/usr/bin/env pwsh
# Sona 0.10.1 Test Suite Runner for PowerShell
# Delegates to the Python runner for coverage compatibility.

python tools/run_all_tests.py @args
exit $LASTEXITCODE
