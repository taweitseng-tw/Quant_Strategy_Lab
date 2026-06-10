# Quant Strategy Lab Packaged App Quickstart - Tasks 325-330

> Windows onedir package quickstart.
> Generated: 2026-06-10

## Purpose

This guide explains how to build and launch the current Windows packaged app.
The package is a local PyInstaller `--onedir` build, not an installer and not a
single-file executable.

Quant Strategy Lab is for research and backtesting only. Backtested performance
does not guarantee future results. This software does not provide investment
advice and does not place live trades.

## Build

From the repository root, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_package.ps1
```

Expected successful output includes:

```text
SUCCESS: dist/QuantStrategyLab/QuantStrategyLab.exe
Launch smoke: PASS (exit code 0)
```

The script uses the project virtual environment when `.\.venv\Scripts\python.exe`
exists. Install developer dependencies first if PyInstaller is missing:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .[dev]
```

## Output Location

After a successful build, the app appears at:

```text
dist/QuantStrategyLab/QuantStrategyLab.exe
```

The package also contains an `_internal/` folder with Python, third-party
libraries, Qt files, and bundled sample data. The output is large; the latest
local verification reported about 386 MB.

## Launch

Open this file from File Explorer:

```text
dist/QuantStrategyLab/QuantStrategyLab.exe
```

Or run it from PowerShell:

```powershell
.\dist\QuantStrategyLab\QuantStrategyLab.exe
```

For an automated launch smoke:

```powershell
$env:QSL_EXIT_AFTER_MS='100'
$env:QT_QPA_PLATFORM='offscreen'
$p = Start-Process -FilePath .\dist\QuantStrategyLab\QuantStrategyLab.exe -Wait -PassThru -WindowStyle Hidden
$p.ExitCode
```

Expected result:

```text
0
```

## First Workflow

1. Click `New Project` and choose a project folder.
2. Go to the `Data` page and click `Import OHLCV Data File`.
3. Import your own OHLCV CSV/TXT file, or browse to the bundled samples under:

```text
dist/QuantStrategyLab/_internal/sample_data/
```

Bundled sample files currently include:

```text
sample_ohlcv.csv
sample_txf.csv
```

4. Go to the `Build` page and run a GA or GP strategy search.
5. Go to the `Validate` page and click `Run`.
6. Go to the `Results` page to inspect ranking, trades, equity, and strategy
   details.
7. Use `Export Report` after validation enables report export.

## Troubleshooting

| Problem | Fix |
|---|---|
| PowerShell blocks the script | Use `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_package.ps1`. |
| PyInstaller is missing | Run `.\.venv\Scripts\python.exe -m pip install -e .[dev]`. |
| Package is large | This is expected for the first PySide6, pandas, numpy, matplotlib, and pyqtgraph onedir build. |
| Qt platform plugin error | Re-run the launch smoke with `QT_QPA_PLATFORM=offscreen` and capture stderr. |
| Sample data is hard to find | Browse to `dist/QuantStrategyLab/_internal/sample_data/`, or use any valid OHLCV CSV/TXT from your file system. |

## Current Limits

- Windows only.
- No MSI or installer yet.
- No `--onefile` package yet.
- No auto-update.
- The packaged launch smoke is verified, but a full manual packaged-app
  walkthrough is still recommended before a formal release tag.
