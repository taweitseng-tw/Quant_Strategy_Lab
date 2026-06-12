# Desktop Release Readiness Triage - Tasks 571-576

Date: 2026-06-12

## Decision

NOT READY for a formal 1.0 desktop release.

The project is suitable for continued developer-alpha validation, but the
remaining release work should shift from feature growth to release packaging,
user-facing setup clarity, documentation staging cleanup, and one final desktop
workflow proof.

No production code was changed in this triage round.

## Evidence Checked

Local evidence reviewed:

- `.github/workflows/ci.yml` exists and runs Windows smoke tests on `master`.
- `scripts/build_package.ps1` exists and builds a PyInstaller onedir package.
- `pyproject.toml` still declares `version = "0.0.1"`.
- The repository currently has 99 `tests/test_*.py` files.
- Focused desktop smoke tests passed locally:
  `tests/test_app_startup_smoke.py` and
  `tests/test_sample_data_workflow_smoke.py`.

## Must Fix Before 1.0

### 1. User-Facing README Quickstart

Status: Must fix.

The current release path needs a concise end-user quickstart that explains how
to install dependencies, launch the desktop app, use sample data, run
validation, and export a report. This is required before a formal desktop
release because users need a reproducible happy path.

Recommended next block: Tasks 577-582.

### 2. Documentation Staging Cleanup

Status: Must fix.

There are still historical documentation and agent artifacts that need an
explicit accept/hold/cleanup decision before release. This prevents release
notes and task history from depending on untracked or ambiguous artifacts.

Recommended block: Tasks 583-588.

### 3. Packaging Release Path

Status: Must fix.

`scripts/build_package.ps1` exists, but there is no verified release workflow
that builds and publishes an artifact for a tagged release. The project should
decide whether 1.0 accepts the current PyInstaller onedir output or requires a
different packaging shape.

Recommended block: Tasks 589-594.

### 4. Version and Release Checklist

Status: Must fix.

`pyproject.toml` still reports `0.0.1`. Before a formal release, the project
needs an intentional version target and a small release checklist that names the
commands and artifact expectations.

Recommended to include with the packaging block unless it becomes too large.

## Should Fix Before 1.0

### 1. End-to-End Desktop Workflow Smoke

Status: Should fix.

Existing focused smokes cover startup and sample data workflow. A final release
candidate should also have one narrow desktop workflow proof that exercises the
most important happy path from data to report without relying on manual review.

### 2. Code Signing Decision

Status: Should fix or explicitly defer.

Unsigned Windows desktop binaries may trigger trust warnings. If signing is not
available for 1.0, document the limitation rather than treating it as solved.

### 3. Packaging Size Review

Status: Should fix or explicitly defer.

The PyInstaller script uses onedir packaging. Size and distribution ergonomics
should be checked before release, but this does not need to block a controlled
developer-alpha package.

## Can Defer

- True mid-stage validation cancellation.
- Fine-grained validation progress callbacks.
- Multi-platform CI beyond Windows.
- Installer polish such as MSI or NSIS.
- Auto-update support.
- Full GA/GP product polish.
- Additional report explainability sections.

## Readiness Estimate

Formal 1.0 desktop readiness: approximately 60%.

Remaining work estimate:

- 3 near-term integrated 6-subtask blocks are already identified:
  - Tasks 577-582: README English quickstart.
  - Tasks 583-588: documentation staging cleanup.
  - Tasks 589-594: CI packaging job and version/release checklist.
- After those, expect roughly 5-13 additional 6-subtask review blocks for
  final packaging proof, release-candidate smoke coverage, cleanup, and final
  acceptance.

This estimate is intentionally conservative because packaging and release
verification often reveal environment-specific issues.

## Verification

Commands run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py -q
git diff --check
```

Results:

- `12 passed`
- `git diff --check` passed with CRLF warnings only.

## Next Recommendation

Proceed with Tasks 577-582: README English Quickstart. Keep the scope narrow and
do not change production code in that block.
