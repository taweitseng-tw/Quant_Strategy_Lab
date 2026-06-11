# Data Resampling and Normalization Hardening Design - Tasks 499-504

Design document for hardening data resampling and normalization modules in Quant Strategy Lab. No production code changes are made in this round.

Date: 2026-06-11

---

## 1. Audit of Current Behavior

### 1.1 Schema Normalizer (`normalizer.py`)
- **Column Aliasing**: Maps common Date, Time, Timestamp, TotalVolume, and Price aliases (lowercase, stripped) to canonical names: `datetime, open, high, low, close, volume`.
- **Date + Time Handling**: Detects and combines separate Date and Time columns into a single `datetime` column.
- **Uncanonical Columns**: Discards any columns not present in `INTERNAL_COLUMNS`.
- **Datetime Parsing & Validation**:
  - Rejects rows containing `NaT` (unparseable datetimes) by raising `NormalizerError`.
  - Sorts values by `datetime` and resets the index.
  - Rejects duplicate timestamps by checking `.duplicated().any()` and raising `NormalizerError`.

### 1.2 OHLCV Resampler (`resampler.py`)
- **Parameter Validation**: Enforces that `target_minutes >= source_minutes` and that `target_minutes` is a multiple of `source_minutes`.
- **Identity Mode**: If `target_minutes == source_minutes`, skips grouping and returns the canonical DataFrame with `available_at` mapped to `datetime`.
- **Type Checking**: Asserts that `datetime` is `datetime64` (recommending running normalizer first), rejects `NaT`, and checks for duplicates.
- **Aggregation**:
  - Sorts input by `datetime`.
  - Preserves a copy of the datetime as `_dt` for lookahead-safe availability logic.
  - Groups using `pd.Grouper(freq="[target_minutes]min", closed="left", label="left")`.
  - Aggregates OHLCV: `open` = first, `high` = max, `low` = min, `close` = last, `volume` = sum.
  - Maps `available_at` = last `_dt` in the group (the lookahead-safe two-timestamp contract).
  - Drops empty buckets via `.dropna(subset=["open"])`.

---

## 2. Identified Edge Cases & Gaps

### 2.1 OHLC Logical Consistency & Numeric Validity (High Priority Gap)
- **Gaps**:
  - The normalizer validates required OHLCV column presence but does not validate numeric dtype or basic price/volume logic.
  - The resampler validates numeric dtype, but it does not validate OHLC relationships, finite values, or price/volume bounds.
  - It does not verify:
    - Price logical boundaries: `high >= open`, `high >= close`, `high >= low`, `low <= open`, `low <= close`.
    - Positive prices: `open > 0`, `high > 0`, `low > 0`, `close > 0` (negative/zero prices can break percentage-based SL/TP or backtest logic).
    - Volume validity: `volume >= 0`.
    - Absence of `NaN` or `inf` values in OHLCV columns.
- **Risk**: Bad data exports containing invalid price relationships or zero/negative prices will silently pass, causing calculation errors in indicators, backtests, or strategy fitness evaluations.

### 2.2 Non-Monotonic (Out-of-Order) Timestamps
- **Gaps**:
  - Both modules call `.sort_values("datetime")` silently.
  - If the source data contains out-of-order rows (e.g. overlapping data blocks or merged history files), it is sorted without warning or error.
- **Risk**: Overlapping segments or out-of-order exports might mask structural data duplication or sequence errors that shouldn't be silently patched.

### 2.3 Duplicate Timestamps
- **Gaps**:
  - Duplicate timestamps are rejected via raising `NormalizerError` / `ResamplerError`.
  - The error messages do not report which timestamps are duplicated, how many duplicates exist, or their index locations, making troubleshooting difficult.
- **Risk**: Devs/Users are left with a generic error and must manually search the database/CSV to identify duplicates.

### 2.4 Missing Timestamps & Gaps (Resampler)
- **Gaps**:
  - When `pd.Grouper` generates empty buckets (because no source data falls into that timeframe), they are dropped via `.dropna(subset=["open"])`.
  - This dropping is silent. If a dataset has large holes (e.g. missing hours or days during active sessions), there is no warning or notification.
- **Risk**: Downstream indicators (like SMA/EMA) calculate across time gaps as if they were adjacent bars, distorting trading signals without warning.

### 2.5 Constituent Count Gaps (Incomplete Target Bars)
- **Gaps**:
  - If a target group contains fewer than the expected number of constituent bars (e.g. only 3 1-minute bars are present for a 5-minute bar due to a gap), the resampler aggregates them silently.
  - `available_at` correctly points to the last available timestamp, but the bar has incomplete volume and potentially skewed range data.
- **Risk**: Indicator precomputing and signal logic run on partial bars, under-representing volume and high/low values.

