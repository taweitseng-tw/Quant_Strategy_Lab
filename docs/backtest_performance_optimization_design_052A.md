# Task 052A - Backtest Performance Optimization Design

## 1. Overview
The current event-driven backtest engine (`backtest_engine/runner.py`) uses a highly deterministic, conservative bar-by-bar evaluation model. While correct and robust (preventing future leaks and ensuring next-bar-open execution), this approach introduces significant performance overhead, particularly when generating thousands of strategies during Genetic Algorithm (GA) or Genetic Programming (GP) searches.

## 2. Identified Bottlenecks

1. **Row-by-Row Pandas Iteration**:
   - `runner.py` iterates via `for i in range(n):` and fetches row data using `bar = data.iloc[i]` and `df.at[i, col]`. Pandas row-by-row iteration is notoriously slow.
2. **Per-Bar Condition Evaluation**:
   - Inside `strategy_engine/evaluator.py`, conditions are parsed strings (`op == ">"`, `ind == "SMA"`) evaluated freshly at every single bar.
3. **Redundant Indicator Precomputation**:
   - `_precompute_indicators` is called per-strategy. During GA/GP, if 50 strategies use `SMA(20)`, the engine might redundantly compute or check it per backtest, instead of caching the column on a master dataset for the entire generation.

## 3. Profiling Protocol
Before setting any performance targets or making changes, Task 052B must establish concrete baselines.

### 3.1. Small Smoke Baseline
For rapid sanity checking during development, we will use an existing test.
- **Command**:
  ```bash
  python -m cProfile -s cumtime -o profile_smoke.prof -m pytest tests/test_ga_service.py::test_ga_search_returns_structured_result -q
  ```
- **Note**: This runs a tiny DataFrame (150 bars) with a tiny population. It is strictly a smoke test to ensure the profiler and engine are working, **not** the target for performance claims.

### 3.2. Large-Load Baseline (First step of 052B)
To simulate a realistic load, 052B **must first create a dedicated profiling script** (e.g., `tests/profile_large_ga.py`) with the following strict parameters:
- **Dataset**: A standard test dataset spanning at least 5,000 bars.
- **Strategy Count**: GA search configured for 500 total strategy evaluations (e.g., pop=100, gen=5).
- **Execution**: Headless (no PySide6 imports or GUI).
- **Seed**: Hardcoded deterministic seed.
- **Output**: Output profile data explicitly saved to a reproducible path (e.g., `docs/perf_baselines/large_load_baseline.prof`).

### 3.3. Tools and Metrics
We will rely strictly on the built-in `cProfile` module. **Note: `line_profiler` is strictly optional and must not be added to the project's dependencies without explicit approval.**

Optimization claims must compare **before/after** metrics using the large-load baseline script:
- **Total Execution Time**: Real wall-clock time for the headless search.
- **Cumulative Time (cumtime)**: Time spent inside `run_backtest`, `evaluate_block`, and `_compute_base_indicator`.

*Goal: We will measure the large-load baseline first before setting an explicit numeric improvement target.*

## 4. Implementation Strategy (Phase-by-Phase)
Optimizations must be split into strict, isolatable phases to contain risk.

### Phase 1: Local Runner Array Extraction (Safe)
- **Concept**: Before entering the `for i in range(n):` loop in `runner.py`, extract the necessary Pandas columns into flat Numpy arrays or use `df.itertuples()`. Accessing array elements `[i]` is magnitudes faster than `df.iloc[i]`.
- **Scope**: Modifies `runner.py` local data access only.

### Phase 2: Pre-parsed Condition Accessors (Safe)
- **Concept**: Instead of doing string matching (`if ind == "SMA":`) at every bar, parse the Strategy's blocks *once* before the loop, returning a list of fast closure functions or direct array references.
- **Scope**: Modifies `evaluator.py` internal logic.

