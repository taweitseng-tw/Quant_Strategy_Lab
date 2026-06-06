# Walk-Forward Per-Window Equity Persistence Design — Task 057B

> Design-only. No production code changed.

## 1. Current State

### What Exists

`validation_engine/walk_forward.py` produces per-window results:

```python
@dataclass
class WalkForwardWindow:
    index: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    train_bars: int
    test_bars: int
    metrics: dict                  # test-segment metrics
    passed: bool
    train_metrics: dict            # train-segment metrics (only when calc_wfe)
    wfe: float | None
```

`WalkForwardResult` aggregates: `window_count`, `pass_count`, `pass_rate`, `aggregate_metrics`, `stability_score`, `average_wfe`, `windows: list[WalkForwardWindow]`.

### What's Missing (PRD §12.5 Alpha)

Per-window equity curves are **not stored**. Each `WalkForwardWindow` has aggregate metrics but no time-series data. This prevents:

- Per-window drawdown visualization.
- Debugging why a specific window failed.
- Per-window equity curve charts in reports.

### Design Principle

Add an **optional** per-window equity curve to `WalkForwardWindow`, stored as a list of float equity values (or compressed dict). Keep it off by default to avoid memory overhead for users who don't need it.

## 2. Proposed Addition

### 2.1 WalkForwardWindow Enhancement

Add one optional field:

```python
@dataclass
class WalkForwardWindow:
    # ... existing fields ...
    equity_curve: list[float] | None = None  # NEW: cumulative equity per bar in test segment
```

### 2.2 Data Shape

`equity_curve` is a list of floats representing cumulative equity at each bar in the test segment:

```python
equity_curve = [100000.0, 100050.0, 100020.0, ...]  # length = test_bars
```

### 2.3 Memory Estimate

| Scenario | Bars per window | Windows | Total floats | Memory (~8 bytes/float) |
|---|---|---|---|---|
| Typical (train=500, test=200, step=200, n=10 windows) | 200 | 10 | 2,000 | ~16 KB |
| Large (train=100, test=50, step=25, n=40 windows) | 50 | 40 | 2,000 | ~16 KB |
| Worst (1-minute data, 1 year, small windows) | ~100 | ~500 | 50,000 | ~400 KB |

**Verdict**: Memory overhead is negligible for typical use. Even worst case is under 1 MB.

### 3. Backward Compatibility

Existing consumers of `WalkForwardWindow` access `metrics`, `passed`, `test_start`, etc. The new `equity_curve: list[float] | None = None` field:

- Defaults to `None` — existing code that doesn't check it is unaffected.
- Serialized to dict via `asdict()` when present — adds about 16 KB to pipeline result dict.
- Reports/display can check `if window.equity_curve: render_chart(...)` with zero cost when absent.

### 3.1 Serialization Impact

`_wf_to_dict()` in `validation_pipeline_service.py` currently serializes aggregate WF data. If per-window equity is needed in pipeline results, `WalkForwardResult.windows` must be serialized too (currently not). This is a separate concern — recommend serializing windows only when equity is enabled.

### 3.2 `WalkForwardWindow` dict conversion

The window dataclass uses `@dataclass` — `asdict()` works directly. Equity curve serializes as a list of floats in JSON:

```python
window_dict = asdict(window)
# {
#   "index": 0,
#   ...
#   "equity_curve": [100000.0, 100050.0, ...] | null
# }
```

## 4. Implementation Approach

### 4.1 Engine Change (WalkForwardWindow)

Minimal: add one field and populate it in `walk_forward()`:

```python
# In walk_forward(), after test backtest:
window = WalkForwardWindow(
    ...
    equity_curve=test_result.equity_curve["equity"].tolist()
        if store_equity else None,
)
```

### 4.2 Enable/Disable

New parameter on `walk_forward()`:

```python
def walk_forward(
    ...,
    store_equity: bool = False,  # NEW, default off
) -> WalkForwardResult:
```

And in `PipelineConfig`:

```python
wf_store_equity: bool = False  # default off
```

### 4.3 WalkForwardResult Serialization

Currently `_wf_to_dict()` only serializes aggregate fields. When `store_equity=True`, also serialize `windows`:

```python
def _wf_to_dict(wf) -> dict:
    result = { ... existing aggregate fields ... }
    if hasattr(wf, "windows") and wf.windows and wf.windows[0].equity_curve is not None:
        result["windows"] = [asdict(w) for w in wf.windows]
    return result
```

## 5. Report/Display Integration (Deferred)

Per-window equity curves enable:
- Per-window drawdown chart in HTML reports.
- "Worst window" identification in validation summary.
- Window-by-window pass/fail visualization.

These are separate display tasks, not part of this design.

## 6. Non-Persistence Note

This design adds **in-memory** equity curves. It does NOT add SQLite/Parquet persistence. Per-window equity is transient (lives in `PipelineResult`) and appears in reports. If persistence is needed later, `WalkForwardWindow.equity_curve` can be stored as a JSON blob in `walk_forward_results` table.

## 7. Test Plan

| # | Test | Verifies |
|---|---|---|
| 1 | `test_wf_equity_store_enabled` | `store_equity=True` -> windows have equity_curve |
| 2 | `test_wf_equity_store_disabled` | `store_equity=False` -> equity_curve is None |
| 3 | `test_wf_equity_length_matches_test_bars` | len(equity_curve) == test_bars |
| 4 | `test_wf_equity_serialization` | `asdict(window)` includes equity_curve (or None) |
| 5 | `test_wf_equity_backward_compatible` | Old code accessing `window.metrics` still works |
| 6 | `test_wf_equity_no_mutation` | Original equity DataFrame not mutated |
| 7 | `test_wf_equity_empty_trades` | No trades -> equity_curve pulled from backtest result |

## 8. Design Decisions

1. **Default off** — `store_equity=False`. Users who need per-window detail opt in.
2. **List of floats** — simple, JSON-serializable, no pandas dependency in schema.
3. **No persistence** — equity curves are transient. If needed later, they serialize trivially.
4. **No duplicate storage** — equity curve comes from the backtest result, which already computes it. No re-computation.
5. **One field, not a new class** — `WalkForwardWindow` gets `equity_curve`, not a separate equity container.

## 9. Non-Goals

- Not implementing per-window equity charts in reports (separate display task).
- Not adding SQLite/Parquet persistence for equity curves.
- Not changing WalkForwardMatrix.
- Not changing existing WF aggregate behavior.
- Not implementing per-window drawdown curves (equity is sufficient; drawdown derives from equity).

## 10. Triage metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Dependencies**: None (standalone)
- **Blocked by**: Nothing
