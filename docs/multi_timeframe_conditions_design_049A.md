# Multi-Timeframe Conditions Design (Task 049A)

> **Hardening revision:** 2026-06-04 — DeepSeek V4 Pro design review.
> Key corrections: (1) Resolved incomplete final HTF candle contradiction —
> partial candles are dropped, not used.  (2) Clarified base `datetime` = bar
> START semantics with code citations.  (3) Expanded exact-match boundary
> justification.  (4) Updated test T26 for dropped-candle behavior.  See §4.6,
> §4.7, §10.10 for revised sections.

## 1. Executive Summary

This document specifies the architecture for adding **multi-timeframe (MTF) conditions**
to the Quant Strategy Lab strategy evaluation and backtesting pipeline.  The design
allows a strategy operating on a base timeframe (e.g., 1-minute bars) to include
conditions that reference indicators computed on a higher timeframe (e.g., 5-minute,
15-minute, or 60-minute bars), while providing **absolute guarantees against future
data leakage**.

### Design Principles

1. **Opt-in per condition** — existing strategies with no timeframe metadata behave
   exactly as before.  No migration required.
2. **Zero future leak** — a lower-timeframe bar may only see a higher-timeframe
   indicator value after that higher-timeframe candle is fully closed.
3. **Precompute-only** — all MTF indicator values are merged into the base DataFrame
   before the event-driven loop starts.  The main backtest loop is unchanged.
4. **No live trading assumptions** — no streaming / partial candle logic.
5. **No dataclass changes** — extends `Condition.params` dict (Option A).

### Scope

This document is **design only**.  No production Python code is modified.  The design
covers schema extension, alignment rules, precompute strategy, evaluator changes,
runner integration, generator plan, UI/report/export implications, edge cases, a
detailed test plan, and risk assessment.

---

## 2. Current Architecture Findings

### 2.1 Condition Model

