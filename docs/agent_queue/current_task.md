# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 056H - Remove Best N Trades Stress Config Surface Design Only.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/stress_result_details_surface_design_056G.md`
8. `docs/review_notes/2026-06-06_task-056g-impl-fix2_escape-html-stress-detail-pnl-loss-value_codex-review.md`
9. `app/services/validation_pipeline_service.py`
10. `app/widgets/validation_summary.py`
11. `reports/generator.py`
12. This task file

## Context

Remove-best-N-trades stress now exists in the engine, can be enabled through `PipelineConfig`, is serialized with assumptions, and is displayed in the validation widget and reports. The remaining product gap is discoverability/configuration: the default pipeline keeps it off, and we need a careful design for where users should enable and configure it without overloading the UI.

This is design-only. Do not implement UI or service changes in this task.

## Scope

### Do

- Inspect the current validation/run configuration flow:
  - Where `PipelineConfig` is constructed.
  - Which validation options are already user-facing.
  - Which widgets/services would be touched by a future implementation.
- Write a design note:
  - `docs/remove_best_n_trades_config_surface_design_056H.md`
- The design must answer:
  - Whether remove-best-N should be exposed on the Validate page, Run/build configuration, report settings, or another existing surface.
  - Recommended control shape:
    - enable/disable checkbox or toggle
    - `n` numeric input
    - max PnL loss threshold input
  - Recommended defaults:
    - disabled by default
    - `n = 3`
    - `max_pnl_loss = 0.30`
  - How the UI should pass settings into `PipelineConfig` without engine/UI coupling.
  - How the selected settings should appear in reports or validation summary.
  - Minimal tests required for a later implementation task.
  - Risks and non-goals.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-056h_remove-best-n-trades-stress-config-surface-design_deepseek.md`

### Do Not

- Do not change production code.
- Do not modify `PipelineConfig`.
- Do not add UI controls.
- Do not change report generation.
- Do not change stress engine behavior.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `docs/remove_best_n_trades_config_surface_design_056H.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-056h_remove-best-n-trades-stress-config-surface-design_deepseek.md`

Read-only references may include:

- `app/services/validation_pipeline_service.py`
- `app/ui/main_window.py`
- `app/widgets/validation_summary.py`
- `reports/generator.py`
- tests around validation pipeline, run flow, and validation summary

## Acceptance Criteria

1. Design note clearly maps current configuration flow.
2. Design recommends one minimal config surface for remove-best-N stress.
3. Design keeps remove-best-N disabled by default.
4. Design explains how settings should reach `PipelineConfig` without UI-engine coupling.
5. Design lists future implementation files and tests.
6. No production code is changed.
7. Changelog and task board are updated.
8. Completion report is created.
9. `git diff --check` passes.

## Verification

Run exactly:

```powershell
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- `git diff --check` passes.
- Agent status shows Task 056H completion report as the latest report.
- No tests are required because this is design-only.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
