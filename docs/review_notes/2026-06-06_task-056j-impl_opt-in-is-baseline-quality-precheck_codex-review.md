# Codex Review - Task 056J-Impl Opt-in IS Baseline Quality Precheck

## Verdict

Needs fix before acceptance.

## Score

8.5 / 10

## Review Summary

The implementation is mostly aligned with the task: the precheck is opt-in, default behavior remains unchanged, early returns are structured, and the zero-trade branch has reasonable coverage.

Codex manually confirmed that the nonpositive-PnL branch can trigger with a nonzero-trade baseline. However, the test suite does not actually lock that behavior, so a future regression could break the branch while the current tests still pass.

## Blocking Finding

### P1 - Nonpositive-PnL branch is not directly tested

File: `tests/test_validation_pipeline_service.py`

`test_precheck_nonpositive_pnl_triggers_when_enabled` only checks that the config snapshot contains `fail_is_baseline_on_nonpositive_pnl=True`; it does not assert `precheck_failed=True` or the non-positive PnL warning.

`test_precheck_nonpositive_pnl_short_circuits_with_negative` uses `_make_zero_trade_strategy()`, so it triggers the zero-trade precheck branch rather than proving the nonpositive-PnL branch.

## Verified

```powershell
.venv\Scripts\python.exe -m pytest tests/test_validation_pipeline_service.py -v
git diff --check
```

Results:

- Focused pipeline tests: 29 passed.
- `git diff --check`: passed.
- Manual probe confirmed current implementation can trigger the nonpositive-PnL branch with `total_trades=11` and negative baseline PnL.

## Required Fix

Strengthen tests so the nonpositive-PnL branch is exercised with `total_trades > 0`, and prove the same baseline does not short-circuit when `fail_is_baseline_on_nonpositive_pnl=False`.