**File:** [`core/models/strategy.py`](file:///d:/Quant_Strategy_Lab/core/models/strategy.py)

```python
@dataclass
class Condition:
    indicator: str           # "SMA", "RSI", "MACD", "ATR", "VOLUME", "VOLUME_SMA"
    params: dict             # {"period": 20}
    operator: str            # ">" or "<"
    left: str = "close"      # "close" (MVP)
    right: float | str = 0.0
```

The `params` dict is an **open dictionary** — it already carries varying keys per
indicator type (e.g., `{"period": N}` for SMA, `{"fast": F, "slow": S, "signal": G}`
for MACD).  Adding a `"timeframe"` key requires no structural changes.

### 2.2 Evaluator Dispatch

**File:** [`strategy_engine/evaluator.py`](file:///d:/Quant_Strategy_Lab/strategy_engine/evaluator.py)

The evaluator resolves indicator column names via the `_col()` helper (lines 21–36):

```python
def _col(name: str, params: dict) -> str:
    ind = name.upper()
    if ind == "SMA":
        return f"sma_{params.get('period', '')}"
    elif ind == "RSI":
        return f"rsi_{params.get('period', 14)}"
    # ... etc.
```

Column lookup is by **exact string match** against the DataFrame.  The evaluator
reads `df.at[i, col]` at the current bar index only — no forward peek.

NaN values during warmup cause all evaluators to return `False` (lines 86, 100, 122,
139).  This is the existing safe-default for missing data.

### 2.3 Indicator Precompute in Runner

**File:** [`backtest_engine/runner.py`](file:///d:/Quant_Strategy_Lab/backtest_engine/runner.py#L267-L326)

`_precompute_indicators()` (lines 267–326) iterates all four strategy blocks,
extracts each condition's indicator type and params, and computes the indicator
on `df["close"]` (or `df` for ATR) using backward-looking rolling windows.
A `seen: set[tuple]` prevents duplicate computation.

Currently, all indicators are computed on the **base DataFrame only**.  There is
no awareness of timeframe.

### 2.4 Resampler and the Two-Timestamp Contract

**File:** [`data_engine/resampler.py`](file:///d:/Quant_Strategy_Lab/data_engine/resampler.py)

The resampler produces two timestamps per output bar:

| Column | Meaning | Usage |
|--------|---------|-------|
| `datetime` | Start of the candle window (chart label) | Display only |
| `available_at` | Timestamp of the **last constituent bar** | Signal gate — the bar is not "known" until this time |

Grouper settings: `closed="left"`, `label="left"`.  A bucket covers
`[t, t + target_minutes)`.

**Example — 1-min -> 5-min:**

| Constituent bars | datetime | available_at |
|------------------|----------|--------------|
| 08:30, 08:31, 08:32, 08:33, 08:34 | 08:30 | 08:34 |
| 08:35, 08:36, 08:37, 08:38, 08:39 | 08:35 | 08:39 |

The `available_at` column is the foundation of the no-future-leak contract.

### 2.5 Backtest Execution Model

The runner (lines 119–191) uses a **pending action queue**:

1. Signal evaluated at bar close -> stored as `pending`.
2. Pending action executed at the **next bar's open**.
3. No same-bar optimistic assumptions.

This execution model is unchanged by MTF — signals are still evaluated at the
base-timeframe bar close.

### 2.6 Strategy Service and Generator

**File:** [`strategy_engine/generator.py`](file:///d:/Quant_Strategy_Lab/strategy_engine/generator.py)

The generator creates conditions with `Condition(indicator=..., params={...}, ...)`.
It currently never sets a `"timeframe"` key in `params`.  Provenance records
`parameter_ranges` and `rule_block_versions`.

**File:** [`app/services/strategy_service.py`](file:///d:/Quant_Strategy_Lab/app/services/strategy_service.py)

`StrategyService.get_ranked_strategies()` passes strategies through
`run_backtest()` without modification.  The service layer does not inspect
individual condition params.

### 2.7 Base DataFrame `datetime` Semantics (Critical for MTF Alignment)

The `datetime` column in the base (un-resampled) DataFrame represents the
**bar open / start timestamp**.  Verified from:

1. The normalizer passes through the source CSV's timestamp column as-is;
   for 1-minute bars, each row has a timestamp like `08:30`, `08:31`, etc.
2. The resampler (`resampler.py` line 160) uses `closed="left"` and
   `label="left"` on `pd.Grouper`, confirming that `datetime` is the bucket
   **start** — the bar covers `[datetime, datetime + base_minutes)`.

This is essential for MTF alignment: the base bar at `datetime = 08:34`
covers the minute from 08:34:00 to 08:34:59.  The signal is evaluated at
**bar close** (approximately 08:34:59).  By that time, any 5-minute HTF
candle whose last constituent bar timestamp is ≤ 08:34 is fully known.

Therefore the merge condition `HTF.available_at <= base.datetime` is the
correct no-future-leak gate.

---

## 3. Proposed Condition Schema

### Decision: Option A — Extend `Condition.params`

| Aspect | Option A (params extension) | Option B (explicit field) |
|--------|---------------------------|--------------------------|
| Dataclass change | None | Add `timeframe: int \| None = None` |
| JSON compat | Seamless — params is already `dict` | Requires migration for all existing JSON |
| SQLite compat | Seamless — stored as JSON blob | Requires schema migration |
| Test impact | Zero — existing tests don't set `timeframe` | All condition-creation tests need update |
| Code export | Minimal — exporters read params | All exporters need new field awareness |
| Semantic clarity | Slightly overloaded params | Cleaner model |
| Risk | Low | Medium — migration surface across JSON import/export, persistence, reports, tests |

**Chosen: Option A.**

**Justification:**
The `params` dict is already semantically overloaded per indicator type (SMA uses
`{"period"}`, MACD uses `{"fast", "slow", "signal"}`).  Adding `"timeframe"` is
consistent with this pattern.  Option B would require touching:
- `core/models/strategy.py` (dataclass change)
- `strategy_engine/generator.py` (all condition creation)
- `app/services/report_service.py` (JSON import/export)
- `reports/` (Python/NinjaTrader exporters)
- `repository/` (SQLite persistence layer)
- All test files that create `Condition` objects (~15 files)

Option A avoids all of these while maintaining full backward compatibility.

### Schema Specification

A condition referencing a higher timeframe includes `"timeframe"` in its `params`:

```python
# Base-timeframe condition (unchanged — no "timeframe" key):
Condition(indicator="SMA", params={"period": 20}, operator=">")

# Multi-timeframe condition (5-minute SMA on 1-minute base data):
Condition(indicator="SMA", params={"period": 20, "timeframe": 5}, operator=">")

# Multi-timeframe RSI on 60-minute bars:
Condition(indicator="RSI", params={"period": 14, "timeframe": 60}, operator="<", right=70.0)

# Multi-timeframe MACD on 15-minute bars:
Condition(indicator="MACD", params={"fast": 12, "slow": 26, "signal": 9, "timeframe": 15}, operator=">")
```

**Rules:**
1. `"timeframe"` value is an `int` representing target bar period in minutes.
2. If `"timeframe"` is absent, `None`, or equals the base timeframe, the condition
   operates on the base DataFrame (existing behavior).
3. `"timeframe"` must be ≥ base timeframe and an integer multiple of it (validated
   at precompute time, matching resampler constraints).
4. The `"timeframe"` key is **ignored** by existing code that doesn't check for it.

---

## 4. Time Alignment and No-Future-Leak Rules

This is the most critical section.  These rules **must** be enforced by any
implementation.

### 4.1 Core Invariant

> **A lower-timeframe bar at time `T` may only read a higher-timeframe indicator
> value from a candle whose `available_at ≤ T`.**

Equivalently: a higher-timeframe candle's indicator value becomes visible to the
base timeline only **after** that candle is fully closed.

### 4.2 Timestamp Arithmetic Example

Base: 1-minute bars.  Higher TF: 5-minute bars.

```
Base bars:   08:30  08:31  08:32  08:33  08:34  08:35  08:36  ...  08:39  08:40  ...
             ├──────────── HTF candle A ────────────┤├──────────── HTF candle B ────────────┤
HTF candle A: datetime=08:30, available_at=08:34, close=C_A
HTF candle B: datetime=08:35, available_at=08:39, close=C_B
```

SMA(20) computed on the 5-minute series produces a value at each 5-minute bar.
Let `SMA_A` = SMA value at candle A, `SMA_B` = SMA value at candle B.

| Base bar | Visible HTF SMA value | Reason |
|----------|-----------------------|--------|
| 08:30 | NaN (or prior) | Candle A not yet closed (available_at=08:34 > 08:30) |
| 08:31 | NaN (or prior) | Candle A not yet closed |
| 08:32 | NaN (or prior) | Candle A not yet closed |
| 08:33 | NaN (or prior) | Candle A not yet closed |
| **08:34** | **SMA_A** | Candle A just closed (available_at=08:34 == 08:34) |
| 08:35 | SMA_A (forward-filled) | Candle B not yet closed; last known = A |
| 08:36 | SMA_A (forward-filled) | Candle B not yet closed |
| 08:37 | SMA_A (forward-filled) | Candle B not yet closed |
| 08:38 | SMA_A (forward-filled) | Candle B not yet closed |
| **08:39** | **SMA_B** | Candle B just closed (available_at=08:39 == 08:39) |
| 08:40 | SMA_B (forward-filled) | Next candle not yet closed |

### 4.3 Merge Strategy

The alignment is achieved via `pd.merge_asof`:

```python
# Pseudocode — NOT production code
# base_df["datetime"] = bar START timestamp (see §2.7)
# htf_df["available_at"] = timestamp of last constituent bar (see §2.4)
merged = pd.merge_asof(
    base_df[["datetime"]],          # left: base timeline (bar start)
    htf_df[["available_at", col]],  # right: HTF indicator + gate timestamp
    left_on="datetime",
    right_on="available_at",
    direction="backward",           # only look at HTF candles already closed
)
```

`direction="backward"` guarantees that for each base bar at time `T`, the merge
selects the most recent HTF row whose `available_at ≤ T`.

### 4.4 Forward-Fill Semantics

After `merge_asof`, the HTF indicator value is **naturally forward-filled** — it
persists from the bar where it first appears until a newer HTF candle closes and
provides a new value.  No explicit `ffill()` call is needed; `merge_asof` handles
this by design.

### 4.5 No-Future-Leak Rules (Mandatory)

| # | Rule | Enforcement |
|---|------|-------------|
| 1 | A base bar at time `T` must NOT read any HTF candle whose `available_at > T` | `merge_asof(direction='backward')` |
| 2 | The **current incomplete** HTF candle must never be used | Incomplete candles with fewer than `target_minutes / source_minutes` constituent bars are **dropped** during precompute (see §4.7).  Partial final groups are unsafe — they may have fewer data points than expected, causing indicators to compute on incomplete data |
| 3 | HTF indicator values must be forward-filled only **after** the HTF candle's close timestamp (`available_at`) | `merge_asof` aligns on `available_at`, not `datetime` |
| 4 | If no HTF candle has closed yet (warmup), the merged value must be NaN | `merge_asof` returns NaN when no right-side key satisfies `≤ T` |
| 5 | Indicators on the HTF series must use backward-looking rolling windows only | Same constraint as base-TF indicators; enforced by existing `sma()`, `rsi()`, etc. |
| 6 | The resampler must use `available_at = last constituent bar timestamp` | Already implemented in `resampler.py` line 164 |

### 4.6 Final Incomplete HTF Candle — Dropped (Conservative Rule)

**Decision: Drop incomplete final HTF candles.**

When the resampled higher-timeframe DataFrame has a final candle with fewer
than the expected `target_minutes / source_minutes` constituent bars, that
candle is **dropped** before indicator computation and merge.

**Rationale:**
- A 5-minute HTF candle from a 1-minute base expects 5 constituent bars.
  If the data ends at 08:42, the resampler produces a candle with only 3 bars
  (08:40, 08:41, 08:42).  This candle has valid OHLCV but represents an
  incomplete period.
- Indicators computed on a series ending with a partial candle will have
  values that differ from what they would be if the candle were complete.
- The safest behavior is to drop the incomplete candle.  The last full HTF
  candle's indicator value forward-fills to the end of data via `merge_asof`.

The implementation must validate that each HTF candle has exactly
`target_minutes / source_minutes` constituent bars (or at minimum >1 bar).
Any candle failing this check is excluded before indicator computation.

**Correction of §10.10 contradiction:** The original design (v1) allowed
the incomplete final candle to be used (§10.10).  This has been **revised**
to the conservative rule: incomplete final HTF candles are **dropped**.
The resampler may emit partial candles, but the MTF precompute filter
excludes them.

### 4.7 Exact-Match Boundary Behavior

When a HTF candle's `available_at` exactly equals a base bar's `datetime`
(e.g., both are `08:34`), `merge_asof(direction='backward')` **includes** that
HTF value.  This is correct because:

1. Base `datetime` is the bar **start** (§2.7).  The bar at 08:34 covers
   the period [08:34:00, 08:35:00) for 1-minute bars.
2. Signal evaluation happens at bar **close** (~08:34:59) — see runner
   main loop lines 176–192, where `evaluate_block()` is called after
   mark-to-market at bar close.
3. The HTF candle whose last constituent bar timestamp is 08:34 is fully
   closed by 08:34:00 + 1 minute = approximately 08:34:59.
4. Therefore at signal evaluation time (bar close of 08:34), the HTF candle
   is fully known.  Including it via `merge_asof` exact-match is correct.

This aligns with the backtest execution model: "signal confirmed at bar close."
At bar close of 08:34, the 5-min candle ending at 08:34 is fully closed.

---

## 5. Indicator Precompute Strategy

### 5.1 Overview

MTF indicator precomputation happens inside `_precompute_indicators()` in
`backtest_engine/runner.py`.  The function will gain a new code path for conditions
that include `"timeframe"` in their `params`.

### 5.2 Proposed Algorithm

```
1.  Infer base_minutes from df["datetime"]:
      diffs = df["datetime"].diff().dropna()
      base_minutes = int(diffs.mode()[0].total_seconds() / 60)

2.  For each condition in all four blocks:
      tf = cond.params.get("timeframe")
      if tf is None or tf == base_minutes:
          # Existing path: compute indicator on base df
          (unchanged)
      else:
          # MTF path
          a.  Validate: tf > base_minutes, tf % base_minutes == 0
          b.  Build cache key: (indicator, params_tuple, tf)
          c.  If not in seen:
              i.   resampled_df = resample(df, source_minutes=base_minutes,
                                           target_minutes=tf)
              ii.  Compute indicator on resampled_df
                   (e.g., sma(resampled_df["close"], period))
              iii. Build merge frame: resampled_df[["available_at", indicator_col]]
              iv.  Rename indicator_col -> "{indicator_col}_tf_{tf}"
              v.   pd.merge_asof(df, merge_frame,
                                 left_on="datetime",
                                 right_on="available_at",
                                 direction="backward")
              vi.  Drop the "available_at" column from the merge result
              vii. Mark key as seen
```

### 5.3 Column Naming Convention

| Condition | Base column | MTF column |
|-----------|-------------|------------|
| SMA(20) on base | `sma_20` | — |
| SMA(20) on 5-min TF | — | `sma_20_tf_5` |
| RSI(14) on 15-min TF | — | `rsi_14_tf_15` |
| MACD on 60-min TF | — | `macd_line_tf_60`, `macd_signal_tf_60`, `macd_histogram_tf_60` |
| ATR(14) on 5-min TF | — | `atr_14_tf_5` |
| VOLUME_SMA(20) on 5-min TF | — | `volume_sma_20_tf_5` |

### 5.4 MACD Special Case

MACD produces three columns.  For MTF, all three must be merged with the `_tf_{N}`
suffix.  The evaluator's MACD handler currently reads `macd_line` and `macd_signal`
by hardcoded name.  For MTF, `_col()` must return `macd_line_tf_{N}` and
`macd_signal_tf_{N}` when the condition has a timeframe param.

### 5.5 Resampler Caching

If multiple conditions reference the same higher timeframe (e.g., SMA(20) on 5-min
and RSI(14) on 5-min), the resampled DataFrame should be computed **once** per
timeframe and reused.  The `seen` set should track `("RESAMPLE", tf)` to avoid
redundant resampling.

### 5.6 Base Timeframe Inference

The base timeframe is inferred from `df["datetime"].diff().mode()`.  This is robust
for regular data.  As a safety measure:

- If the mode is ambiguous (multiple modes), use the smallest.
- If the DataFrame has fewer than 2 rows, skip MTF precomputation (not enough data).
- **Alternative**: accept `base_minutes` as an optional parameter to `run_backtest()`
  for explicit control.  This is recommended for production but not required for MVP.

---

## 6. Evaluator Behavior

### 6.1 `_col()` Modification Plan

The `_col()` helper in `evaluator.py` must be updated to check for `"timeframe"`:

```python
def _col(name: str, params: dict) -> str:
    ind = name.upper()
    tf = params.get("timeframe")  # NEW: check for MTF

    if ind == "SMA":
        base = f"sma_{params.get('period', '')}"
    elif ind == "RSI":
        base = f"rsi_{params.get('period', 14)}"
    elif ind == "MACD":
        base = "macd_line"
    elif ind == "ATR":
        base = f"atr_{params.get('period', 14)}"
    elif ind == "VOLUME":
        base = "volume"
    elif ind == "VOLUME_SMA":
        base = f"volume_sma_{params.get('period', 20)}"
    else:
        base = f"{name.lower()}_{params.get('period', '')}"

    # Append timeframe suffix if present and non-None
    if tf is not None:
        return f"{base}_tf_{tf}"
    return base
```

### 6.2 Evaluator Function Changes

Individual evaluator functions (`_eval_sma`, `_eval_threshold`, `_eval_macd`,
`_eval_volume_sma`) require **no changes**.  They already:

1. Look up column by name from `_col()`.
2. Return `False` on `KeyError` (missing column).
3. Return `False` on `NaN` (warmup / missing data).

The MTF suffix is transparent to them — they just read a different column name.

### 6.3 MACD Evaluator Adjustment

The MACD evaluator currently hardcodes `"macd_line"` and `"macd_signal"`:

```python
def _eval_macd(df, i, op):
    line = df.at[i, "macd_line"]
    signal = df.at[i, "macd_signal"]
```

For MTF, this must be parameterized to accept the timeframe suffix.  The
`evaluate_condition()` function for MACD will need to pass the timeframe-aware
column names.  Proposed approach:

```python
elif ind == "MACD":
    tf = cond.params.get("timeframe")
    suffix = f"_tf_{tf}" if tf else ""
    return _eval_macd(df, i, op, suffix=suffix)
```

With `_eval_macd` updated:

```python
def _eval_macd(df, i, op, *, suffix=""):
    line = df.at[i, f"macd_line{suffix}"]
    signal = df.at[i, f"macd_signal{suffix}"]
```

### 6.4 Backward Compatibility

When `"timeframe"` is absent from `params`:
- `_col()` returns the existing column name (e.g., `sma_20`).
- `_eval_macd` receives `suffix=""`, reading `macd_line` and `macd_signal`.
- Behavior is **identical** to the current implementation.

---

## 7. Backtest Runner Integration Plan

### 7.1 Main Loop — No Changes

The event-driven loop in `run_backtest()` (lines 119–191) iterates base-timeframe
bars, evaluates signals at bar close, and executes at next bar open.  Because MTF
indicator values are precomputed and merged into the base DataFrame before the loop
starts, **the loop requires zero modifications**.

### 7.2 `_precompute_indicators()` — Extension

This is the **only function in `runner.py` that changes**.  The new logic:

1. Extracts `base_minutes` from the DataFrame.
2. For each condition with a `"timeframe"` param:
   a. Resamples `df` to the target timeframe (cached per timeframe).
   b. Computes the indicator on the resampled DataFrame.
   c. Merges the result back into `df` via `merge_asof` on `available_at`.
   d. Names the column with the `_tf_{N}` suffix.
3. For conditions without `"timeframe"`, the existing code path is unchanged.

### 7.3 `run_backtest()` Signature — No Changes

No new parameters are required.  The base timeframe is inferred from the data.
An optional `base_minutes` parameter may be added later for explicit control
but is not required for the initial implementation.

### 7.4 Assumptions Dict Extension

The `result.assumptions` dict should record MTF metadata when MTF conditions are
present:

```python
"multi_timeframe": {
    "base_minutes": 1,
    "higher_timeframes_used": [5, 15],
}
```

When no MTF conditions exist, this key is absent (backward compatible).

---

## 8. Generator Integration Plan

### 8.1 Overview

The generator (`strategy_engine/generator.py`) can be extended to optionally inject
`"timeframe"` into condition `params`.  This is a **separate implementation task**
and should NOT be combined with the engine changes.

### 8.2 Proposed Configuration

```python
# New parameter for generate_strategies():
allowed_timeframes: tuple[int, ...] = ()  # Empty = no MTF conditions generated

# Example: allow 5-min and 15-min higher timeframes
generate_strategies(count=10, seed=42, allowed_timeframes=(5, 15))
```

### 8.3 Generation Logic

When `allowed_timeframes` is non-empty:

1. For each condition, with some configurable probability `mtf_probability`
   (default 0.3), randomly assign a timeframe from `allowed_timeframes`.
2. Store the chosen timeframe (or `None` for base) in `cond.params["timeframe"]`.
3. Record `allowed_timeframes` and `mtf_probability` in provenance
   `parameter_ranges`.

### 8.4 Backward Compatibility

When `allowed_timeframes` is empty (default), no `"timeframe"` key is ever added
to `params`.  Existing generator behavior is **unchanged**.  The random seed
sequence is **unaffected** because MTF selection only occurs when the caller
explicitly enables it.

### 8.5 Provenance Extension

```python
"parameter_ranges": {
    # ... existing fields ...
    "allowed_timeframes": [5, 15],    # NEW (only when non-empty)
    "mtf_probability": 0.3,           # NEW (only when non-zero)
}
```

---

## 9. UI / Report / Export Considerations

### 9.1 Strategy Detail Widget

The `StrategyDetailWidget` currently formats conditions as human-readable strings
(e.g., `close > SMA(20)`).  For MTF conditions, the display should include the
timeframe:

```
close > SMA(20, TF=5m)
RSI(14, TF=15m) < 70
MACD(12/26/9, TF=60m) line > signal
```

### 9.2 Formula Parser

The formula parser (`strategy_engine/formula_parser.py`) currently parses strings
like `"close > SMA(20)"`.  For MTF, a proposed syntax extension:

```
close > SMA(20, tf=5)
RSI(14, tf=15) < 70
```

The parser would extract `tf=N` from the argument list and include it in `params`.

### 9.3 Ranking Table

No changes needed — the ranking table displays metrics, not condition details.

### 9.4 Report Generation

Markdown, HTML, and PDF reports that display strategy conditions should include
the timeframe annotation.  The report template rendering logic reads conditions
from the strategy object and formats them — it will need to check for
`params.get("timeframe")` and append the TF label.

### 9.5 JSON Export / Import

**Export:** Seamless.  `dataclasses.asdict(strategy)` already serializes `params`
as a dict, including any `"timeframe"` key.

**Import:** Seamless.  `preview_strategy_json()` in `report_service.py`
reconstructs `Condition` objects from the JSON `params` dict, which will
naturally include `"timeframe"` if present.

### 9.6 Python Research Export

The Python exporter generates reference logic like:

```python
long_entry = close > sma_20
```

For MTF conditions, the exported code should note the timeframe:

```python
# Requires 5-minute resampled data for SMA(20)
long_entry = close > sma_20_tf_5  # SMA(20) on 5-min bars
```

### 9.7 NinjaTrader Export

NinjaTrader supports multi-timeframe natively via `AddDataSeries()` and
`BarsInProgress`.  The exporter could emit:

```csharp
// Requires additional data series: 5-minute bars
// AddDataSeries(BarsPeriodType.Minute, 5);
bool longEntryCondition = Close[0] > SMA(Closes[1], 20)[0];
```

However, this is complex and should be a **separate task**.  For the initial
implementation, the NinjaTrader exporter should emit a commented warning when
MTF conditions are encountered:

```csharp
// WARNING: Multi-timeframe condition (TF=5m) detected.
// NinjaTrader export for MTF conditions is not yet supported.
// Manual AddDataSeries() setup required.
```

---

## 10. Edge Cases

### 10.1 First Lower-Timeframe Bars Before Any Higher-Timeframe Candle Closes

**Scenario:** Base is 1-min, HTF is 5-min.  The first 5-min candle closes at
`available_at = 08:34`.  Base bars 08:30–08:33 have no completed HTF candle.

**Behavior:** `merge_asof(direction='backward')` finds no right-side key with
`available_at ≤ 08:33`.  The merged column is `NaN`.  The evaluator returns
`False` for any condition referencing this column.

**Correctness:** This is the safe default — no signal during warmup.

### 10.2 Higher-Timeframe Candle Closes Exactly at Lower-Timeframe Bar Timestamp

**Scenario:** HTF candle A has `available_at = 08:34`.  Base bar at `08:34`.

**Behavior:** `merge_asof(direction='backward')` includes exact matches.
The base bar at `08:34` sees `SMA_A`.

**Correctness:** At bar close of `08:34`, the 5-min candle is fully closed.
The signal evaluation happens at bar close, so this is temporally correct.

### 10.3 Missing Volume Column for Higher-Timeframe Volume Conditions

**Scenario:** Strategy has a `VOLUME_SMA(20, tf=5)` condition, but the base
DataFrame's `volume` column contains all zeros or is missing.

**Behavior:** The resampler aggregates volume via `sum`.  If base volume is
all zeros, the resampled volume is also zero.  `volume_sma(zero_series, 20)`
returns zeros after warmup.  The condition `volume > volume_sma * 2.0`
evaluates to `False` (0 > 0 is false).

If the volume column is entirely missing, the resampler raises `ResamplerError`
("Required columns missing").  This is caught before the backtest loop.

**Correctness:** Safe.  No crash, no false positive.

### 10.4 Sparse Data / Holiday Gaps

**Scenario:** Base data has gaps (e.g., no bars between Friday 16:00 and
Monday 08:30).  The HTF candle spanning the gap may have fewer constituent
bars than expected.

**Behavior:** The resampler's `pd.Grouper` creates buckets by clock time.
Buckets with no data produce NaN rows, which are dropped by
`dropna(subset=["open"])` (line 170).  The surviving HTF candles have valid
OHLCV from whatever constituent bars exist.  `merge_asof` forward-fills
the last valid HTF value across the gap.

**Correctness:** The last known HTF value persists until a new candle closes.
This is conservative and correct — we don't fabricate data for gaps.

### 10.5 DST / Session Boundary Issues

**Scenario:** Daylight Saving Time causes a 1-hour shift.  A 60-minute HTF
candle may span a DST transition.

**Behavior:** The resampler groups by pandas `DatetimeIndex` with
`freq=f"{target_minutes}min"`.  Pandas handles timezone-naive timestamps
by absolute minute count.  If the input is timezone-aware, pandas respects
DST transitions in grouping.

**Correctness:** For the MVP (timezone-naive data), this works correctly.
For timezone-aware data, the behavior depends on the pandas version and
timezone handling.  This is an existing limitation of the resampler, not
specific to MTF.

**Recommendation:** Document that MTF assumes timezone-naive timestamps
(consistent with the current normalizer output).

### 10.6 Multiple Higher Timeframes in One Strategy

**Scenario:** A strategy has conditions referencing 5-min, 15-min, and 60-min
bars simultaneously.

**Behavior:** Each timeframe triggers a separate resample + indicator compute +
merge_asof pass.  The base DataFrame accumulates columns like `sma_20_tf_5`,
`rsi_14_tf_15`, `atr_14_tf_60`.  Each merge is independent and correct.

**Correctness:** Fully supported.  The `seen` set in `_precompute_indicators()`
prevents duplicate computation per (indicator, params, timeframe) tuple.

### 10.7 JSON Export / Import Compatibility

**Scenario:** A strategy with MTF conditions is exported to JSON, then imported
on a version of the software that doesn't support MTF.

**Behavior:** The `"timeframe"` key in `params` is preserved in JSON.  On import,
the `Condition` is reconstructed with `params={"period": 20, "timeframe": 5}`.
If the importing version's `_precompute_indicators()` doesn't handle `"timeframe"`,
the MTF column (e.g., `sma_20_tf_5`) is never created.  The evaluator's `KeyError`
catch returns `False` for that condition.

**Correctness:** The condition silently fails (returns `False`), which is safe.
No crash.  The user sees fewer signals but no corrupted results.

### 10.8 Python / NinjaTrader Export for Unsupported MTF Conditions

**Scenario:** User exports a strategy containing MTF conditions to Python or
NinjaTrader format.

**Behavior:**
- **Python exporter:** Should emit a comment noting the timeframe dependency
  and the column name convention.
- **NinjaTrader exporter:** Should emit a `// WARNING` comment and skip
  the MTF condition logic (or emit a placeholder requiring manual
  `AddDataSeries` setup).

**Correctness:** The exporter must NOT silently omit the condition.  It must
either translate it correctly or emit a visible warning.

### 10.9 Multi-Instrument Backtest with Per-Instrument Resampling

**Scenario:** `run_multi_instrument_backtest()` runs the same strategy on
multiple `(DataFrame, InstrumentProfile)` pairs.

**Behavior:** Each instrument's data is independently passed to `run_backtest()`,
which calls `_precompute_indicators()` on that instrument's DataFrame.  The
resampling and merge happen independently per instrument.

**Correctness:** Fully correct.  Each instrument has its own timeline and
its own resampled bars.  No cross-instrument data leakage.

### 10.10 Incomplete Higher-Timeframe Candle at End of Data

**Scenario:** Base data ends at 08:42 (1-min bars).  The last complete 5-min
candle covers 08:40–08:44, but bars 08:43 and 08:44 don't exist.

**Behavior (Revised — Conservative Rule, §4.6):** The resampler produces
a partial candle with `datetime=08:40, available_at=08:42` (3 bars instead
of 5).  The MTF precompute logic **drops** this incomplete candle before
indicator computation.  The last complete HTF candle's indicator value
forward-fills to the end of data via `merge_asof`.

**Correctness:** This is the safe default.  The partial candle is excluded
because indicators computed on it would differ from what the full candle
would produce.  No trades are falsely triggered by incomplete-candle data.

**Rationale for revision:** The original design (v1) allowed partial final
candles.  Hardening review determined this violates the no-future-leak
spirit — the indicator value from a partial candle is not the same as from
a complete candle.  Conservative behavior is to drop the incomplete candle.

### 10.11 Higher Timeframe Equals Base Timeframe

**Scenario:** A condition has `"timeframe": 1` on 1-minute base data.

**Behavior:** The precompute logic detects `tf == base_minutes` and falls
through to the existing (non-MTF) code path.

**Correctness:** Identity — no resampling needed.  The condition operates
on the base DataFrame directly.

---

## 11. Test Plan

### 11.1 Unit Tests — Resampler + Merge Integration

| # | Test | Description |
|---|------|-------------|
| T1 | `test_merge_asof_basic_alignment` | 10 1-min bars -> 2 5-min bars.  Verify that base bars 0–3 see NaN, bar 4 sees HTF candle A value, bars 5–8 see HTF candle A (forward-filled), bar 9 sees HTF candle B. |
| T2 | `test_merge_asof_exact_boundary` | HTF `available_at=08:34`, base bar at `08:34`.  Verify base bar sees the HTF value (not NaN). |
| T3 | `test_merge_asof_no_future_leak` | For every base bar at time T, verify that the merged HTF value comes from a candle with `available_at ≤ T`.  No exceptions. |
| T4 | `test_merge_asof_forward_fill_persistence` | Verify that a HTF value persists for all base bars between two HTF candle closes. |
| T5 | `test_merge_asof_gap_handling` | Base data with a gap (e.g., missing bars 08:35–08:39).  Verify that bar 08:40 still sees the last closed HTF value. |

### 11.2 Unit Tests — Precompute + Column Naming

| # | Test | Description |
|---|------|-------------|
| T6 | `test_precompute_mtf_sma_column_exists` | Strategy with SMA(20, tf=5).  After precompute, verify `sma_20_tf_5` exists in df. |
| T7 | `test_precompute_mtf_rsi_column_exists` | Strategy with RSI(14, tf=15).  After precompute, verify `rsi_14_tf_15` exists. |
| T8 | `test_precompute_mtf_macd_columns_exist` | Strategy with MACD(tf=60).  After precompute, verify `macd_line_tf_60`, `macd_signal_tf_60`, `macd_histogram_tf_60` exist. |
| T9 | `test_precompute_mtf_atr_column_exists` | Strategy with ATR(14, tf=5).  After precompute, verify `atr_14_tf_5` exists. |
| T10 | `test_precompute_no_timeframe_unchanged` | Strategy with SMA(20) and no timeframe.  After precompute, verify `sma_20` exists (not `sma_20_tf_*`). |
| T11 | `test_precompute_dedup_same_timeframe` | Two conditions both using tf=5 (SMA and RSI).  Verify resample is called once (mock/spy). |
| T12 | `test_precompute_multiple_timeframes` | SMA(20, tf=5) + RSI(14, tf=15).  Verify both `sma_20_tf_5` and `rsi_14_tf_15` exist. |

### 11.3 Unit Tests — Evaluator MTF Column Resolution

| # | Test | Description |
|---|------|-------------|
| T13 | `test_col_with_timeframe_returns_suffixed_name` | `_col("SMA", {"period": 20, "timeframe": 5})` returns `"sma_20_tf_5"`. |
| T14 | `test_col_without_timeframe_returns_base_name` | `_col("SMA", {"period": 20})` returns `"sma_20"`. |
| T15 | `test_col_macd_with_timeframe` | `_col("MACD", {"timeframe": 60})` returns `"macd_line_tf_60"`. |
| T16 | `test_evaluate_condition_mtf_reads_correct_column` | Create df with both `sma_20` and `sma_20_tf_5` (different values).  Verify that MTF condition reads `sma_20_tf_5`. |
| T17 | `test_evaluate_condition_mtf_missing_column_returns_false` | Condition references `sma_20_tf_5` but column doesn't exist.  Verify returns `False`. |

### 11.4 Integration Tests — Full Backtest with MTF

| # | Test | Description |
|---|------|-------------|
| T18 | `test_backtest_mtf_condition_produces_trades` | Strategy with SMA(5, tf=5) on 1-min uptrend data.  Verify trades are produced after HTF warmup. |
| T19 | `test_backtest_mtf_no_trades_during_warmup` | Verify no trades occur before the first HTF candle closes AND the indicator warmup completes. |
| T20 | `test_backtest_mtf_no_future_leak_entry_timing` | Verify that the first trade entry occurs at the correct bar — not before the HTF indicator value should be available. |
| T21 | `test_backtest_mtf_accounting_identity` | Sum of trade PnL == final equity - initial capital (with MTF strategy). |
| T22 | `test_backtest_mtf_assumptions_recorded` | Verify `result.assumptions` includes `multi_timeframe` metadata. |
| T23 | `test_backtest_base_only_strategy_unchanged` | Run existing SMA crossover strategy.  Verify results are bit-for-bit identical to pre-MTF code. |

### 11.5 Edge Case Tests

| # | Test | Description |
|---|------|-------------|
| T24 | `test_mtf_first_bars_before_htf_close_evaluate_false` | First 4 base bars (before any 5-min candle closes) -> all MTF conditions return False. |
| T25 | `test_mtf_exact_boundary_match` | Base bar datetime == HTF available_at -> condition sees the HTF value. |
| T26 | `test_mtf_incomplete_final_candle_dropped` | Data ends mid-candle (e.g., base has 3 bars of a 5-bar HTF window).  Verify the incomplete final HTF candle is **dropped** — no indicator value computed from it.  The last complete candle value forward-fills.  |
| T27 | `test_mtf_multiple_timeframes_independent` | Strategy with tf=5 and tf=15 conditions.  Verify each reads the correct column. |
| T28 | `test_mtf_timeframe_equals_base_is_noop` | Condition with `"timeframe": 1` on 1-min data.  Verify it uses the base column. |
| T29 | `test_mtf_condition_json_roundtrip` | Export strategy to JSON, reimport.  Verify `"timeframe"` key is preserved. |
| T30 | `test_mtf_invalid_timeframe_ratio_raises` | Condition with `"timeframe": 7` on 1-min data (7 is not a multiple).  Verify clear error. |

### 11.6 Generator Tests (for future implementation)

| # | Test | Description |
|---|------|-------------|
| T31 | `test_generator_no_mtf_by_default` | `generate_strategies()` with defaults produces no `"timeframe"` in any condition params. |
| T32 | `test_generator_mtf_respects_allowed_timeframes` | With `allowed_timeframes=(5, 15)`, all generated timeframes are in {5, 15}. |
| T33 | `test_generator_mtf_strategies_backtestable` | All generated MTF strategies run through `run_backtest()` without error. |
| T34 | `test_generator_mtf_provenance_records_config` | Provenance includes `allowed_timeframes` and `mtf_probability`. |

---

## 12. Risks and Deferred Items

### 12.1 Risks

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| R1 | **Performance** — Precomputing multiple timeframes adds memory + CPU overhead (one resample + merge per unique timeframe) | Medium | Cache resampled DataFrames per timeframe.  For N conditions on K unique timeframes, cost is O(K × resample) + O(K × merge_asof).  Acceptable for backtesting; monitor for large datasets. |
| R2 | **Base timeframe inference** — `df["datetime"].diff().mode()` may be ambiguous on irregular data | Low | Use smallest mode value.  Optionally accept `base_minutes` as explicit parameter.  Add validation warning if mode is ambiguous. |
| R3 | **Pandas version dependency** — `merge_asof` behavior with timezone-aware datetimes varies across pandas versions | Low | Document timezone-naive assumption.  Test with the project's pinned pandas version. |
| R4 | **MACD column naming** — MACD produces 3 columns, requiring special handling in both precompute and evaluator | Low | Explicit handling already required; document the pattern clearly. |
| R5 | **Semantic overload of params** — Adding `"timeframe"` to params increases cognitive load | Low | Acceptable tradeoff vs. dataclass migration.  Revisit if params grows further (e.g., > 5 keys). |
| R6 | **Generator RNG stability** — Adding MTF generation may alter RNG sequence for non-MTF calls | Medium | Use separate RNG draws for MTF decisions (only when `allowed_timeframes` is non-empty).  Verify with regression test. |

### 12.2 Deferred Items

| # | Item | Reason |
|---|------|--------|
| D1 | Full NinjaTrader MTF export (`AddDataSeries` + `BarsInProgress`) | Complex NinjaScript API; separate task |
| D2 | Formula parser MTF syntax (`tf=N`) | Requires parser grammar extension; separate task |
| D3 | Explicit `base_minutes` parameter on `run_backtest()` | Nice-to-have; inference works for MVP |
| D4 | Timezone-aware MTF resampling | Current normalizer outputs timezone-naive; future enhancement |
| D5 | Real-time / streaming MTF (partial candle handling) | Explicitly excluded per design principle #4 |
| D6 | Cross-timeframe condition operators (e.g., "5-min SMA > 15-min SMA") | Requires evaluator architecture change; future enhancement |
| D7 | UI for configuring MTF timeframes in the generator settings panel | Separate UI task |
| D8 | Walk-forward / Monte Carlo with MTF strategies | Should work transparently since they call `run_backtest()`, but needs verification |

---

## Appendix A: Implementation Task Decomposition (Proposed)

| Subtask | Scope | Risk | Suggested Agent |
|---------|-------|------|-----------------|
| 049B — Runner MTF precompute | Extend `_precompute_indicators()` with resample + merge | Medium | DeepSeek |
| 049C — Evaluator MTF column resolution | Update `_col()` and MACD handler | Low | Anti-Gravity |
| 049D — MTF test suite | Implement tests T1–T30 | Low | Anti-Gravity |
| 049E — Generator MTF injection | Add `allowed_timeframes` parameter | Low | Anti-Gravity |
| 049F — UI/Report MTF display | Update detail widget, report templates | Low | Anti-Gravity |
| 049G — Code export MTF handling | Python warning, NinjaTrader warning | Low | Anti-Gravity |
| 049H — Integration acceptance | End-to-end smoke, regression | Low | Codex |

---

## Appendix B: Mandatory Checklist

| # | Question | Answer |
|---|----------|--------|
| 1 | Did you inspect Condition / StrategyBlock models? | ✅ Yes — [`strategy.py`](file:///d:/Quant_Strategy_Lab/core/models/strategy.py) lines 17–39 |
| 2 | Did you inspect evaluator.py? | ✅ Yes — [`evaluator.py`](file:///d:/Quant_Strategy_Lab/strategy_engine/evaluator.py) lines 21–36 (`_col`), 39–60 (`evaluate_condition`), 63–71 (`evaluate_block`), 116–128 (`_eval_macd`) |
| 3 | Did you inspect backtest_engine/runner.py precompute behavior? | ✅ Yes — [`runner.py`](file:///d:/Quant_Strategy_Lab/backtest_engine/runner.py#L267-L326) `_precompute_indicators()` lines 267–326 |
| 4 | Did you inspect data_engine/resampler.py? | ✅ Yes — [`resampler.py`](file:///d:/Quant_Strategy_Lab/data_engine/resampler.py) lines 44–175, two-timestamp contract, `available_at` derivation |
| 5 | Did you choose and justify schema option A or B? | ✅ Option A — params extension.  Zero migration, full backward compat.  See §3. |
| 6 | Did you define exact no-future-leak alignment rules? | ✅ Yes — §4.1–4.6 with timestamp arithmetic, `merge_asof` direction, boundary behavior |
| 7 | Did you define warmup behavior? | ✅ Yes — §4.2 (NaN before first HTF close), §10.1, T19, T24 |
| 8 | Did you define missing data behavior? | ✅ Yes — NaN -> evaluator returns False.  §10.3 (missing volume), §10.7 (import compat) |
| 9 | Did you define generator integration plan? | ✅ Yes — §8 with `allowed_timeframes`, backward compat, provenance extension |
| 10 | Did you define JSON/code export implications? | ✅ Yes — §9.5 (JSON), §9.6 (Python), §9.7 (NinjaTrader), §10.8 (unsupported MTF) |
| 11 | Did you avoid production code changes? | ✅ Yes — this is a design-only document |
| 12 | Did full suite pass? | ✅ Yes — test suites for resampler, indicators, backtest, strategy generator all pass.  MTF tests (T1–T34) will be added in Task 049D. |
