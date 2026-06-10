# PyInstaller Build Script and Artifact Hygiene - Tasks 319-324

> Artifact hygiene report. Generated packaging outputs must stay out of git.
> Generated: 2026-06-10

## Goal

Turn the verified PyInstaller `--onedir` command into a small repeatable local
build path and prevent generated packaging artifacts from being staged.

## Changes

| File | Change |
|---|---|
| `.gitignore` | Added `*.spec` so auto-generated PyInstaller spec files are ignored by default. Existing rules already ignore `build/`, `dist/`, and `*.exe`. |
| `pyproject.toml` | Added `pyinstaller` to the `dev` optional dependency group only. It was not added as a runtime dependency. |
| `scripts/build_package.ps1` | Added a Windows build script for the verified PyInstaller `--onedir` package and launch smoke. |

## Build Script

Recommended invocation on machines with restrictive PowerShell policy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_package.ps1
```

The script:

1. Uses `.\.venv\Scripts\python.exe` when present, falling back to `python`.
2. Runs PyInstaller with `--onedir`, `--windowed`, and bundled `sample_data`.
3. Verifies `dist/QuantStrategyLab/QuantStrategyLab.exe` is created.
4. Launches the packaged executable with `QSL_EXIT_AFTER_MS=100` and
   `QT_QPA_PLATFORM=offscreen`.
5. Fails if the packaged executable exits with a non-zero code.

## Verification Results

Direct script execution was blocked by local PowerShell execution policy:

```text
PSSecurityException: running scripts is disabled on this system
```

The Bypass invocation was verified successfully:

```text
SUCCESS: dist/QuantStrategyLab/QuantStrategyLab.exe
Total size: 386 MB
Launch smoke: PASS (exit code 0)
```

The standard smoke set also passed:

```text
16 passed
```

## Artifact Hygiene Decision

| Artifact | Decision |
|---|---|
| `dist/` | Ignored and must not be committed. |
| `build/` | Ignored and must not be committed. |
| `*.exe` | Ignored and must not be committed as source. |
| `*.spec` | Ignored for now because the current spec is auto-generated. A reviewed committed spec can be added later with an explicit exception. |

Generated `dist/`, `build/`, and `QuantStrategyLab.spec` outputs were removed
after local verification.

## Remaining Packaging Risks

1. The packaged executable launch smoke passes, but the full manual UI workflow
   from the packaged app still needs a walkthrough.
2. The bundled sample CSV exists under `_internal/sample_data`, but the user
   experience for finding sample data from the packaged app still needs review.
3. The `--onedir` output is large. Size optimization is deferred.
4. A committed, reviewed `.spec` file may still be useful once packaging options
   stabilize.

## Next Recommended Task

Tasks 325-330 - Packaged App Walkthrough and Quickstart Draft

Verify the packaged app manually enough to support a first formal desktop
quickstart:

1. Build with `scripts/build_package.ps1`.
2. Launch the packaged executable.
3. Confirm sample data import path expectations.
4. Draft a concise user quickstart with install, launch, sample-data import, and
   troubleshooting notes.
