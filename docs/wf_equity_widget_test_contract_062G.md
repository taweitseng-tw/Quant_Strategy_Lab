# WF Equity Widget Test Contract - Task 062G

> Design-only. No production code changed.

## 1. Target File

`app/widgets/validation_summary.py` - extend `ValidationSummary.update_from_result()` with a WF equity chart.

## 2. Input Data Shape

```python
walk_forward_summary = {
    "windows": [
        {
            "index": 0,
            "equity_curve": [100000.0, 100500.0, 101000.0],
            "passed": True,
        },
    ],
}
```

Data is present only when `PipelineConfig.wf_store_equity=True`. `ValidationSummary` receives this dict from `PipelineResult.walk_forward_summary`.

## 3. Chart Visibility Rules

| Condition | Chart visible? |
|---|---|
| `wf_store_equity=False` or no `windows` key | No |
| `windows` is `None` or empty list | No |
| All `equity_curve` values are `None` or length < 2 | No |
| At least one window has a valid `equity_curve` with length >= 2 | Yes; show available windows only |

## 4. Color / Label Expectations

| Window state | Line color | Label |
|---|---|---|
| `passed=True` | Green (`#4CAF50`) | `W{N} PASSED` |
| `passed=False` | Red (`#F44336`) | `W{N} FAILED` |

X-axis: bar index (`0` to `test_bars - 1`). Y-axis: equity value formatted as `:,.0f`.

## 5. Implementation Outline

```python
class _WFEquityChart(QWidget):
    """Simple PySide6 line chart for WF per-window equity curves."""

    def __init__(self, windows: list[dict], parent=None):
        super().__init__(parent)
        self._windows = windows
        self._setup_ui()

    def _setup_ui(self):
        # QGraphicsView + QGraphicsScene + polylines per window.
        # Green/red QPen based on window["passed"].
        # X/Y axis labels.
        pass
```

Insert into `ValidationSummary` after the existing WF equity text section:

```python
if equity_windows:
    self._add_section("WF Equity Summary", "\n".join(lines))
    chart = _WFEquityChart(equity_windows)
    self._layout.addWidget(chart)
```

## 6. Focused Tests For Future Implementation

| # | Test | File |
|---|---|---|
| 1 | Chart renders when equity data is present | `tests/test_validation_summary.py` |
| 2 | Chart is omitted when `windows` key is missing | `tests/test_validation_summary.py` |
| 3 | Chart is omitted when all `equity_curve` values are `None` | `tests/test_validation_summary.py` |
| 4 | Chart handles partial equity availability | `tests/test_validation_summary.py` |
| 5 | Single window with fewer than 2 points renders no chart | `tests/test_validation_summary.py` |
| 6 | Passed windows use green and failed windows use red | `tests/test_validation_summary.py` |
| 7 | Chart height is constrained to avoid layout expansion | `tests/test_validation_summary.py` |

## 7. Out Of Scope

- Report chart embedding in Markdown or HTML.
- Interactive chart features such as zoom, pan, or tooltips.
- Chart image export.
- New charting dependencies.

## 8. Next Two-Task Batch

Batch 062H-Impl + 062I-Design - WF Equity Chart Widget Implementation and Price-Noise UI Config Controls Design.

- 062H: Implement `_WFEquityChart` in `ValidationSummary`.
- 062I: Design-only price-noise pipeline config UI controls.

## 9. Metadata

- Author: DeepSeek V4
- Date: 2026-06-08
