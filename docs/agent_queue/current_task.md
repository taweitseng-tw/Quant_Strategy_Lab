# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 057M-Impl + 057N-Design - Final 057 Acceptance Smoke and Release Readiness Triage Design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-06_task-057l-impl_057m-design_wf-equity-report-tables-and-acceptance-smoke-design_codex-review.md`
8. `docs/validation_expansion_acceptance_smoke_design_057M.md`
9. This task file

## Context

Batch 057L-Impl + 057M-Design was accepted by Codex. Bootstrap MC and WF equity now have engine/pipeline/UI/report surfaces. This batch should seal the 057 validation expansion chain with end-to-end acceptance smoke tests, then design the final release-readiness triage for this v0.2 validation expansion slice.

## Scope

### Do

- Complete two sequential tasks:
  - Task 057M-Impl - Final 057 Validation Expansion Acceptance Smoke
  - Task 057N-Design - 057/v0.2 Validation Expansion Release Readiness Triage Design
- For Task 057M-Impl:
  - Create `tests/test_validation_expansion_acceptance_smoke.py`.
  - Implement the 8 tests described in `docs/validation_expansion_acceptance_smoke_design_057M.md`.
  - Cover bootstrap MC pipeline opt-in, bootstrap widget/report visibility, bootstrap UI control wiring, WF equity widget/report visibility, default-off behavior, and empty-output omissions.
  - Prefer reusing existing fixtures/helpers from bootstrap, validation pipeline, UI wiring, widget, and report tests.
  - Keep this primarily test-only. Production code changes are allowed only if the new acceptance smoke exposes a real defect.
- For Task 057N-Design:
  - Create `docs/validation_expansion_release_readiness_triage_057N.md`.
  - Summarize the 056/057 validation expansion capabilities now covered.
  - Identify remaining risks, test gaps, and any release blockers for v0.2 alpha validation expansion.
  - Estimate whether the validation expansion slice is ready for final v0.2 release-readiness audit.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-057m-impl_057n-design_final-acceptance-smoke-and-release-readiness-triage_deepseek.md`

### Do Not

- Do not add new features.
- Do not add new dependencies.
- Do not broaden Monte Carlo, walk-forward, or report behavior beyond defects found by acceptance smoke.
- Do not modify core architecture.
- Do not create plotted WF charts.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `tests/test_validation_expansion_acceptance_smoke.py`
- `docs/validation_expansion_release_readiness_triage_057N.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-057m-impl_057n-design_final-acceptance-smoke-and-release-readiness-triage_deepseek.md`
- Production files only if a real acceptance defect is discovered.

## Acceptance Criteria

1. The new acceptance smoke test file exists and covers all 8 scenarios from the 057M design.
2. Tests verify real pipeline/widget/report/UI wiring behavior, not only hardcoded strings.
3. Default-off and empty-output omission behavior is covered.
4. No production behavior changes are made unless required to fix a real failing acceptance path.
5. 057N design gives a concise release-readiness triage and one clear next two-task batch.
6. Changelog and task board are updated.
7. Completion report is created.
8. Focused acceptance smoke, relevant nearby tests, full suite, and `git diff --check` pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_expansion_acceptance_smoke.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_report_export.py tests/test_bootstrap_monte_carlo_acceptance.py tests/test_wfe_ui_wiring.py -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- New acceptance smoke tests pass.
- Nearby report/bootstrap/WF UI tests pass.
- Full suite passes with only known pre-existing warnings.
- `git diff --check` passes.
- Agent status shows Batch 057M-Impl + 057N-Design completion report as the latest report.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