### Phase 3: Population-Level Indicator Cache (Moderate)
- **Concept**: Pre-scan the population's required indicators (e.g., in `ga_fitness.py` or `ga.py`) and precompute them on a master dataset *before* running individual backtests.
- **Scope**: Modifies the search engines (`ga.py` only). GP cache integration is out of scope.
- **Phase 3A Design (Hardened)**:
  - **Bottleneck**: `run_backtest` clones the base DataFrame and computes indicators from scratch for every single strategy evaluation, repeating expensive work like `SMA(20)` or `resample("5min")` up to 500 times per GA generation.
  - **Scope Limitation**: Phase 3B implementation is **GA-only first** (integrated into `ga_fitness.py`). GP cache integration remains explicitly deferred to a later separate task.
  - **Cache Lifecycle**:
    - The cache must be created per GA search / population evaluation context. It must **not** be global.
    - The cache must **not** survive across datasets or different GA runs.
    - The cache must **not** mutate Strategy objects.
    - The cache must **not** mutate ranked_data or previous result objects.
  - **Dataset Fingerprint Rule**:
    - `len`, `start_time`, and `end_time` alone are insufficient.
    - The fingerprint must include a deterministic hash of the dataset's `datetime`, `open`, `high`, `low`, `close`, `volume` shape, and boundary samples (e.g., first 5 and last 5 rows), or an explicit `dataset_id` if available.
    - If fingerprint validation fails upon cache access, the cache must **fail safe** by bypassing the cache and falling back to recomputation.
  - **Strict Cache Keys**:
    - Must specify: indicator type, all indicator params (sorted), timeframe, base vs MTF, source dataframe fingerprint, and expected output column names/dtypes.
  - By requiring an explicit fallback when cache is absent or fingerprint mismatches, it reliably prevents accidental cross-contamination. This is explicitly defined as: *The cache must store the final base-aligned Series (post `merge_asof(direction="backward")` on `available_at`). A dedicated test must prove that accessing `cached_mtf_array[i]` returns the exact same value as `baseline_mtf_array[i]` without shifting future HTF close prices backward.*
  - **Phase 3B Concrete Test Plan**:
    1. **Equivalence Test**: Cache disabled vs. enabled produces byte-for-byte identical trades, equity curve, drawdown, and metrics on a deterministic strategy.
    2. **MTF Equivalence Test**: MTF cache disabled vs. enabled produces identical base-aligned outputs.
    3. **Fingerprint Rejection Test**: Cache rejects or bypasses reuse when explicitly passed a DataFrame with a different fingerprint (e.g., altered prices or timestamps).
    4. **Hit-Rate Test**: Repeated indicators within a mock population successfully hit the cache without triggering `_compute_base_indicator` more than once.
    5. **Backward Compatibility Test**: `run_backtest` maintains identical behavior when `indicator_cache=None`.
    6. **End-to-End GA Test**: GA search `best_score` remains identical before and after cache integration for a fixed deterministic seed.
  - **Phase 3B Profiling Plan**:
    1. Preserve previous baseline files (do not delete or overwrite them).
    2. Write new output to `docs/perf_baselines/post_phase3_baseline.prof`.
    3. Compare wall-clock time, `run_backtest` cumulative time, `_precompute_indicators` cumulative time, and total indicator compute counts against `post_phase2_baseline.prof`.
    4. Do not make performance claims until empirically measured.

### Phase 4: Vectorized Signal Masks (High Risk - Deferred)
- **Concept**: Use vectorized boolean operations (`long_entry_signals = df['close'] > df['sma_20']`) to evaluate conditions for the entire dataset at once.
- **Scope**: Fundamentally alters `evaluate_block`.
- **Status**: Deferred. Remains explicitly deferred unless Phases 1-3 prove insufficient, due to the high risk of breaking event-driven execution models.

## 5. Correctness Invariants (052B Acceptance Criteria)
For every optimization phase, the outputs **must exactly match** the baseline behavior for any given deterministic seed:

1. **Trades List**: Identical entry/exit indices, timestamps, directions, fill prices, and PnL.
2. **Equity Curve**: Identical values at every bar.
3. **Drawdown Curve**: Identical values at every bar.
4. **Metrics**: Identical summary metrics (Profit Factor, Max Drawdown, etc.).
5. **Assumptions and Warnings**: Exact preservation of configuration metadata and edge-case warnings (e.g., unexecuted last-bar signals).

## 6. MTF Safety Constraints
Multi-Timeframe integration must strictly preserve the "no-future-leak" boundaries established in Task 049/050:
1. **`available_at` Semantics**: HTF indicators must only use data available at or before the bar being evaluated.
2. **`merge_asof` Constraint**: Any optimized join or array alignment must strictly emulate `pd.merge_asof(direction="backward")` using the base `datetime` against the HTF `available_at` timestamp.
3. **Incomplete HTF Candles**: The dropping of the incomplete final HTF candle (`_drop_incomplete_final_htf_group`) must remain verified by regression tests.
4. **Boundary Integrity**: Accessing `array[i]` must never indirectly fetch an HTF value that wasn't finalized prior to the open of bar `i`.
