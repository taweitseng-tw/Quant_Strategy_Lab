# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 056D - OOS Metrics Display Surface Implementation.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/oos_stability_reporting_surface_design_056C.md`
8. `docs/review_notes/2026-06-06_task-056c-fix_oos-stability-reporting-surface-design-correction_codex-review.md`
9. `app/services/validation_pipeline_service.py`
10. `app/widgets/validation_summary.py`
11. `reports/generator.py`
12. `app/ui/main_window.py`
13. Relevant existing tests:
    - `tests/test_validation_summary.py`
    - `tests/test_report_export.py`
    - `tests/test_active_dataset.py`
14. This task file

## Context

Task 056B added `PipelineResult.oos_metrics`. Task 056C-Fix corrected the reporting design so UI/report/log surfaces must display only existing structured OOS metrics, without recomputing IS/OOS stability ratios in presentation code.

This task is a narrow display implementation.

## Scope

### Do

- In `app/widgets/validation_summary.py`:
  - Add an "OOS Metrics" card after Walk-Forward Matrix and before Elimination.
  - Read only `result.oos_metrics`.
  - If `oos_metrics` is `None` or empty, show `No OOS data.`
  - If present, show PnL, PF, Trades, Max DD, and Win Rate.
- In `reports/generator.py`:
  - Add one OOS metrics line after the Baseline line in `_format_markdown_validation()`.
  - Add one OOS metrics line after the Baseline paragraph in `_format_html_validation()`.
  - Read only `vr.get("oos_metrics", {})`.
  - If missing or empty, skip the OOS line.
- In `app/ui/main_window.py`:
  - Add one log line after the elimination log line when `result.oos_metrics` is present.
  - Example content: `OOS: PnL=..., PF=..., Trades=...`.
- Add or update focused tests:
  - `tests/test_validation_summary.py`: OOS card appears with metrics and handles missing OOS data.
  - `tests/test_report_export.py` or another existing report test file: Markdown and HTML validation evidence include the OOS line when `oos_metrics` is present and omit it when absent.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-056d_oos-metrics-display-surface-implementation_deepseek.md`

### Do Not

- Do not change engine logic.
- Do not change `validation_engine/elimination.py`.
- Do not change `PipelineResult` schema.
- Do not compute PF degradation, drawdown ratio, or average-trade degradation in UI/report/log code.
- Do not add new stability ratio display.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `app/widgets/validation_summary.py`
- `reports/generator.py`
- `app/ui/main_window.py`
- `tests/test_validation_summary.py`
- `tests/test_report_export.py`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-056d_oos-metrics-display-surface-implementation_deepseek.md`

## Acceptance Criteria

1. ValidationSummary displays OOS metrics when `oos_metrics` exists.
2. ValidationSummary displays `No OOS data.` when OOS metrics are absent.
3. Markdown reports include exactly one OOS metrics line when `oos_metrics` exists.
4. HTML reports include exactly one OOS metrics paragraph when `oos_metrics` exists.
5. Markdown/HTML reports omit the OOS line when `oos_metrics` is absent.
6. Main-window validation log prints an OOS summary only when `result.oos_metrics` exists.
7. UI/report/log code does not compute OOS/IS stability ratios.
8. Focused tests and full suite pass.
9. `git diff --check` passes.

## Verification

Run exactly:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_validation_summary.py tests/test_report_export.py tests/test_active_dataset.py -v
.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused tests pass.
- Full suite passes without ignored tests.
- `git diff --check` passes.
- Agent status shows Task 056D completion report as the latest report.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
