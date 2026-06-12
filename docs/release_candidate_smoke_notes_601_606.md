# Release Candidate Smoke and Artifact Notes - Tasks 601-606

Date: 2026-06-12

## Decision

PASS after Codex review cleanup.

The current developer release candidate has a reproducible local smoke path for
startup, sample data workflow, PyInstaller onedir packaging, and packaged launch
smoke. No production code was changed in this documentation round.

## Verified Commands

### Desktop Smoke Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py -q
```

Expected result:

- `12 passed`

### Package Build and Launch Smoke

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_package.ps1
```

Expected result:

- PyInstaller builds `dist/QuantStrategyLab/QuantStrategyLab.exe`.
- The script runs the short launch smoke with `QSL_EXIT_AFTER_MS=100`.
- The script reports `Launch smoke: PASS (exit code 0)`.

Do not bypass `scripts/build_package.ps1` with an ad hoc PyInstaller command in
release verification. The script is the release path and includes the launch
smoke fallback behavior.

### Whitespace Check

```powershell
git diff --check
```

Expected result:

- No whitespace errors.
- CRLF warnings are acceptable in this repository.

## Artifact Handling

| Item | Current Rule |
|---|---|
| Build output | `dist/QuantStrategyLab/` |
| Executable | `dist/QuantStrategyLab/QuantStrategyLab.exe` |
| CI artifact | `QuantStrategyLab-windows-onedir` |
| CI upload path | `dist/QuantStrategyLab/` |
| Local release artifacts | Keep under `release_artifacts/` and do not stage |
| Generated build files | `dist/`, `build/`, and `*.spec` stay untracked/ignored |

## Remaining Release Risks

- The executable is unsigned and may trigger Windows SmartScreen warnings.
- Distribution is PyInstaller onedir, not a single-file exe or installer.
- CI uploads a workflow artifact but does not create a GitHub Release page.
- CI tag-run behavior still needs confirmation after the first pushed `v*` tag.
- Qt/offscreen behavior on GitHub's Windows runner should be watched on the
  first tag build.

## Tag Readiness

The repo is close to a developer release tag, but the tag should not be created
by a model task unless the user explicitly requests it. The next safe step is a
short tag-readiness decision that confirms:

- working tree cleanliness,
- latest release notes/changelog scope,
- current version/tag naming alignment,
- artifact handling instructions,
- whether the user wants to create and push `v0.4.0-dev`.

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

## Next Recommendation

Proceed to Tasks 607-612: Developer Release Tag Readiness Decision. Keep that
round decision-only unless the user explicitly approves creating or pushing a
tag.
