# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 056G - Stress Result Details Reporting Surface Design Only.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-06_task-056f-fix_remove-best-n-trades-pipeline-assumptions-serialization_codex-review.md`
8. `app/services/validation_pipeline_service.py`
9. `validation_engine/stress_test.py`
10. `app/widgets/validation_summary.py`
11. `reports/generator.py`
12. This task file

## Context

Task 056F and 056F-Fix wired remove-best-N-trades stress into the validation pipeline and preserved serialized `assumptions`, `warnings`, and `threshold` fields. The next safe step is not production UI/report implementation yet; first decide how these optional stress details should surface without cluttering the validation summary or exported reports.

## Scope

### Do

- Inspect current validation display/reporting surfaces:
  - `app/widgets/validation_summary.py`
  - `reports/generator.py`
  - any service/report helper directly involved in rendering validation stress results
- Write a design note:
  - `docs/stress_result_details_surface_design_056G.md`
- The design must answer:
  - Which stress result fields are already displayed today.
  - Whether optional `assumptions`, `warnings`, and `threshold` should be shown in the UI, Markdown/HTML reports, or both.
  - Minimal display format for remove-best-N-trades details:
    - `n`
    - `removed_count`
    - `surviving_count`
    - `pnl_loss_ratio`
    - `threshold["max_pnl_loss"]`
    - `warnings`
  - How to keep existing stress tests backward compatible.
  - Proposed acceptance criteria for a later implementation task.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-056g_stress-result-details-reporting-surface-design_deepseek.md`

### Do Not

- Do not change production UI code.
- Do not change report generation code.
- Do not change validation pipeline behavior.
- Do not change stress engine behavior.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `docs/stress_result_details_surface_design_056G.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-056g_stress-result-details-reporting-surface-design_deepseek.md`

Read-only references:

- `app/widgets/validation_summary.py`
- `reports/generator.py`
- `app/services/validation_pipeline_service.py`
- `validation_engine/stress_test.py`

## Acceptance Criteria

1. Design note clearly describes current stress result display behavior.
2. Design note recommends a minimal implementation plan for surfacing optional stress details.
3. Design explicitly covers remove-best-N-trades assumptions, threshold, and warnings.
4. No production code is changed.
5. Changelog and task board are updated.
6. Completion report is created.
7. `git diff --check` passes.

## Verification

Run exactly:

```powershell
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- `git diff --check` passes.
- Agent status shows Task 056G completion report as the latest report.
- No tests are required because this is design-only.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
