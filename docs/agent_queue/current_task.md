# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 057G-Impl + 057H-Design - Bootstrap Feature Acceptance Smoke and Remaining Validation Gap Triage.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-06_task-057e-fix_057f-impl_bootstrap-display-hardening-and-ui-controls_codex-review.md`
8. `docs/bootstrap_ui_config_controls_design_057F.md`
9. `docs/bootstrap_pipeline_report_surface_design_057C.md`
10. `docs/monte_carlo_bootstrap_ci_design_057A.md`
11. `docs/v0.2_validation_expansion_readiness.md`
12. This task file

## Context

Batch 057E-Fix + 057F-Impl was accepted. Bootstrap Monte Carlo now has engine, pipeline, display, and UI controls. Before adding more features, add a focused acceptance smoke and then produce a design-only triage of any remaining validation gaps.

## Scope

### Do

- Complete two sequential tasks:
  - Task 057G-Impl - Bootstrap Feature Acceptance Smoke
  - Task 057H-Design - Remaining Validation Gap Triage
- For Task 057G-Impl:
  - Add test-only acceptance smoke coverage for the bootstrap feature chain.
  - Prefer one new focused test file:
    - `tests/test_bootstrap_monte_carlo_acceptance.py`
  - Cover:
    - default PipelineConfig does not run bootstrap,
    - opt-in PipelineConfig produces `bootstrap_monte_carlo_result` with `confidence_intervals`,
    - UI controls pass enabled/custom values into `PipelineConfig`,
    - widget displays Bootstrap MC when CI data is present,
    - markdown and HTML reports display Bootstrap MC when CI data is present,
    - widget/markdown/HTML omit Bootstrap MC when CI data is empty.
  - Do not change production code unless a test exposes a real bug; if production code must change, keep it minimal and explain why.
- For Task 057H-Design:
  - Write `docs/validation_gap_triage_057H.md`.
  - Design-only triage: summarize what 057 completed, list remaining PRD validation gaps, and recommend exactly one next task.
  - Include whether price-noise stress, WF equity display, or broader validation acceptance should come next.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-057g-impl_057h-design_bootstrap-acceptance-and-validation-gap-triage_deepseek.md`

### Do Not

- Do not modify Monte Carlo engine code unless acceptance smoke exposes a real bug.
- Do not add `worst_case_equity`.
- Do not change walk-forward production code.
- Do not add new UI controls.
- Do not change report layout beyond bug fixes required by acceptance smoke.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `tests/test_bootstrap_monte_carlo_acceptance.py`
- `docs/validation_gap_triage_057H.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-057g-impl_057h-design_bootstrap-acceptance-and-validation-gap-triage_deepseek.md`

## Acceptance Criteria

1. Acceptance tests cover the bootstrap feature chain from pipeline/UI config to widget/report display.
2. Default-off behavior is covered.
3. Empty-CI omission behavior is covered across widget/markdown/HTML.
4. 057H triage note summarizes completed 057 bootstrap work and remaining validation gaps.
5. 057H recommends exactly one next task.
6. Changelog and task board are updated.
7. Completion report is created.
8. Focused acceptance tests and `git diff --check` pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_bootstrap_monte_carlo_acceptance.py -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused tests pass.
- `git diff --check` passes.
- Agent status shows Batch 057G-Impl + 057H-Design completion report as the latest report.
- No new feature implementation beyond test-only acceptance smoke unless fixing a real bug exposed by the smoke.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
