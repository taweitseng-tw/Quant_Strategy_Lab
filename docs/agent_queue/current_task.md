# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 056E-Impl - Remove Best N Trades Stress Test Engine Implementation.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/remove_best_n_trades_stress_design_056E.md`
8. `docs/review_notes/2026-06-06_task-056e-fix2_remove-best-n-trades-design-duplicate-cleanup_codex-review.md`
9. `validation_engine/stress_test.py`
10. `tests/test_stress_test.py`
11. This task file

## Context

The design for Remove Best N Trades is accepted. This implementation must be engine-only: add the stress function and focused engine tests, but do not wire it into the validation pipeline yet.

## Scope

### Do

- In `validation_engine/stress_test.py`:
  - Add `stress_remove_best_n_trades(baseline: BacktestResult, *, n: int = 3, degradation_threshold: float = 0.30) -> StressTestResult`.
  - Operate on `baseline.trades` only; do not re-run backtests.
  - Sort trades by `pnl` descending and remove the top `n`.
  - Recompute stressed metrics with `compute_metrics(surviving_trades)`.
  - Preserve existing `degradation` convention: `(stressed - baseline) / abs(baseline)`.
  - Use separate `pnl_loss_ratio` in `assumptions` for pass/fail.
  - Do not mutate `baseline.trades`.
  - Raise `ValueError` for non-int or negative `n`.
  - Raise `ValueError` for negative `degradation_threshold`.
  - Handle edge cases:
    - zero trades: pass with warning.
    - `n == 0`: pass with no trades removed and `assumptions["n_zero"] = True`.
    - `0 < trade_count <= n`: fail with warning and `assumptions["insufficient_trades"] = True`.
- In `tests/test_stress_test.py`, add focused tests for:
  - deterministic output.
  - PnL worsens after removing best trades.
  - fails above threshold.
  - passes within threshold.
  - zero trades vacuous pass.
  - insufficient trades fail.
  - does not mutate baseline.
  - structured output fields.
  - negative `n` raises.
  - negative `degradation_threshold` raises.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-056e-impl_remove-best-n-trades-stress-engine-implementation_deepseek.md`

### Do Not

- Do not modify `app/services/validation_pipeline_service.py`.
- Do not add PipelineConfig fields.
- Do not wire this stress test into the pipeline.
- Do not modify UI/report code.
- Do not change elimination thresholds.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `validation_engine/stress_test.py`
- `tests/test_stress_test.py`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-056e-impl_remove-best-n-trades-stress-engine-implementation_deepseek.md`

## Acceptance Criteria

1. `stress_remove_best_n_trades()` exists and returns `StressTestResult`.
2. The implementation does not mutate `baseline.trades`.
3. The implementation preserves existing `degradation` sign convention.
4. `pnl_loss_ratio` is present in `assumptions` and is not stored as `degradation["total_pnl"]`.
5. Low-trade-count behavior matches the accepted design.
6. No pipeline, UI, report, or elimination behavior changes.
7. Focused stress tests pass.
8. Full suite passes.
9. `git diff --check` passes.

## Verification

Run exactly:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_stress_test.py -v
.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused stress tests pass.
- Full suite passes without ignored tests.
- `git diff --check` passes.
- Agent status shows Task 056E-Impl completion report as the latest report.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
