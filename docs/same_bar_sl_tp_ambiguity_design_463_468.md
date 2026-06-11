# Same-Bar SL/TP Ambiguity Audit and Design - Tasks 463-468

Design document. No production code changed.

Date: 2026-06-11

## Finding

The current backtest engine already implements the conservative same-bar
stop-loss / take-profit ambiguity rule:

- Active risk management runs in `backtest_engine/runner.py` after pending
  entries are executed.
- For long positions:
  - stop-loss is hit when `bar_low <= sl_price`
  - take-profit is hit when `bar_high >= tp_price`
- For short positions:
  - stop-loss is hit when `bar_high >= sl_price`
  - take-profit is hit when `bar_low <= tp_price`
- When either trigger is hit, the exit reason is selected as:
  - `stop_loss` if `hit_sl` is true
  - otherwise `take_profit`

Because `hit_sl` wins whenever both booleans are true, same-bar ambiguity is
currently resolved as stop-loss first.

## Existing Coverage

`tests/test_backtest_engine.py` already covers:

- long stop-loss hit
- long take-profit hit
- short stop-loss hit
- short take-profit hit
- long same-bar SL/TP ambiguity with stop-loss winning
- long gap-through stop-loss
- short gap-through stop-loss
- stop/take-profit assumptions recorded in result assumptions

## Remaining Test Gap

The current production code does not require a formula change for the audited
path. The next implementation slice should add focused regression tests only.

Missing high-value tests:

1. Short same-bar SL/TP ambiguity where both stop-loss and take-profit are hit
   in the same bar and stop-loss wins.
2. Long same-bar gap-through ambiguity where the position is already open, the
   next bar opens beyond the stop, and the same bar also touches take-profit.
3. Short same-bar gap-through ambiguity where the position is already open, the
   next bar opens beyond the stop, and the same bar also touches take-profit.

## Implementation Plan For Tasks 469-474

Modify only:

- `tests/test_backtest_engine.py`
- `docs/task_board.md`
- `docs/changelog.md`

Do not modify:

- `backtest_engine/runner.py` unless one of the new tests proves the audit
  finding wrong.
- ranking, validation, reports, or UI code.

## Required Tests

### 1. Short Same-Bar Ambiguity

Shape:

- entry bar fills short at `105.0`
- stop-loss is `110.0`
- take-profit is `100.0`
- same bar high is at least `115.0`
- same bar low is at most `95.0`

Expected:

- exactly one trade
- `direction == "short"`
- `exit_reason == "stop_loss"`
- `exit_price == 110.0` when slippage is zero

### 2. Long Gap-Through Same-Bar Ambiguity

Shape:

- long is already open at `100.0`
- stop-loss is `95.0`
- take-profit is `105.0`
- next bar opens at `90.0`
- same bar high is at least `112.0`
- same bar low is at most `85.0`

Expected:

- `exit_reason == "stop_loss"`
- `exit_price == 90.0` when slippage is zero
- warning includes gap execution on stop-loss

### 3. Short Gap-Through Same-Bar Ambiguity

Shape:

- short is already open at `100.0`
- stop-loss is `105.0`
- take-profit is `95.0`
- next bar opens at `112.0`
- same bar high is at least `115.0`
- same bar low is at most `90.0`

Expected:

- `exit_reason == "stop_loss"`
- `exit_price == 112.0` when slippage is zero
- warning includes gap execution on stop-loss

## Acceptance Criteria For Tasks 469-474

- Focused tests pass.
- No production code changes unless a test exposes a real mismatch.
- `git diff --check` passes.
- The stop-loss-first contract remains explicit in test names and assertions.