### 2.6 Session Boundary Crossing & Timezone Naivety
- **Gaps**:
  - `pd.Grouper` groups purely by time offsets from the epoch. If target minutes cross session boundaries (e.g. daily session end is 16:15 and reopen is 18:00, or overnight gaps), bars can span across sessions.
  - Datetimes are parsed timezone-naive. Mixed timezone inputs or DST transitions (leading to 23-hour or 25-hour days) can trigger duplicate datetime failures or missing bar gaps.
- **Risk**: Resampled bars can blend data from two different trading days or session intervals.

---

## 3. Proposed Hardening Decisions

### 3.1 Normalizer Checks
1. **OHLC Logical Validation**:
   - Verify:
     - `high >= open`, `high >= close`, `high >= low`
     - `low <= open`, `low <= close`
     - `open > 0`, `high > 0`, `low > 0`, `close > 0`
     - `volume >= 0`
   - Raise `NormalizerError` if any of these conditions are violated, specifying the row index and the failed condition.
2. **Numeric / Missing / NaN / Inf Check**:
   - Convert or validate OHLCV columns as numeric before enforcing bounds.
   - Check if any OHLCV column contains `NaN`, `None`, or `inf`. Raise `NormalizerError` if found.
3. **Out-of-Order Warnings**:
   - Check if `df["datetime"].is_monotonic_increasing` is `False`.
   - If out-of-order, log a warning indicating that the source data was out-of-order and is being sorted.
4. **Duplicate Diagnostics**:
   - Improve duplicate error message to show up to the first 5 duplicated timestamps and the total duplicate count.

### 3.2 Resampler Warnings
1. **Constituent Bar Count Validation**:
   - Calculate the expected constituent count: `expected = target_minutes / source_minutes`.
   - Calculate the actual count of constituent bars in each resampled group: `actual = count(open)`.
   - Track incomplete groups where `actual < expected`.
   - If any incomplete groups are found:
     - Ignore the very first and very last resampled bars of the dataset (since they are naturally partial at the boundaries of the data file).
     - For other bars, log a warning or return metadata showing the count/timestamps of partial bars.
2. **Empty Group Warning**:
   - Compare the range of the resampled datetimes against the expected sequence (with target timeframe steps).
   - Log a warning if the dropped empty group percentage exceeds 10% of the dataset, or if there is a gap longer than `max(target_minutes * 10, 60)` minutes.

---

## 4. Smallest Safe Implementation Slice (Tasks 505-510)

To avoid breaking existing backtest and import flows, the hardening checks should raise strict errors only for clear-cut data corruption (OHLC violations, NaNs), while using warnings/logging for structural gaps (missing bars, out-of-order sorting).

### 4.1 Production Code Changes
- **`data_engine/normalizer.py`**:
  - Add `_validate_ohlcv_bounds(df)` to check logical relationships, positive values, non-negative volume, and absence of NaNs/infs. Raise `NormalizerError`.
  - Add numeric conversion or dtype validation for OHLCV fields before bounds validation.
  - Add monotonic check: check `df["datetime"].is_monotonic_increasing` and log a warning if `False`.
  - Add diagnostic print/log to `NormalizerError` on duplicate timestamps.
- **`data_engine/resampler.py`**:
  - Add OHLCV bounds validation that mirrors the normalizer rules without introducing UI coupling.
  - Add constituent count calculation: group aggregation also counts `open` values. Check if any non-boundary group has fewer than `target_minutes / source_minutes` elements, and log a warning with the count of partial bars.

### 4.2 Required Files to Modify
- [normalizer.py](file:///d:/Quant_Strategy_Lab/data_engine/normalizer.py)
- [resampler.py](file:///d:/Quant_Strategy_Lab/data_engine/resampler.py)

---

## 5. Verification & Test Plan

### 5.1 Automated Unit Tests (to be implemented in `tests/`)
1. **Normalizer Tests**:
   - `test_normalize_ohlc_consistency_violating_high_raises`: high < open or high < close raises `NormalizerError`.
   - `test_normalize_ohlc_consistency_violating_low_raises`: low > open or low > close raises `NormalizerError`.
   - `test_normalize_negative_price_raises`: any price <= 0 raises `NormalizerError`.
   - `test_normalize_negative_volume_raises`: volume < 0 raises `NormalizerError`.
   - `test_normalize_nan_values_raises`: any NaN in open, high, low, close, volume raises `NormalizerError`.
   - `test_normalize_non_monotonic_logs_warning`: inputting out-of-order data triggers a log warning.
2. **Resampler Tests**:
   - `test_resample_partial_bar_warning`: resampling a dataset with missing constituent bars inside the session (excluding boundary bars) logs a warning about incomplete target bars.
   - `test_resample_invalid_inputs_raises`: invalid prices/volumes in the input df trigger validations.

### 5.2 Manual Verification
- Run existing test suites `test_csv_importer.py` and `test_resampler.py` to ensure existing happy-paths are unaffected.
- Verify that standard `sample_ohlcv.csv` imports without errors.
