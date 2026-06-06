# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 056K - IS Baseline Precheck Visibility Surface Design Only.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-06_task-056j-impl-fix_nonpositive-pnl-precheck-test-hardening_codex-review.md`
8. `app/services/validation_pipeline_service.py`
9. `app/widgets/validation_summary.py`
10. `reports/generator.py`
11. Existing validation summary/report tests
12. This task file

## Context

Task 056J-Impl added an opt-in IS baseline quality precheck. Early-return results now carry `precheck_failed=True`, explicit warnings, empty stress results, and skipped MC/WF summaries. The next safe step is design-only: decide whether ValidationSummary and reports need a clearer user-facing precheck/skipped-validation surface before any UI/report implementation.

## Scope

### Do

- Inspect current display behavior for a representative `PipelineResult(precheck_failed=True)`:
  - `app/widgets/validation_summary.py`
  - `reports/generator.py`
  - related tests
- Write a design note:
  - `docs/is_baseline_precheck_visibility_design_056K.md`
- The design must answer:
  - What currently appears in ValidationSummary when precheck fails.
  - What currently appears in Markdown and HTML reports when precheck fails.
  - Whether the existing warnings/empty sections are sufficient.
  - If not sufficient, propose the smallest display/report change.
  - Exact text/fields recommended for user-visible output.
  - Tests required for a later implementation task.
  - Explicit non-goals.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-056k_is-baseline-precheck-visibility-surface-design_deepseek.md`

### Do Not

- Do not change production code.
- Do not add tests.
- Do not modify report/widget behavior.
- Do not modify pipeline behavior.
- Do not add UI controls.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `docs/is_baseline_precheck_visibility_design_056K.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-056k_is-baseline-precheck-visibility-surface-design_deepseek.md`

Read-only references:

- `app/services/validation_pipeline_service.py`
- `app/widgets/validation_summary.py`
- `reports/generator.py`
- `tests/test_validation_summary.py`
- `tests/test_report_export.py`

## Acceptance Criteria

1. Design note accurately describes current precheck failure display behavior.
2. Design note decides whether a display/report implementation is needed.
3. If implementation is recommended, scope is minimal and file/test list is clear.
4. No production code or tests are changed.
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
- Agent status shows Task 056K completion report as the latest report.
- No tests are required because this is design-only.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
