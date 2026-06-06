# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 056C - OOS Stability Reporting Surface Design Only.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-06_task-056b-fix_oos-stability-undefined-ratio_codex-review.md`
8. `app/services/validation_pipeline_service.py`
9. `validation_engine/elimination.py`
10. `app/widgets/validation_summary.py`
11. Relevant report/export files discovered by search
12. This task file

## Context

Task 056B now computes OOS metrics in the validation pipeline and passes them into elimination stability rules. The next risk is product-surface drift: UI/report output may hide OOS metrics, stability warnings, or fail reasons, making the new validation gate hard to inspect.

This task is design only. Do not implement UI/report changes yet.

## Scope

### Do

- Trace where validation pipeline results are currently displayed or exported:
  - Validation summary UI.
  - Report generation/export surfaces.
  - Any structured result serialization that already exists.
- Identify the minimal product surface needed for OOS stability:
  - OOS metrics to show.
  - Stability ratios to show, if available.
  - Warning/fail reason wording.
  - Research-only disclaimer placement if a report surface is involved.
- Propose the smallest follow-up implementation task with file list and acceptance criteria.
- Write a design note:
  - `docs/oos_stability_reporting_surface_design_056C.md`
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-056c_oos-stability-reporting-surface-design_deepseek.md`

### Do Not

- Do not change production code.
- Do not change tests.
- Do not implement UI, report, export, or serialization changes.
- Do not add dependencies.
- Do not rename existing validation fields.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `docs/oos_stability_reporting_surface_design_056C.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-056c_oos-stability-reporting-surface-design_deepseek.md`

Read-only inspection likely includes:

- `app/services/validation_pipeline_service.py`
- `validation_engine/elimination.py`
- `app/widgets/validation_summary.py`
- report/export modules found with `rg`

## Acceptance Criteria

1. The design note accurately traces the current result flow from validation pipeline to UI/report surfaces.
2. The design note recommends one small implementation task, not a broad redesign.
3. The recommendation preserves engine/UI separation.
4. No production code or tests are changed.
5. `docs/changelog.md` and `docs/task_board.md` are updated.
6. `git diff --check` passes.

## Verification

Run exactly:

```powershell
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- `git diff --check` passes.
- Agent status shows Task 056C completion report as the latest report.
- No production code or tests changed.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
