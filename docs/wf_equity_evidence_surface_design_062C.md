# WF Equity Evidence Surface Design - Task 062C

> Design-only. No production code changed.

## 1. Purpose

Define how walk-forward per-window equity curves should be surfaced in the UI
and reports, giving visual evidence of strategy stability across OOS windows.

## 2. Required Data Shape

Expected source:

```python
walk_forward_summary["windows"][*]["equity_curve"]  # list[float] | None
walk_forward_summary["windows"][*]["passed"]        # bool
walk_forward_summary["windows"][*]["index"]         # int
```

The equity curve length should match the window test bars when
`PipelineConfig.wf_store_equity=True`.

## 3. UI Widget Expectations

| Aspect | Design |
|---|---|
| Location | After the existing WF equity summary/table in `ValidationSummary` |
| Chart type | Line chart using existing PySide6/project charting infrastructure only |
| Series | One line per window, visually distinguished by pass/fail |
| X-axis | Test-bar index within the WF window |
| Y-axis | Equity value with compact currency-style formatting |
| Tooltip | `Window N - PASSED/FAILED - Start: X, End: Y, Change: +/-Z%` |

## 4. Empty and Failure States

| Condition | Behavior |
|---|---|
| `wf_store_equity=False` | No chart section rendered |
| `windows` missing | No chart section rendered |
| All equity curves `None` or empty | No chart section rendered |
| Some windows have equity, some do not | Render available windows only; skip missing |
| Equity curve length less than 2 | Render a point marker or omit that window without crashing |

## 5. Report Markdown Expectations

After the WF equity table, include a compact evidence table:

```markdown
### WF Equity by Window

| Window | Start | End | Change | Result |
|---|---:|---:|---:|---|
| 0 | 100000 | 105000 | +5.0% | PASSED |
```

If no equity data exists, omit the section and do not emit a misleading
placeholder.

## 6. Report HTML Expectations

When chart rendering is available, HTML may reference a generated PNG:

```html
<p><b>WF Equity by Window</b></p>
<table>...</table>
<p><img src="wf_equity_chart.png" alt="WF Equity Chart" width="800" height="400"></p>
```

PNG generation must use existing project dependencies. PDF embedding is optional
future polish and must not be required for this milestone.

## 7. Focused Tests (Future)

| # | Test | Scope |
|---|---|---|
| 1 | Widget renders WF equity chart when equity data is present | UI happy path |
| 2 | Widget omits chart when `wf_store_equity=False` | Empty state |
| 3 | Widget handles partial equity data | Graceful degradation |
| 4 | Markdown report includes WF equity evidence table when data is present | Report happy path |
| 5 | HTML report includes chart reference only when a chart image exists | Report happy path |
| 6 | Single-point equity curve does not crash rendering | Edge case |
| 7 | PDF-specific expectations are omitted unless PNG export already exists | Scope guard |

## 8. Metadata

- Author: DeepSeek V4, amended by Codex review
- Date: 2026-06-08
