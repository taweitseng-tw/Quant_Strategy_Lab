# Developer Release Tag Readiness Decision - Tasks 607-612

Date: 2026-06-12

## Decision

READY TO TAG after this decision document is committed.

The repository is ready for a developer pre-release tag, provided the user
explicitly approves tag creation. This task did not create, push, delete, or move
any git tag.

## Proposed Tag

| Property | Value |
|---|---|
| Tag name | `v0.4.0-dev` |
| Tag type | Annotated git tag |
| Target commit | The commit that includes this readiness decision |
| Python package version | `0.4.0.dev0` |
| Release type | Developer pre-release, not public 1.0 |

Proposed tag message:

```text
v0.4.0-dev - Developer pre-release with async validation, cancellation support, session-aware quality gaps, structured quality issues, English quickstart, and CI packaging.
```

## Readiness Checks

| Check | Status | Notes |
|---|---|---|
| Existing `v0.4.0*` tag | PASS | No matching local tag was found during review. |
| Version/tag alignment | PASS | `pyproject.toml` uses PEP 440 `0.4.0.dev0`; proposed git tag uses `v0.4.0-dev`. |
| CI tag trigger | PASS | `.github/workflows/ci.yml` includes `v*` tag pushes and package job guard. |
| Package script | PASS | `scripts/build_package.ps1` builds onedir output and runs launch smoke. |
| Smoke tests | PASS | Focused startup and sample workflow smoke tests pass locally. |
| Artifact handling | PASS | `dist/`, `build/`, `*.spec`, and `release_artifacts/` remain untracked/ignored. |

## Remaining Non-Blocking Risks

- The Windows executable is unsigned.
- The package is PyInstaller onedir, not a single-file executable or installer.
- GitHub Actions uploads an artifact but does not create a GitHub Release page.
- The first pushed `v*` tag still needs live CI observation.

These are acceptable for a developer pre-release and must not be described as a
stable public 1.0 release.

## Verification

Commands run:

```powershell
git tag --list "v0.4.0*"
.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py -q
git diff --check
```

Results:

- No local `v0.4.0*` tag exists.
- `12 passed`
- `git diff --check` passed with CRLF warnings only.

## Next Safe Action

Ask the user whether Codex should create the local annotated tag
`v0.4.0-dev`. Do not delegate git tag creation to another model unless the user
explicitly asks for that workflow.

Suggested command only after user approval:

```powershell
git tag -a v0.4.0-dev -m "v0.4.0-dev - Developer pre-release with async validation, cancellation support, session-aware quality gaps, structured quality issues, English quickstart, and CI packaging."
```
