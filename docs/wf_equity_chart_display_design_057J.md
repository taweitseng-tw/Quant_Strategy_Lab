# WF Per-Window Equity Chart Display Design — Task 057J

> Design-only. No production code changed.

## 1. Current State

Per-window equity curves are stored in `walk_forward_summary["windows"][*]["equity_curve"]` as `list[float]` when `wf_store_equity=True` (Task 057B-Impl). No consumer reads or renders these curves yet.

## 2. Data Availability Rules

| Condition | `equity_curve` |
|---|---|
| `wf_store_equity=False` (default) | `None` for all windows |
| `wf_store_equity=True` | List of floats, length = `test_bars` |
| No trades in window | List of zeros or single value (from backtest) |

Display surfaces must check: `wf` dict exists → `windows` key exists → `equity_curve` is non-None for at least one window. If any condition fails, skip the chart section.

## 3. No-Dependency Rendering Approach

### 3.1 Widget — Text Summary Table

No charting library needed. Render a compact per-window equity summary table as text in the existing Walk-Forward card:

```
WF Equity Summary (when store_equity=True)
Window 0: equity 100,000 → 105,000 (+5.0%)  PASSED
Window 1: equity 100,000 → 98,500 (-1.5%)  FAILED
Window 2: equity 100,000 → 102,000 (+2.0%)  PASSED
```

Format: `<window index>: equity <first> → <last> (<pct>%)  <PASSED/FAILED>`

This avoids adding matplotlib/pyqtgraph dependencies for chart rendering and stays within the existing `_add_section()` pattern.

### 3.2 Markdown Report — Table

```markdown
- **WF Equity by Window**:
  | Window | Start Equity | End Equity | Change | Result |
  |---|---|---|---|---|
  | 0 | 100,000 | 105,000 | +5.0% | PASSED |
  | 1 | 100,000 | 98,500 | -1.5% | FAILED |
```

### 3.3 HTML Report — Table

```html
<p><b>WF Equity by Window</b></p>
<table>
<tr><th>Window</th><th>Start</th><th>End</th><th>Change</th><th>Result</th></tr>
<tr><td>0</td><td>100,000</td><td>105,000</td><td class="pnl-positive">+5.0%</td><td>PASSED</td></tr>
...
</table>
```

Reuses existing HTML table CSS classes (`pnl-positive`/`pnl-negative`).

## 4. Empty/Missing Behavior

| Condition | Widget | Markdown | HTML |
|---|---|---|---|
| `wf_store_equity=False` | No equity summary | No equity section | No equity section |
| `windows` not in dict | No equity summary | No equity section | No equity section |
| All `equity_curve is None` | No equity summary | No equity section | No equity section |
| Single window, no equity | Skip section | Skip section | Skip section |

## 5. Implementation Plan

**Recommendation**: Widget first, reports deferred to follow-up display task.

Widget is the simplest surface (text only, no HTML/markdown formatting), and users see it immediately on the Validate page.

### Implementation Surface (Task 057J-Impl)

| File | Change |
|---|---|
| `app/widgets/validation_summary.py` | WF Equity Summary sub-card after Walk-Forward card |
| `tests/test_validation_summary.py` | 2 tests (shown, absent) |

### Report surface (deferred)

| File | Change |
|---|---|
| `reports/generator.py` | Markdown table + HTML table |
| `tests/test_report_export.py` | Tests |

## 6. Test Plan

| # | Test | Verifies |
|---|---|---|
| 1 | `test_wf_equity_summary_shown` | Widget shows table when equity present |
| 2 | `test_wf_equity_summary_absent` | Widget omits when no equity data |
| 3 | `test_wf_equity_summary_percent_calc` | Change % is correct |

## 7. Non-Goals

- Not implementing charts (matplotlib/pyqtgraph).
- Not adding new dependencies.
- Not adding per-window drawdown curves.
- Not modifying walk-forward engine.
- Not implementing WF equity in reports (deferred).

## 8. Triage metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Dependencies**: 057B-Impl (equity storage) — Done
