# Slippage and Tick-Size Rounding Enforcement Design - Tasks 475-480

Design document. No production code changed.

Date: 2026-06-11

## Current Behavior Finding

`backtest_engine/runner.py` currently applies slippage as:

- long entry: `bar_open + slippage_ticks * tick_size`
- short entry: `bar_open - slippage_ticks * tick_size`
- long signal exit: `bar_open - slippage_ticks * tick_size`
- short signal exit: `bar_open + slippage_ticks * tick_size`
- long SL/TP exit: `trigger_price - slippage_ticks * tick_size`
- short SL/TP exit: `trigger_price + slippage_ticks * tick_size`
- session-end long exit: `bar_close - slippage_ticks * tick_size`
- session-end short exit: `bar_close + slippage_ticks * tick_size`

The end-of-data liquidation path uses `last_close` directly and does not apply
slippage.

The engine does not currently align calculated execution prices or percent-based
SL/TP levels to `tick_size`. This means unaligned input data, percent-based
risk settings, or fractional slippage can produce fills that are not valid
instrument ticks.

## Design Decision

Use side-aware conservative tick alignment for execution fills.

Do not use nearest-tick rounding for fills, because nearest rounding can improve
the trader's price. Instead:

- buy-like fills round up
  - long entry
  - short exit
- sell-like fills round down
  - short entry
  - long exit

This keeps alignment pessimistic or neutral.

## Proposed Helper

Add small helpers near runner internals:

```python
def _tick_decimals(tick_size: float) -> int:
    ...

def _align_price_to_tick(price: float, tick_size: float, *, side: str) -> float:
    if tick_size <= 0:
        return price
    steps = price / tick_size
    if side == "buy":
        aligned = math.ceil(steps - 1e-12) * tick_size
    elif side == "sell":
        aligned = math.floor(steps + 1e-12) * tick_size
    else:
        raise ValueError("side must be 'buy' or 'sell'")
    return round(aligned, _tick_decimals(tick_size))
```

Use `side="buy"` for long entries and short exits. Use `side="sell"` for short
entries and long exits.

## Proposed Scope For Tasks 481-486

Modify:

- `backtest_engine/runner.py`
- `tests/test_backtest_engine.py`
- `docs/task_board.md`
- `docs/changelog.md`

Do not modify:

- ranking, validation, reports, UI, or repositories

## Required Tests

1. Long entry with unaligned open and slippage rounds up to the next tick.
2. Short entry with unaligned open and slippage rounds down to the previous tick.
3. Long signal exit with unaligned open and slippage rounds down.
4. Short signal exit with unaligned open and slippage rounds up.
5. Long SL/TP fill with unaligned trigger/gap price rounds down.
6. Short SL/TP fill with unaligned trigger/gap price rounds up.
7. Session-end long exit rounds down.
8. Session-end short exit rounds up.

Optional design decision for implementation:

- Decide whether `end_of_data` liquidation should remain a mark-to-close path
  without slippage, or become a forced liquidation path with side-aware
  slippage. If changed, add explicit tests and update assumptions. Do not make
  this change silently.

## Acceptance Criteria For Tasks 481-486

- Execution fills are tick-aligned in all assigned fill paths.
- Alignment is conservative by direction.
- Existing stop-loss-first behavior remains unchanged.
- Focused backtest tests pass.
- `git diff --check` passes.
