# Task 040A — Volume Conditions Design

## 1. Overview
This document outlines the design for integrating volume-based conditions into the existing `Quant Strategy Lab` strategy generation and evaluation engine. It adheres to the project's strict no-future-leak policy and maps cleanly onto the existing `Condition` dataclass without requiring structural changes to the core strategy models.

## 2. Supported Condition Types

We propose two initial volume condition types to be supported by the MVP:
1. **VOLUME_THRESHOLD**: Compares the current bar's volume against a fixed absolute threshold.
   - Example: `volume > 5000`
2. **VOLUME_SMA**: Compares the current bar's volume against its own Simple Moving Average (SMA) over $N$ periods, optionally multiplied by a factor (to support "volume spikes").
   - Example: `volume > 1.5 * SMA(volume, 20)`

## 3. Data Model Mapping (Condition Schema)

The existing `core.models.strategy.Condition` dataclass is defined as:
```python
@dataclass
class Condition:
    indicator: str
    params: dict
    operator: str
    left: str = "close"
    right: float | str = 0.0
```

### 3.1. VOLUME_THRESHOLD Schema
- `indicator`: `"VOLUME"`
- `params`: `{}` (Empty, as there is no lookback period)
- `operator`: `">"` or `"<"`
- `left`: `"volume"` (Though `left` is often ignored by the specific evaluator function, we use `"volume"` for semantic correctness)
- `right`: `float` (The absolute volume threshold, e.g., `5000.0`)

### 3.2. VOLUME_SMA Schema
- `indicator`: `"VOLUME_SMA"`
- `params`: `{"period": int}` (e.g., `{"period": 20}`)
- `operator`: `">"` or `"<"`
- `left`: `"volume"`
- `right`: `float` (Acts as a multiplier for the SMA value. Defaults to `1.0` for a straight comparison, but can be `2.0` for a volume spike condition).

## 4. Evaluator Integration

### 4.1. Column Naming (`_col` function)
The `evaluator.py::_col` function will be updated:
- `"VOLUME"` -> returns `"volume"`
- `"VOLUME_SMA"` -> returns `f"volume_sma_{params.get('period', 20)}"`

### 4.2. Condition Dispatch (`evaluate_condition`)
- `ind == "VOLUME"`: Dispatches to the existing `_eval_threshold(_col("VOLUME", cond.params), df, i, op, cond.right)`
- `ind == "VOLUME_SMA"`: Dispatches to a new `_eval_volume_sma(cond, df, i, op)`

### 4.3. New Evaluator Function
```python
def _eval_volume_sma(cond: Condition, df: pd.DataFrame, i: int, op: str) -> bool:
    col = _col("VOLUME_SMA", cond.params)
    sma_val = df.at[i, col]
    vol_val = df.at[i, "volume"]
    
    if pd.isna(sma_val) or pd.isna(vol_val):
        return False
        
    multiplier = float(cond.right) if cond.right else 1.0
    target_val = sma_val * multiplier
    
    if op == ">":
        return vol_val > target_val
    elif op == "<":
        return vol_val < target_val
    return False
```

## 5. Indicator Calculation (`indicators.py`)

A new function will be added to `strategy_engine/indicators.py`:
```python
def volume_sma(series: pd.Series, period: int = 20) -> pd.Series:
    """Simple Moving Average of Volume over *period* bars."""
    return series.rolling(window=period, min_periods=period).mean()
```

## 6. Random Strategy Generator Integration (`generator.py`)

To allow the generator to produce these new conditions:
1. **Ranges**:
   - `DEFAULT_VOLUME_THRESHOLD_RANGE = (1000, 100000)` (Will need adjustment based on specific instruments, but provides a baseline)
   - `DEFAULT_VOLUME_SMA_PERIOD_RANGE = (5, 50)`
   - `DEFAULT_VOLUME_SMA_MULTIPLIER_RANGE = (0.5, 3.0)`
2. **Weights**: Add `"VOLUME"` and `"VOLUME_SMA"` to `_INDICATOR_TYPES` and adjust `_DEFAULT_INDICATOR_WEIGHTS`.
3. **Dispatch**: Update `_random_block` to handle the instantiation of `VOLUME` and `VOLUME_SMA` `Condition` objects using the above ranges.

## 7. No-Future-Leak Assumptions & Safety

- **Volume Column**: `df["volume"]` at index `i` only accesses the volume of the current bar.
- **Volume SMA**: Uses `pandas.Series.rolling(window=period).mean()`. This strictly operates on a backward-looking window `[i - period + 1 : i]`. No future data is consumed.
- **Warm-up**: The first `period - 1` bars of `VOLUME_SMA` will evaluate to `NaN`. The evaluator safely catches `pd.isna(sma_val)` and returns `False`, ensuring no trades are taken on uninitialized data.
- **Invalid Parameters**: If `cond.right` is an invalid type or missing, `float(cond.right)` falls back or fails safely (evaluator catches `TypeError`/`ValueError` and returns `False`).

## 8. Test Plan

When implementing this design, the following tests must be added/updated:

1. **`tests/test_indicators.py`**:
   - Verify `volume_sma` correctly computes the rolling mean.
   - Verify `volume_sma` has `NaN` for the first `period - 1` rows.
2. **`tests/test_strategy_generator.py`**:
   - Override indicator weights to force 100% `VOLUME` and `VOLUME_SMA` generation.
   - Assert the generated `Condition` blocks match the defined schemas.
3. **`tests/test_evaluator.py`** (or equivalent, e.g., `test_backtest_engine.py`):
   - Mock a DataFrame with specific `volume` and `volume_sma_20` columns.
   - Assert `VOLUME_THRESHOLD` correctly triggers on `>` and `<`.
   - Assert `VOLUME_SMA` correctly triggers on `>` and `<` with default `1.0` multiplier.
   - Assert `VOLUME_SMA` correctly evaluates a multiplier (e.g., `cond.right = 2.0`).
   - Assert behavior when volume or volume SMA is `NaN` is strictly `False`.
