# PyInstaller Onedir Build Spike - Tasks 313-318

> Build spike. PyInstaller was used locally for verification and was not added
> to runtime dependencies.
> Generated: 2026-06-10

## Goal

Verify whether the current Windows desktop app can be packaged with a minimal
PyInstaller `--onedir` build and launched with the existing exit timer.

## Build Command

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --onedir --windowed --name QuantStrategyLab --add-data "sample_data;sample_data" app/main.py
```

Local PyInstaller version:

```text
6.20.0
```

PyInstaller is currently installed in the local virtual environment only. It was
not added to `pyproject.toml`.

## Build Result

| Property | Observed result |
|---|---|
| Build status | Success |
| Output folder | `dist/QuantStrategyLab/` |
| Executable | `dist/QuantStrategyLab/QuantStrategyLab.exe` |
| Executable size | 16,781,296 bytes |
| Onedir file size total | 404,246,592 bytes |
| Sample CSV bundled | `dist/QuantStrategyLab/_internal/sample_data/sample_ohlcv.csv` |
| Generated spec | `QuantStrategyLab.spec` |
| Generated build folder | `build/QuantStrategyLab/` |

## Packaged Launch Result

The packaged executable was launched with the existing timer and offscreen Qt
configuration:

```powershell
$env:QSL_EXIT_AFTER_MS='100'
$env:QT_QPA_PLATFORM='offscreen'
$p = Start-Process -FilePath .\dist\QuantStrategyLab\QuantStrategyLab.exe -Wait -PassThru -WindowStyle Hidden
$p.ExitCode
```

Observed result:

```text
0
```

This verifies that the packaged executable can start and exit cleanly in the
local Windows environment. It does not yet verify the full manual UI workflow
from the packaged app.

## Warnings and Gaps

| Item | Status | Next action |
|---|---|---|
| PySide6 platform plugins | No missing Qt platform plugin error observed during offscreen launch. | Keep an exe launch smoke in the next packaging task. |
| Sample data bundled | The CSV exists under `_internal/sample_data`. | Verify whether UI import/help paths should point to bundled data or external sample data. |
| Build artifacts | `dist/`, `build/`, and `QuantStrategyLab.spec` are generated locally. | Do not commit generated build outputs. Decide whether to commit a reviewed spec file later. |
| Size | Onedir output is about 404 MB. | Accept for first packaging validation; optimize later. |
| PyInstaller warnings | Warning file includes many optional missing modules. | Review only if packaged workflow fails; do not treat generic optional warnings as blockers. |

## Current Verification Still Passing

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q
```

Observed result:

```text
16 passed
```

## Recommendation

Accept PyInstaller `--onedir` as the first packaging implementation path.

The next task should turn this ad hoc command into a small reviewed build path,
while keeping generated outputs out of git.

## Next Recommended Task

Tasks 319-324 - PyInstaller Build Script and Artifact Hygiene

Do:

1. Add a small build script or documented command for the verified `--onedir`
   build.
2. Add `.gitignore` entries for generated PyInstaller outputs if they are not
   already ignored.
3. Decide whether `QuantStrategyLab.spec` should be committed now or generated
   by the build command.
4. Add or document a packaged-exe launch smoke using `QSL_EXIT_AFTER_MS`.
5. Keep `pyinstaller` out of runtime dependencies.

Do not:

1. Commit `dist/` or `build/`.
2. Add installer publishing.
3. Add `--onefile` before the `--onedir` workflow is repeatable.
