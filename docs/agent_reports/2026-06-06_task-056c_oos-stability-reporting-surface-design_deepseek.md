# Task 056C — OOS Stability Reporting Surface Design Only

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### Data Flow Trace

Traced the full path from `PipelineResult` through all consumer surfaces:

```
run_validation_pipeline()
  └─ PipelineResult (has oos_metrics + elimination_result)
       ├─ ValidationSummary widget (app/widgets/validation_summary.py)
       │    update_from_result() → reads everything EXCEPT oos_metrics
       │    └─ OOS card: MISSING
       ├─ Report generator (reports/generator.py)
       │    _format_markdown_validation() / _format_html_validation()
       │    └─ OOS metrics line: MISSING
       └─ Log panel (app/ui/main_window.py)
            └─ OOS summary line: MISSING
```

**Key finding**: `PipelineResult.oos_metrics` is computed (Task 056B) and stored in the dataclass, but **no consumer reads it**.

### Design Recommendations

1. **ValidationSummary widget**: Add an "OOS Metrics" card between Walk-Forward Matrix and Elimination cards; show OOS PnL, PF, trades, Max DD, Win Rate; show stability ratios when config thresholds are set.
2. **Report generator**: Add a single OOS line to both `_format_markdown_validation()` and `_format_html_validation()`; add optional stability-ratio sub-lines when thresholds are configured.
3. **Log panel**: Add one-line `f"OOS: PnL={...}, PF={...}"` OOS summary after the elimination log line.
4. **Engine/UI separation preserved**: all formatting is text presentation; no quant logic moves into widgets.

### Recommended Follow-up: Task 056D

Minimal implementation touching exactly 3 files:
- `app/widgets/validation_summary.py`
- `reports/generator.py`
- `app/ui/main_window.py`

Full scope documented in `docs/oos_stability_reporting_surface_design_056C.md`.

## Files Changed

| File | Change |
|---|---|
| `docs/oos_stability_reporting_surface_design_056C.md` | **Created** — design note with data flow trace and Task 056D scope |
| `docs/changelog.md` | Added Task 056C entry |
| `docs/task_board.md` | Task 056C → Done |
| `docs/agent_reports/2026-06-06_task-056c_oos-stability-reporting-surface-design_deepseek.md` | **Created** — this report |

## Verification

- **No production code changed** (design-only).
- **`git diff --check`**: ✅ passes.
- **Git status**: Dirty only with expected docs files.

## Known Issues

- None.

## Risks

- None (design-only).

## Suggested Next Task

**Task 056D — OOS Stability Report/UI Surface Implementation** as scoped in `docs/oos_stability_reporting_surface_design_056C.md`:

```python
# Files: 3 implementation files, all display-only
- app/widgets/validation_summary.py: Add OOS Metrics card
- reports/generator.py: Add OOS metrics + stability lines to both formatters
- app/ui/main_window.py: Add one-line OOS summary after elimination log
```

Do NOT touch engine, elimination rules, pipeline defaults, tests, or add dependencies.
