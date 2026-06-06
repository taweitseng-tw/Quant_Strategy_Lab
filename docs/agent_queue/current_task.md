# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 056H-Impl - Remove Best N Trades Stress Config Controls.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/remove_best_n_trades_config_surface_design_056H.md`
8. `docs/review_notes/2026-06-06_task-056h_remove-best-n-trades-stress-config-surface-design_codex-review.md`
9. `app/ui/main_window.py`
10. `tests/test_wfe_ui_wiring.py`
11. This task file

## Context

Remove-best-N-trades stress is engine-backed, pipeline-backed, serialized, and displayed in validation summary/report outputs. It remains opt-in and currently has no user-facing controls. The next step is to add minimal Validate page controls that feed existing `PipelineConfig` fields without changing engine or pipeline behavior.

## Scope

### Do

- In `app/ui/main_window.py`:
  - Add Validate page controls near the existing WFE checkbox:
    - `QCheckBox` for enabling remove-best-N stress.
    - `QSpinBox` for `remove_best_n_trades_n`, default `3`, min `1`, max `50`.
    - `QDoubleSpinBox` for `remove_best_n_trades_degradation_threshold`, default `0.30`, min `0.01`, max `1.00`, step `0.05`, two decimals.
  - Keep the enable checkbox unchecked by default.
  - Disable the two spinboxes while the checkbox is unchecked; enable them when checked.
  - Pass the three values into `PipelineConfig(...)` in `_handle_run()`.
  - Keep WFE behavior unchanged.
- In `tests/test_wfe_ui_wiring.py` or a clearly named adjacent test file:
  - Add tests that assert controls exist and defaults are correct.
  - Assert spinboxes are disabled when unchecked and enabled when checked.
  - Patch `run_validation_pipeline` and verify unchecked state passes:
    - `run_remove_best_n_trades_stress is False`
    - `remove_best_n_trades_n == 3`
    - `remove_best_n_trades_degradation_threshold == 0.30`
  - Verify checked/custom values pass through to `PipelineConfig`.
  - Ensure existing WFE tests still pass.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-056h-impl_remove-best-n-trades-stress-config-controls_deepseek.md`

### Do Not

- Do not change `PipelineConfig` fields or defaults.
- Do not change validation pipeline service behavior.
- Do not change stress engine behavior.
- Do not change report generation.
- Do not add a new widget class unless absolutely necessary.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `app/ui/main_window.py`
- `tests/test_wfe_ui_wiring.py`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-056h-impl_remove-best-n-trades-stress-config-controls_deepseek.md`

## Acceptance Criteria

1. Remove-best-N controls exist on the Validate page.
2. Enable checkbox is unchecked by default.
3. `n` spinbox defaults to `3`, min `1`, max `50`.
4. Threshold spinbox defaults to `0.30`, min `0.01`, max `1.00`, step `0.05`, two decimals.
5. Spinboxes are disabled when the checkbox is unchecked and enabled when checked.
6. `_handle_run()` passes unchecked defaults into `PipelineConfig`.
7. `_handle_run()` passes checked/custom values into `PipelineConfig`.
8. Existing WFE checkbox behavior is unchanged.
9. Focused UI wiring tests pass.
10. Full suite passes.
11. `git diff --check` passes.

## Verification

Run exactly:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_wfe_ui_wiring.py -v
.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused UI wiring tests pass.
- Full suite passes without ignored tests.
- `git diff --check` passes.
- Agent status shows Task 056H-Impl completion report as the latest report.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
