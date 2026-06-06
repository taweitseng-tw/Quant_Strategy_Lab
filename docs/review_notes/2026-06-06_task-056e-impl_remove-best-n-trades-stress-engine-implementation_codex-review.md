# Codex Review - Task 056E-Impl Remove Best N Trades Stress Engine Implementation

Date: 2026-06-06
Reviewer: Codex
Verdict: Needs Fix
Score: 8.3 / 10

## Summary

The engine implementation appears directionally correct and stays engine-only. It adds `stress_remove_best_n_trades()` without pipeline wiring, preserves the existing degradation sign convention, and keeps `pnl_loss_ratio` separate in `assumptions`.

The blocker is test quality: several core tests rely on `_make_baseline_with_trades(200)`, which currently produces only one trade. As a result, important assertions are wrapped in `if baseline.metrics["total_trades"] >= 3:` and can silently skip the behavior they are supposed to verify.

## Findings

### P1 - Core threshold tests can silently skip assertions

The focused tests for "worsens PnL", "fails above threshold", and "passes within threshold" use a generated SMA baseline and guard core assertions behind:

```python
if baseline.metrics["total_trades"] >= 3:
    ...
```

Codex probe showed the current helper produces:

```text
trade_count=1
```

Therefore those tests can pass without validating the main threshold behavior.

Required correction:

- Add a deterministic synthetic `BacktestResult` helper built from explicit `Trade` objects and `compute_metrics()`.
- Use that helper for remove-best-N tests that need known trade counts and known PnL values.
- Remove conditional guards around the core assertions.
- Assert exact or near-exact values for:
  - `stressed_metrics["total_pnl"]`
  - `degradation["total_pnl"]`
  - `assumptions["pnl_loss_ratio"]`
  - `passed`

Suggested fixture:

```python
trades = [
    Trade(..., pnl=100.0),
    Trade(..., pnl=50.0),
    Trade(..., pnl=-20.0),
    Trade(..., pnl=-10.0),
]
```

Baseline total PnL is `120.0`; removing the best trade leaves `20.0`, so:

- `degradation["total_pnl"] = (20 - 120) / 120 = -0.833333`
- `pnl_loss_ratio = (120 - 20) / 120 = 0.833333`

## Non-Blocking Notes

- The implementation accepts boolean `degradation_threshold` because `bool` is a subclass of `int`; this is not currently in task scope, but a future strict-input cleanup could reject it for consistency with `n`.

## Verification

- `.venv\Scripts\python.exe -m pytest tests/test_stress_test.py -v`
  - Result: 25 passed.
- `.venv\Scripts\python.exe -m pytest -q`
  - Result: 1002 passed, 1 pre-existing pandas datetime warning.
- `git diff --check`
  - Result: passed, with LF/CRLF working-copy warnings only.
- Manual probe confirmed `_make_baseline_with_trades(200)` currently produces only one trade.

## Decision

Do not accept yet. Run Task 056E-Impl-Fix to harden tests and, only if necessary, adjust implementation to match the deterministic assertions.

## Next Task

Task 056E-Impl-Fix - Remove Best N Trades Deterministic Test Hardening.
