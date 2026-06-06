# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 057E-Impl + 057F-Design - Bootstrap Display Surfaces and UI Controls Design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-06_task-057c-fix_057d-impl_bootstrap-surface-design-and-pipeline-wiring_codex-review.md`
8. `docs/bootstrap_pipeline_report_surface_design_057C.md`
9. `docs/monte_carlo_bootstrap_ci_design_057A.md`
10. `docs/milestone_direction_056N.md`
11. `docs/v0.2_validation_expansion_readiness.md`
12. This task file

## Context

Batch 057C-Fix + 057D-Impl was accepted. Bootstrap is now wired into the validation pipeline behind a default-off config flag, but it is not yet visible in the validation summary widget or exported reports. This batch pairs one display implementation task with one design-only UI controls task.

## Scope

### Do

- Complete two sequential tasks:
  - Task 057E-Impl - Bootstrap Display Surfaces
  - Task 057F-Design - Bootstrap UI Config Controls Design
- For Task 057E-Impl:
  - Implement display-only surfaces for `bootstrap_monte_carlo_result`.
  - In `app/widgets/validation_summary.py`, add a "Bootstrap MC" card after the existing Monte Carlo card only when bootstrap data is present.
  - In `reports/generator.py`, add bootstrap lines to both markdown and HTML validation formatting.
  - Render known numeric CI fields only:
    - `total_pnl`
    - `profit_factor`
    - `max_drawdown_pnl`
    - `stability_score`
  - Keep output absent when `bootstrap_monte_carlo_result` is missing or has no CI data.
  - Add focused tests in `tests/test_validation_summary.py` and `tests/test_report_export.py`.
- For Task 057F-Design:
  - Write `docs/bootstrap_ui_config_controls_design_057F.md`.
  - Design only; do not implement controls.
  - Cover Validate page controls, default-off behavior, PipelineConfig mapping, numeric bounds, validation rules, UI wiring tests, and non-goals.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-057e-impl_057f-design_bootstrap-display-and-ui-controls-design_deepseek.md`

### Do Not

- Do not modify validation pipeline or Monte Carlo engine code.
- Do not add UI controls.
- Do not wire UI controls into `PipelineConfig`.
- Do not add `worst_case_equity`.
- Do not change walk-forward production code.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `docs/bootstrap_pipeline_report_surface_design_057C.md`
- `app/widgets/validation_summary.py`
- `reports/generator.py`
- `tests/test_validation_summary.py`
- `tests/test_report_export.py`
- `docs/bootstrap_ui_config_controls_design_057F.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-057e-impl_057f-design_bootstrap-display-and-ui-controls-design_deepseek.md`

## Acceptance Criteria

1. Widget shows Bootstrap MC only when bootstrap CI data is present.
2. Markdown and HTML reports show Bootstrap MC only when bootstrap CI data is present.
3. Missing bootstrap data does not change existing validation summary/report output.
4. HTML output escapes or strictly formats any dynamic non-numeric values; numeric CI values are formatted consistently.
5. 057F design covers UI controls without implementation.
6. Changelog and task board are updated.
7. Completion report is created.
8. Focused display/report tests and `git diff --check` pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_summary.py tests/test_report_export.py -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused tests pass.
- `git diff --check` passes.
- Agent status shows Batch 057E-Impl + 057F-Design completion report as the latest report.
- Bootstrap UI controls are designed only, not implemented.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
