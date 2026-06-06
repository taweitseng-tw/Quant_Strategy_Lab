# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 057C-Fix + 057D-Impl - Bootstrap Surface Design Hardening and Pipeline Wiring.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-06_task-057a-impl_057c-design_bootstrap-engine-and-surface-design_codex-review.md`
8. `docs/bootstrap_pipeline_report_surface_design_057C.md`
9. `docs/monte_carlo_bootstrap_ci_design_057A.md`
10. `docs/milestone_direction_056N.md`
11. `docs/v0.2_validation_expansion_readiness.md`
12. This task file

## Context

Batch 057A-Impl + 057C-Design was accepted. The bootstrap engine exists but is not wired into the validation pipeline. The 057C design is sufficient for pipeline wiring, but display/report wording needs hardening before any UI/report implementation.

## Scope

### Do

- Complete two sequential tasks:
  - Task 057C-Fix - Bootstrap Display Surface Design Hardening
  - Task 057D-Impl - Bootstrap Pipeline Wiring Only
- For Task 057C-Fix:
  - Update only `docs/bootstrap_pipeline_report_surface_design_057C.md`.
  - Add concrete proposed wording/field layout for:
    - validation summary widget,
    - markdown report,
    - HTML report.
  - Keep display/report implementation deferred.
  - Preserve default-off behavior and non-goals.
- For Task 057D-Impl:
  - Wire bootstrap into `run_validation_pipeline()` only.
  - Add to `PipelineConfig`:
    - `run_bootstrap_monte_carlo: bool = False`
    - `bootstrap_iterations: int = 200`
    - `bootstrap_confidence_level: float = 0.95`
  - Add to `PipelineResult`:
    - `bootstrap_monte_carlo_result: dict | None = None`
  - Add serialization helper for bootstrap result including confidence intervals, assumptions, percentile summary, worst case, and stability score.
  - When disabled, existing `monte_carlo_summary` and existing pipeline outputs must remain unchanged.
  - Add focused tests in `tests/test_validation_pipeline_service.py`.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-057c-fix_057d-impl_bootstrap-surface-design-and-pipeline-wiring_deepseek.md`

### Do Not

- Do not modify UI widgets or reports.
- Do not add report display code.
- Do not add UI controls.
- Do not add `worst_case_equity`.
- Do not change Monte Carlo engine code except imports needed by pipeline wiring.
- Do not change walk-forward production code.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `docs/bootstrap_pipeline_report_surface_design_057C.md`
- `app/services/validation_pipeline_service.py`
- `tests/test_validation_pipeline_service.py`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-057c-fix_057d-impl_bootstrap-surface-design-and-pipeline-wiring_deepseek.md`

## Acceptance Criteria

1. 057C design has concrete widget, markdown, and HTML wording proposals.
2. Bootstrap remains default-off in `PipelineConfig`.
3. When disabled, `bootstrap_monte_carlo_result` is `None`.
4. When enabled, `bootstrap_monte_carlo_result` includes `confidence_intervals`.
5. Existing `monte_carlo_summary` remains present and unchanged when bootstrap is disabled.
6. Focused pipeline tests cover enabled/disabled behavior and config snapshot.
7. Changelog and task board are updated.
8. Completion report is created.
9. Focused tests and `git diff --check` pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_pipeline_service.py -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused tests pass.
- `git diff --check` passes.
- Agent status shows Batch 057C-Fix + 057D-Impl completion report as the latest report.
- Bootstrap is wired only into pipeline, not UI/reports.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
