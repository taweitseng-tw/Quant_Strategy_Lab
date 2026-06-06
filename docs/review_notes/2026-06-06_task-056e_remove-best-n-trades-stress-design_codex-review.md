# Codex Review - Task 056E Remove Best N Trades Stress Test Design

Date: 2026-06-06
Reviewer: Codex
Verdict: Needs Fix
Score: 8.1 / 10

## Summary

Task 056E identifies a valuable validation gap: strategies that only survive because of a few outlier trades should be stress-tested by removing their best trades. The design is close, but it should not be implemented as written yet because several details would create ambiguity or overly lenient behavior.

## Findings

### P1 - Degradation sign conflicts with existing stress-test convention

Existing `_build_result()` stores per-metric degradation as `(stressed - baseline) / abs(baseline)`. For profitable baselines, worse PnL is therefore negative.

The 056E design instead defines `(base_pnl - stressed_pnl) / abs(base_pnl)`, where worse PnL is positive. That is a valid business metric, but it conflicts with the current `StressTestResult.degradation` convention and can confuse reports, tests, and future elimination logic.

Required correction:

- Preserve the existing `degradation` sign convention in `StressTestResult.degradation`.
- If a positive "loss of edge" ratio is needed for pass/fail, store it separately as `pnl_loss_ratio` in `assumptions`, or keep it as an internal local variable.

### P1 - First implementation scope is internally inconsistent

The design says the first implementation should be engine-only, but the implementation surface also includes pipeline config fields, pipeline wiring, and pipeline tests.

Required correction:

- Pick one first implementation scope.
- Codex recommends engine-only first:
  - `validation_engine/stress_test.py`
  - `tests/test_stress_test.py`
  - docs updates
- Defer pipeline config and pipeline wiring to a later task.

### P2 - Low-trade-count behavior is too lenient

The design proposes a vacuous pass when `n >= len(trades)`. If this stress is later counted by `min_stress_pass_rate`, low-trade-count strategies can receive a free pass despite not having enough trades for the test to be meaningful.

Required correction:

- Zero trades may remain a vacuous pass with warning to match existing stress-test behavior.
- For `0 < len(trades) <= n`, prefer `passed=False` with a clear warning and `assumptions["insufficient_trades"] = True`, or explicitly justify why it must pass.

### P3 - Minor typo in proposed pipeline call

The pseudo-code uses `degration_threshold` instead of `degradation_threshold`.

## Verification

- Reviewed `docs/remove_best_n_trades_stress_design_056E.md`.
- Compared the design against `validation_engine/stress_test.py`, `app/services/validation_pipeline_service.py`, and `validation_engine/elimination.py`.
- Confirmed no production code or tests were changed.

## Decision

Do not implement Task 056E-Impl from the current design. Run Task 056E-Fix first.

## Next Task

Task 056E-Fix - Remove Best N Trades Stress Test Design Hardening.
