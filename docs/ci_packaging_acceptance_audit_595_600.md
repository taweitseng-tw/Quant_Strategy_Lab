# CI Packaging and Version Acceptance Audit - Tasks 595-600

Date: 2026-06-12

## Decision

PASS after Codex review cleanup.

The CI packaging and version changes from Tasks 589-594 are acceptable for the
current developer release path. The package job is tag-triggered, uses the
existing package script, uploads the onedir artifact, and keeps the smoke job
unchanged.

No production app logic was changed in this audit round.

## Acceptance Checks

### GitHub Actions Trigger

Status: PASS

- `.github/workflows/ci.yml` keeps push and pull request smoke coverage for
  `master`.
- Tag pushes matching `v*` are included under `on.push.tags`.
- The `package` job also has `if: startsWith(github.ref, 'refs/tags/v')`, so it
  does not run for ordinary branch pushes or pull requests.

### Smoke Job

Status: PASS

- The existing smoke job still installs with `python -m pip install -e .[dev]`.
- The existing smoke command remains focused on startup, sample data workflow,
  and archive import preview acceptance tests.

### Package Job

Status: PASS

- The package job runs on `windows-latest` with Python 3.11.
- It installs dev dependencies before building.
- It calls `.\scripts\build_package.ps1` instead of duplicating packaging logic.
- It uploads `dist/QuantStrategyLab/` as `QuantStrategyLab-windows-onedir`.

### Version

Status: PASS

- `pyproject.toml` now declares `0.4.0.dev0`.
- The version is PEP 440-compatible and accurately signals a development build,
  not a final 1.0 release.

### Build Script Launch Smoke

Status: PASS

- `scripts/build_package.ps1` still performs the PyInstaller onedir build.
- The script verifies that `dist/QuantStrategyLab/QuantStrategyLab.exe` exists.
- The script runs a short `QSL_EXIT_AFTER_MS=100` launch smoke.
- If `Start-Process -WindowStyle Hidden` is blocked, the script falls back to
  direct invocation and checks the resulting exit code.

## Verification

Commands run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py -q
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_package.ps1
git diff --check
```

Results:

- `12 passed`
- Package build completed and launch smoke passed locally.
- `git diff --check` passed with CRLF warnings only.

## Remaining Release Risks

- The artifact is uploaded by GitHub Actions but not attached to a GitHub
  Release page.
- The executable is unsigned and may trigger Windows SmartScreen warnings.
- The distribution remains PyInstaller onedir, not a single-file executable or
  installer.
- The CI launch-smoke behavior depends on Qt/offscreen behavior on GitHub's
  Windows runner; this should be watched after the first tag push.

## Next Recommendation

Proceed to Tasks 601-606: Release Candidate Smoke and Artifact Notes. The next
round should verify the user-facing release path and document artifact handling,
not add new product features.
