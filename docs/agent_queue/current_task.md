# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 057J-Impl + 057L-Design - WF Equity Summary Widget and Report Surface Design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-06_task-057j-design_057k-design_wf-equity-display-and-validation-acceptance-triage_codex-review.md`
8. `docs/wf_equity_chart_display_design_057J.md`
9. `docs/validation_expansion_acceptance_triage_057K.md`
10. `docs/validation_gap_triage_057H.md`
11. `docs/v0.2_validation_expansion_readiness.md`
12. This task file

## Context

Batch 057J-Design + 057K-Design accepted a no-dependency, widget-first WF equity summary approach. Implement the widget summary only, and separately harden the report/table design before any report implementation.

## Scope

### Do

- Complete two sequential tasks:
  - Task 057J-Impl - WF Equity Summary Widget
  - Task 057L-Design - WF Equity Report Surface Design Hardening
- For Task 057J-Impl:
  - Implement widget-only WF equity summary in `app/widgets/validation_summary.py`.
  - Use already-serialized `walk_forward_summary["windows"][*]["equity_curve"]`.
  - Add a compact "WF Equity Summary" section after the existing Walk-Forward section only when at least one window has a non-empty equity curve.
  - Render no more than the first 5 windows to keep the widget compact, with a suffix line such as `... N more windows` if needed.
  - For each shown window, display:
    - window index,
    - start equity,
    - end equity,
    - percent change,
    - PASSED/FAILED from `passed`.
  - Omit the section when `windows` is missing, empty, all equity curves are missing/empty, or all curves have fewer than 2 points.
  - Add focused tests in `tests/test_validation_summary.py`.
- For Task 057L-Design:
  - Write `docs/wf_equity_report_surface_design_057L.md`.
  - Design-only; do not implement report output.
  - Harden markdown/HTML table design, row limits, escaping/formatting rules, empty behavior, and focused report test plan.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-057j-impl_057l-design_wf-equity-summary-widget-and-report-design_deepseek.md`

### Do Not

- Do not modify walk-forward engine or validation pipeline.
- Do not add `worst_case_equity`.
- Do not implement plotted charts.
- Do not modify reports in this batch.
- Do not add report tests in this batch.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `app/widgets/validation_summary.py`
- `tests/test_validation_summary.py`
- `docs/wf_equity_report_surface_design_057L.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-057j-impl_057l-design_wf-equity-summary-widget-and-report-design_deepseek.md`

## Acceptance Criteria

1. Widget shows WF Equity Summary only when valid per-window equity curves are present.
2. Widget omits WF Equity Summary for missing/empty/too-short equity data.
3. Widget summary is capped to the first 5 windows and indicates omitted remaining windows.
4. Focused widget tests cover present, absent, and row-limit behavior.
5. 057L report design defines markdown/HTML table behavior without implementation.
6. Changelog and task board are updated.
7. Completion report is created.
8. Focused widget tests and `git diff --check` pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_summary.py -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused widget tests pass.
- `git diff --check` passes.
- Agent status shows Batch 057J-Impl + 057L-Design completion report as the latest report.
- Reports are designed only, not implemented.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
