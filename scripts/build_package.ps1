# Build packaged Quant Strategy Lab desktop executable
# Requires: pyinstaller (pip install -e .[dev])
# Output: dist/QuantStrategyLab/QuantStrategyLab.exe

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$Name = "QuantStrategyLab"
$EntryPoint = "app/main.py"
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

Write-Host "Building $Name package..." -ForegroundColor Cyan

& $Python -m PyInstaller `
    --noconfirm `
    --onedir `
    --windowed `
    --name $Name `
    --add-data "sample_data;sample_data" `
    $EntryPoint

if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: dist/$Name/$Name.exe" -ForegroundColor Green
} else {
    Write-Host "FAILED: PyInstaller exited with code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

$ExePath = "dist/$Name/$Name.exe"
if (-not (Test-Path $ExePath)) {
    Write-Host "FAILED: expected executable not found at $ExePath" -ForegroundColor Red
    exit 1
}

Write-Host "Total size: $( (Get-ChildItem -Recurse dist/$Name | Measure-Object -Property Length -Sum).Sum / 1MB -as [int] ) MB" -ForegroundColor Green

# Quick smoke: launch with exit timer
$env:QSL_EXIT_AFTER_MS = "100"
$env:QT_QPA_PLATFORM = "offscreen"
$ExitCode = $null
try {
    $p = Start-Process -FilePath $ExePath -Wait -PassThru -WindowStyle Hidden
    $ExitCode = $p.ExitCode
} catch {
    Write-Host "Start-Process launch smoke failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "Retrying launch smoke with direct invocation..." -ForegroundColor Yellow
    & $ExePath
    $ExitCode = $LASTEXITCODE
}
if ($ExitCode -eq 0) {
    Write-Host "Launch smoke: PASS (exit code 0)" -ForegroundColor Green
} else {
    Write-Host "Launch smoke: FAIL (exit code $ExitCode)" -ForegroundColor Red
    exit $ExitCode
}
