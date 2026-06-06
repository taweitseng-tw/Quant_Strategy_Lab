# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 056G-Impl - Stress Result Details Display Implementation.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/stress_result_details_surface_design_056G.md`
8. `docs/review_notes/2026-06-06_task-056g_stress-result-details-reporting-surface-design_codex-review.md`
9. `app/widgets/validation_summary.py`
10. `reports/generator.py`
11. `tests/test_validation_summary.py`
12. `tests/test_report_export.py`
13. This task file

## Context

Task 056G designed a minimal way to surface optional stress result details now that pipeline stress dictionaries preserve `assumptions`, `warnings`, and `threshold`. The implementation should be narrow: display details for `remove_best_n_trades` only, and keep existing stress display behavior unchanged for commission, slippage, one-bar delay, and parameter perturbation.

## Scope

### Do

- In `app/widgets/validation_summary.py`:
  - Extend the existing stress result rendering to append compact sub-lines for `test_name == "remove_best_n_trades"` when `assumptions` exist.
  - Include:
    - `n`
    - `removed_count`
    - `surviving_count`
    - `pnl_loss_ratio`
    - `threshold["max_pnl_loss"]` when present
    - `warnings` when non-empty
  - Do not create a new section, card, widget, or layout pattern.
- In `reports/generator.py`:
  - Add matching detail sub-lines to markdown validation output.
  - Add matching detail sub-lines to HTML validation output.
  - Ensure HTML output escapes dynamic warning/detail values.
- In tests:
  - Add focused coverage in `tests/test_validation_summary.py`.
  - Add focused coverage in `tests/test_report_export.py` for both markdown and HTML output, or the closest existing report export tests if naming differs locally.
  - Assert details appear for `remove_best_n_trades`.
  - Assert details do not appear for existing basic stress tests without rich display behavior.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-056g-impl_stress-result-details-display-implementation_deepseek.md`

### Do Not

- Do not change validation pipeline behavior.
- Do not change stress engine behavior.
- Do not change report export file formats beyond the validation stress detail text.
- Do not add a broad generic assumptions dumper for every stress test.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `app/widgets/validation_summary.py`
- `reports/generator.py`
- `tests/test_validation_summary.py`
- `tests/test_report_export.py`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-056g-impl_stress-result-details-display-implementation_deepseek.md`

## Acceptance Criteria

1. ValidationSummary shows compact remove-best-N detail sub-lines when serialized assumptions exist.
2. Markdown report shows matching remove-best-N detail sub-lines.
3. HTML report shows matching remove-best-N detail sub-lines and escapes dynamic text.
4. `n`, `removed_count`, `surviving_count`, `pnl_loss_ratio`, and `max_pnl_loss` threshold are visible when present.
5. Warnings are visible when present and omitted cleanly when empty.
6. Existing commission/slippage/one-bar-delay/parameter-perturbation stress lines remain compact.
7. Missing `assumptions`, `warnings`, or `threshold` does not crash any surface.
8. Focused tests pass.
9. Full suite passes.
10. `git diff --check` passes.

## Verification

Run exactly:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_validation_summary.py tests/test_report_export.py -v
.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused tests pass.
- Full suite passes without ignored tests.
- `git diff --check` passes.
- Agent status shows Task 056G-Impl completion report as the latest report.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
