# One-Bar Execution Delay Stress Test Design (Task 053F)

## 1. Goal & Rationale

The current `stress_one_bar_delay` in `validation_engine/stress_test.py` uses a naive data-shifting approach (shifting OHLCV columns forward by 1). This is functionally flawed because it delays both the indicators and the prices identically, meaning the strategy trades the exact same price patterns merely with shifted timestamps. 

A true "execution delay stress test" must simulate latency in order routing or execution without altering when the trading signal was conceptually generated. If a signal fires at Bar $T$ close, the baseline engine executes at Bar $T+1$ open. A 1-bar execution delay should force the engine to execute at Bar $T+2$ open, using the price at $T+2$, while keeping the indicators and signal generation strictly pegged to Bar $T$. 

This design outlines how to implement true execution delay natively in the backtest engine while preserving the baseline behavior and completely avoiding future-leak.

## 2. Scope & Location

- **Core Engine API (`backtest_engine/runner.py`)**: Add an `execution_delay_bars: int = 0` parameter to `run_backtest()`.
- **Validation Engine (`validation_engine/stress_test.py`)**: Rewrite the `stress_one_bar_delay` function to utilize the new engine parameter rather than shifting DataFrames.
- **Tests (`tests/test_stress_test.py`, `tests/test_backtest_engine.py`)**: Introduce rigorous assertions to verify delayed prices.

## 3. Engine Design Details

### 3.1 Preserving Baseline Behavior
The parameter `execution_delay_bars` will default to `0`. When `0`, the existing engine loop logic remains entirely untouched. Baseline behavior (signal at $T$ close, execution at $T+1$ open) is perfectly preserved.

### 3.2 Modifying the `pending` State Machine
Currently, the engine uses:
```python
pending: tuple[str, str] | None = None
```
When a signal is generated at bar $T$, `pending = ("enter", "long")` is set, and it is executed at the start of bar $T+1$.

**Proposed Change**:
Modify the pending state to track a countdown:
```python
pending: tuple[str, str, int] | None = None
```
Where the third element is the `bars_remaining` until execution. 
- When a signal fires at bar $T$, set `pending = ("enter", "long", execution_delay_bars)`.
- At the open of bar $T+1$, check `pending`. 
  - If `bars_remaining == 0`, execute the trade immediately.
  - If `bars_remaining > 0`, decrement the counter (`bars_remaining -= 1`) and do **not** execute yet.

### 3.3 No Future-Leak Guarantee
Because the delay mechanism only acts on the execution phase and purely uses a state-machine countdown (`bars_remaining -= 1` per loop iteration), it only looks at the *current* bar's open price when the counter hits zero. It does not peek ahead in the arrays, nor does it shift historical arrays. The indicators evaluate exactly as they did before. This strictly prevents future-leak.

### 3.4 Handling Stop-Loss / Take-Profit (SL/TP)
Intra-bar SL/TP logic operates on *open positions*. If a pending entry is delayed from $T+1$ to $T+2$, the position does not exist during $T+1$. Therefore, SL/TP cannot be hit during $T+1$. The position is officially opened at $T+2$, and SL/TP bounds are calculated from the $T+2$ open price. This accurately reflects real-world latency.

### 3.5 Handling Conflicting Signals During Delay
If an `enter` signal is pending and counting down, what happens if an `exit` signal fires during the wait period? Or an opposite `enter`?
**Conservative Assumption**: The engine's existing logic only checks entry signals when `position is None`. While delayed, `position` is still `None`, so new entry signals could theoretically evaluate.
**Design Rule**: If `pending` is not `None`, we should bypass new entry signal evaluation to prevent a newer signal from overwriting an already-routed (but delayed) order. We treat the delayed order as "in flight" and inescapable.

## 4. Validation Engine Rewrite

The `stress_one_bar_delay` function in `validation_engine/stress_test.py` will be rewritten as:

```python
def stress_one_bar_delay(
    strategy: Strategy,
    df: pd.DataFrame,
    baseline: BacktestResult,
    *,
    instrument=None,
) -> StressTestResult:
    # 1. Reject if no baseline trades (vacuously passes)
    # 2. Call run_backtest with execution_delay_bars=1
    stressed = run_backtest(
        strategy, df,
        execution_delay_bars=1,
        instrument=instrument,
    )
    # 3. Compare stressed metrics to baseline metrics
    # 4. Return standard StressTestResult
```

### Outputs & Assumptions Reporting
The `run_backtest` function must append `execution_delay_bars` to the result's `assumptions` dictionary. The `StressTestResult` will inherit these assumptions. 

## 5. Required Deterministic Test Cases

Before or during implementation, the following tests must be created:

1. **Baseline Equivalence**: `execution_delay_bars=0` must yield byte-for-byte identical trades and equity curves as the current master branch.
2. **One-Bar Execution Shift**: Create a 5-bar mock DataFrame. Trigger a signal at Bar 0. With `delay=1`, assert the trade `entry_time` matches Bar 2's timestamp and `entry_price` matches Bar 2's open.
3. **In-Flight Signal Blocking**: Trigger a long signal at Bar 0. With `delay=1`, force a short signal condition to be true at Bar 1. Assert that the long trade still executes at Bar 2 and the short signal is ignored because the long order was already "in flight".
4. **End of Data Handling**: Trigger a signal on the second-to-last bar. With `delay=1`, the execution would happen on the final bar. Ensure it executes cleanly. Trigger a signal on the final bar. Ensure it safely drops the pending order without crashing.

## 6. Future Work (Out of Scope for Implementation Phase)

- **UI Wiring**: Exposing the delay parameter in the PySide6 runner configuration interface.
- **Reporting**: Displaying the delay stress degradation charts alongside slippage/commission stress in the PDF/HTML reports. 
- **Variable Latency**: Randomizing the delay per trade (e.g., simulating stochastic network lag). 
