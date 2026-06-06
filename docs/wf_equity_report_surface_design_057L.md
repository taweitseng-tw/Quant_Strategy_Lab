# WF Equity Report Surface Design — Task 057L

> Design-only. No production code changed.

## 1. Current State

Widget WF equity summary is implemented (Task 057J-Impl). Report surfaces (markdown/HTML) have no WF equity display.

## 2. Markdown Report Design

After WF line, add a compact table when equity data is present:

```markdown
- **WF Equity by Window**:
  | # | Start | End | Change | Result |
  |---|---|---|---|---|
  | 0 | 100,000 | 105,000 | +5.0% | PASSED |
  | 1 | 100,000 | 98,500 | -1.5% | FAILED |
  | ... 3 more windows ... | — | — | — | — |
```

### Rules

| Rule | Detail |
|---|---|
| Max rows | 5 windows shown; "... N more windows ..." row if > 5 |
| Missing equity | Window without equity_curve → omitted from table |
| All missing | No table rendered |
| windows key absent | No table rendered |

## 3. HTML Report Design

Reuses existing table CSS classes:

```html
<p><b>WF Equity by Window</b></p>
<table><thead><tr><th>#</th><th>Start</th><th>End</th><th>Change</th><th>Result</th></tr></thead><tbody>
<tr><td>0</td><td>100,000</td><td>105,000</td><td class="pnl-positive">+5.0%</td><td>PASSED</td></tr>
<tr><td>1</td><td>100,000</td><td>98,500</td><td class="pnl-negative">-1.5%</td><td>FAILED</td></tr>
<tr><td colspan="5">... 3 more windows ...</td></tr>
</tbody></table>
```

### Rules

Same as markdown. All values are numeric (no HTML escaping needed). Change % uses existing `pnl-positive`/`pnl-negative` CSS classes.

## 4. Implementation Surface

| File | Change |
|---|---|
| `reports/generator.py` | Markdown table + HTML table |
| `tests/test_report_export.py` | 2 tests (shown + absent) |

## 5. Non-Goals

- Not implemented in this design-only task.
- No charts.
- No new dependencies.

## 6. Triage metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Dependencies**: 057J-Impl (widget equity summary) — Done
