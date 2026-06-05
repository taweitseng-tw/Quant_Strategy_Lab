param(
    [switch]$Quick
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

Write-Host "Quant Strategy Lab smoke verification"
Write-Host "Root: $root"
Write-Host "Mode: $(if ($Quick) { 'Quick' } else { 'Full' })"

$python = "python"
if (Test-Path ".venv/Scripts/python.exe") {
    $python = ".venv/Scripts/python.exe"
}

Write-Host ""
Write-Host "== Python =="
& $python --version

Write-Host ""
Write-Host "== Compile Check =="
$compileTargets = @("app", "core", "data_engine", "strategy_engine", "backtest_engine", "validation_engine", "repository", "reports", "tests")
$existingTargets = $compileTargets | Where-Object { Test-Path $_ }
if ($existingTargets.Count -eq 0) {
    Write-Host "No compile targets found."
} else {
    & $python -m compileall @existingTargets
}

Write-Host ""
Write-Host "== Pytest =="
if (-not (Test-Path "tests")) {
    Write-Host "No tests directory found."
    exit 0
}

if ($Quick) {
    $quickTests = @(
        "tests/test_resampler.py",
        "tests/test_formula_parser.py",
        "tests/test_backtest_engine.py"
    ) | Where-Object { Test-Path $_ }

    if ($quickTests.Count -eq 0) {
        Write-Host "No quick test targets found. Falling back to all tests."
        & $python -m pytest tests -q
    } else {
        & $python -m pytest @quickTests -q
    }
} else {
    & $python -m pytest tests -q
}

Write-Host ""
Write-Host "Smoke verification completed."

