# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 057L-Impl + 057M-Design - WF Equity Report Tables and 057 Acceptance Smoke Design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-06_task-057j-impl_057l-design_wf-equity-summary-widget-and-report-design_codex-review.md`
8. `docs/wf_equity_report_surface_design_057L.md`
9. `docs/wf_equity_chart_display_design_057J.md`
10. `docs/validation_expansion_acceptance_triage_057K.md`
11. `docs/v0.2_validation_expansion_readiness.md`
12. This task file

## Context

Batch 057J-Impl + 057L-Design accepted the WF equity summary widget and report table design. Implement report tables only, and separately design the final 057 validation expansion acceptance smoke.

## Scope

### Do

- Complete two sequential tasks:
  - Task 057L-Impl - WF Equity Report Tables
  - Task 057M-Design - 057 Validation Expansion Acceptance Smoke Design
- For Task 057L-Impl:
  - Implement reports-only WF equity tables in `reports/generator.py`.
  - Add markdown table after the existing WF line only when `walk_forward_summary["windows"]` contains at least one `equity_curve` list with at least two points.
  - Add HTML table with escaped/static-safe formatting and existing CSS classes where appropriate.
  - Show at most five valid equity windows and add a `... N more windows ...` row when more exist.
  - Use integer formatting for start/end equity and one decimal for percent change.
  - Omit report table when windows are missing, empty, all equity curves are missing/empty, or all curves have fewer than two points.
  - Add focused markdown/HTML tests in `tests/test_report_export.py`.
- For Task 057M-Design:
  - Write `docs/validation_expansion_acceptance_smoke_design_057M.md`.
  - Design-only; do not implement acceptance smoke.
  - Define final 057 acceptance smoke coverage for bootstrap MC plus WF equity storage/widget/report visibility.
  - Include exact proposed test file name, test list, fixtures, verification command, and non-goals.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-057l-impl_057m-design_wf-equity-report-tables-and-acceptance-smoke-design_deepseek.md`

### Do Not

- Do not modify walk-forward engine or validation pipeline.
- Do not add `worst_case_equity`.
- Do not implement plotted charts.
- Do not modify ValidationSummary widget in this batch.
- Do not add new UI controls.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `reports/generator.py`
- `tests/test_report_export.py`
- `docs/validation_expansion_acceptance_smoke_design_057M.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-057l-impl_057m-design_wf-equity-report-tables-and-acceptance-smoke-design_deepseek.md`

## Acceptance Criteria

1. Markdown and HTML reports show WF equity table only when valid equity curves are present.
2. Markdown and HTML reports omit WF equity table for missing/empty/too-short equity data.
3. Report tables are capped to five valid windows and indicate omitted remaining windows.
4. Focused report tests cover shown, absent, and row-limit behavior.
5. 057M design defines final 057 validation expansion acceptance smoke without implementation.
6. Changelog and task board are updated.
7. Completion report is created.
8. Focused report tests and `git diff --check` pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_report_export.py -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused report tests pass.
- `git diff --check` passes.
- Agent status shows Batch 057L-Impl + 057M-Design completion report as the latest report.
- Final acceptance smoke is designed only, not implemented.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
