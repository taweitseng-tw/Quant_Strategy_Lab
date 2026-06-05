# Multi-Instrument Backtest Design (Task 032A)

## 1. Objective
Run a given `Strategy` across multiple datasets and instrument profiles while strictly preserving the single-instrument `run_backtest` flow in `backtest_engine/runner.py`.

## 2. Architecture & Single-Instrument Preservation
- **No changes to Engine:** `backtest_engine/runner.py` remains strictly single-instrument. 
- **New Service:** A new `app/services/multi_instrument_service.py` will orchestrate the multi-instrument logic.
- **Orchestration:** The service loops over provided instrument configs and calls `run_backtest` for each. This ensures the single-instrument flow is untouched and backwards compatible.

## 3. Data Structures

We will introduce two dataclasses in `app/services/multi_instrument_service.py`:

```python
from dataclasses import dataclass
import pandas as pd
from core.models.instrument import InstrumentProfile
from core.models.backtest_result import BacktestResult

@dataclass
class InstrumentRunConfig:
    label: str
    df: pd.DataFrame
    instrument: InstrumentProfile | None

@dataclass
class PerInstrumentBacktestResult:
    label: str
    instrument_symbol: str
    success: bool
    backtest_result: BacktestResult | None
    error_message: str | None

@dataclass
class MultiInstrumentBacktestResult:
    instrument_count: int
    passed_count: int
    failed_count: int
    
    # Aggregated metrics (only from successful runs)
    mean_total_pnl: float
    median_total_pnl: float
    min_total_pnl: float
    max_drawdown_worst: float
    mean_profit_factor: float | None
    total_trades_sum: int
    
    per_instrument_results: list[PerInstrumentBacktestResult]
```

## 4. Aggregation Rules
Aggregations are computed **only** on instruments where `success == True`.
- `mean_total_pnl`: Arithmetic mean of `total_pnl` across passed instruments.
- `median_total_pnl`: Median of `total_pnl`.
- `min_total_pnl`: Minimum `total_pnl`.
- `max_drawdown_worst`: Maximum (largest positive magnitude) `max_drawdown_pnl` across passed runs.
- `mean_profit_factor`: Mean of numeric `profit_factor`. Instruments with non-numeric PF (e.g. division by zero or NaN) are excluded from the mean.
- `total_trades_sum`: Sum of `total_trades`.

## 5. Error & Warning Behavior
- If `run_backtest` throws an exception for an instrument, `success` becomes `False`, and `error_message` captures the exception. It does **not** crash the entire multi-instrument run.
- Warnings from `BacktestResult.warnings` are preserved in the `PerInstrumentBacktestResult.backtest_result.warnings`.
- If an empty instrument list is provided, the service returns a `MultiInstrumentBacktestResult` with zeros/safely defaulted metrics.

## 6. Deterministic Ordering
- The input to the service will be a list of `InstrumentRunConfig`.
- The `per_instrument_results` output list will have the exact same order as the input list.

## 7. Concrete Tests for Task 032B
- `test_multi_instrument_service_runs_all_instruments`: Verifies multiple instruments return correctly sized results.
- `test_multi_instrument_preserves_order`: Asserts deterministic ordering matches input.
- `test_multi_instrument_aggregations`: Verifies mean, median, min, max_drawdown, profit_factor mean, and trade sum logic.
- `test_multi_instrument_handles_single_failure_gracefully`: If one dataframe is empty/corrupt, it fails safely while others pass.
- `test_multi_instrument_empty_input`: Verifies safe handling of 0 inputs (returns safe zeros).
- `test_multi_instrument_does_not_mutate_dataframes`: Verifies input DataFrames remain unchanged.
