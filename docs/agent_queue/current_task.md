# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 056J-Impl - Opt-in IS Baseline Quality Precheck.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/validation_expansion_followup_triage_056J.md`
8. `docs/review_notes/2026-06-06_task-056j-fix_validation-followup-triage-precision-correction_codex-review.md`
9. `app/services/validation_pipeline_service.py`
10. `tests/test_validation_pipeline_service.py`
11. This task file

## Context

Task 056J/Fix recommended the smallest next validation expansion: an opt-in IS baseline quality precheck. The goal is to skip expensive stress/MC/WF work only when the baseline IS result is clearly unusable, while making the skip explicit through structured result metadata and warnings.

Keep this narrow and pipeline-only.

## Scope

### Do

- In `app/services/validation_pipeline_service.py`:
  - Add `PipelineConfig.run_is_baseline_quality_precheck: bool = False`.
  - Add `PipelineConfig.fail_is_baseline_on_nonpositive_pnl: bool = False`.
  - Add `PipelineResult.precheck_failed: bool = False`.
  - After the baseline IS backtest is computed, if `run_is_baseline_quality_precheck` is enabled:
    - If `baseline.metrics["total_trades"] == 0`, return a structured early result with `precheck_failed=True`.
    - If `fail_is_baseline_on_nonpositive_pnl` is enabled and `baseline.metrics["total_pnl"] <= 0`, return a structured early result with `precheck_failed=True`.
  - Early result must preserve:
    - `split_metadata`
    - `baseline_metrics`
    - `oos_metrics` if already computed or a clear note if not computed
    - `config_snapshot`
    - a warning that explicitly states stress/MC/WF were skipped because the precheck failed
    - `stress_results=[]`
    - `monte_carlo_summary={}` or existing local empty convention
    - `walk_forward_summary=None`
    - `walk_forward_matrix_summary=None`
    - `elimination_result` that clearly fails or records the precheck reason
  - Default behavior must remain unchanged when the new precheck flag is false.
- In `tests/test_validation_pipeline_service.py`:
  - Add focused tests for:
    - default config does not precheck or short-circuit
    - enabled precheck with zero baseline trades returns `precheck_failed=True`, warnings, empty stress, empty/none MC/WF summaries
    - enabled nonpositive-PnL check triggers only when `fail_is_baseline_on_nonpositive_pnl=True`
    - config snapshot includes both new fields
  - Use deterministic synthetic data/strategy or mocking if needed to avoid fragile generated-trade assumptions.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-056j-impl_opt-in-is-baseline-quality-precheck_deepseek.md`

### Do Not

- Do not enable the precheck by default.
- Do not change stress engine behavior.
- Do not change Monte Carlo or walk-forward engines.
- Do not add UI controls.
- Do not change report or widget rendering unless a focused test reveals a crash.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `app/services/validation_pipeline_service.py`
- `tests/test_validation_pipeline_service.py`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-056j-impl_opt-in-is-baseline-quality-precheck_deepseek.md`

## Acceptance Criteria

1. New precheck config fields default to false.
2. Default pipeline behavior and test counts are unchanged except for config snapshot including new false fields.
3. Enabled zero-trade precheck returns `precheck_failed=True`.
4. Enabled zero-trade precheck skips stress/MC/WF and exposes an explicit warning.
5. Nonpositive-PnL precheck is separately opt-in and does not trigger unless its flag is true.
6. Early result preserves baseline metrics, split metadata, config snapshot, and a clear failed/blocked elimination result.
7. Focused pipeline tests pass.
8. Full suite passes.
9. `git diff --check` passes.

## Verification

Run exactly:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_validation_pipeline_service.py -v
.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused pipeline tests pass.
- Full suite passes without ignored tests.
- `git diff --check` passes.
- Agent status shows Task 056J-Impl completion report as the latest report.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
