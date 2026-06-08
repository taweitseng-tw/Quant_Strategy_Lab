# WF Equity Widget Implementation Contract — Task 062E

> Design-only. No production code changed.

## 1. Target File

`app/widgets/validation_summary.py` — extend the existing WF Equity Summary text section with a line chart.

## 2. Required Data Shape

Walk-forward per-window equity data is stored in the validation result dict:

```python
walk_forward_summary["windows"][*]["equity_curve"]  # list[float]
walk_forward_summary["windows"][*]["passed"]        # bool
walk_forward_summary["windows"][*]["index"]         # int
```

Present only when `PipelineConfig.wf_store_equity=True` and the windows were serialized.

## 3. Rendering Strategy (Existing Dependencies Only)

No new charting dependency. Use PySide6's built-in `QGraphicsView` + `QGraphicsScene` + `QPen`/`QBrush` for a simple line chart.

| Component | PySide6 Class | Purpose |
|---|---|---|
| Canvas | `QGraphicsView` | Scrollable chart area |
| Scene | `QGraphicsScene` | Contains line items |
| Lines | `QGraphicsLineItem` or `QPainterPath` | Per-window equity curve |
| Axes | `QGraphicsSimpleTextItem` | Min/max labels |

### Alternative: Use existing `CandlestickChart` pattern

The project already has `CandlestickChart` under `app/widgets/`. If a generic line-chart widget exists or can be added, reuse it. Otherwise, inline the rendering in `ValidationSummary`.

## 4. Implementation Steps

| Step | Action |
|---|---|
| 1 | Add `_WFEquityChart` inner class (or standalone widget) in `validation_summary.py` |
| 2 | Widget accepts `list[dict]` — each dict with `equity_curve`, `passed`, `index` |
| 3 | Render each window as a coloured polyline: green for PASSED, red for FAILED |
| 4 | Add x-axis labels (bar 0 … N-1), y-axis labels (equity range) |
| 5 | Insert the chart widget after the WF Equity Summary text section |
| 6 | Add `height=200px` constraint to avoid layout explosion |

## 5. Empty / Failure States

| Condition | Behaviour |
|---|---|
| `wf_store_equity=False` | No chart, no section |
| `windows` key missing | No chart, no section |
| All `equity_curve` are `None` or empty | No chart, no section |
| Some windows have equity, some don't | Render available curves; skip missing |
| Single window with < 2 equity points | No chart (no line to draw) |

## 6. Report Serialization

Report rendering (markdown/HTML) is out of scope for this widget task. The existing WF equity table covers report display.

## 7. Tests (Future)

| # | Test | Scope |
|---|---|---|
| 1 | Chart widget renders when equity data present | Happy path |
| 2 | Chart omitted when `wf_store_equity=False` | Empty state |
| 3 | Chart handles some windows missing equity curves | Graceful |
| 4 | Chart omitted when all equity curves are `None` | Corner |
| 5 | Single-window with < 2 points renders no chart | Edge case |

## 8. Out of Scope

- Report (markdown/HTML) chart embedding.
- New charting dependencies (matplotlib, plotly, pyqtgraph).
- Interactive chart features (zoom, pan).
- Export chart as image.

## 9. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-08
