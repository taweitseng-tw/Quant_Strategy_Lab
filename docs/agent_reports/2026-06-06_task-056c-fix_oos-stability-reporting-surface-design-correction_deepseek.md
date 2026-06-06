# Task 056C-Fix — OOS Stability Reporting Surface Design Correction

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### P1 Fix: Stability Ratios Removed from UI/Report Display Scope

**Problem**: Original Task 056C design proposed displaying PF degradation, drawdown ratio, and avg-trade degradation as raw numeric values in the ValidationSummary widget and report generator. These ratios are computed inside `validation_engine/elimination._compute_oos_stability()` but are NOT exposed as a structured `PipelineResult` field. Implementing the original design would force UI/report code to recompute ratios from `baseline_metrics` and `oos_metrics`, violating engine/UI separation.

**Fix**: Narrowed Task 056D scope to display only existing structured data:

- **Widget**: OOS Metrics card shows raw `oos_metrics` values only (PnL, PF, Trades, Max DD, Win Rate). No ratio computation.
- **Report**: Single OOS metrics line in both markdown and HTML formatters.
- **Log panel**: One-line OOS summary.
- **Deferred**: Stability ratio display until a structured `oos_stability` engine-layer payload exists with tests.

### Additional Fixes

| Issue | What was changed |
|---|---|
| Garbled symbols in data flow diagram | Replaced Unicode box-drawing characters (`\u2500`, `\u2193`, etc.) with plain ASCII brackets and arrows |
| No acceptance criteria for Task 056D | Added 7 concrete acceptance criteria covering widget, markdown, HTML, log, empty-data, test compatibility, git diff |

## Design Correction Summary

| Before (Task 056C) | After (Task 056C-Fix) |
|---|---|
| Widget shows raw PF/degradation, DD/ratio, avg trade/degradation with pass/fail marks | Widget shows OOS PnL, PF, Trades, Max DD, Win Rate only |
| Report includes IS/OOS Stability sub-section with ratio values | Report includes one OOS metrics line only |
| Risk: UI recomputes `_compute_oos_stability()` logic | Risk: zero — all values from `PipelineResult.oos_metrics` dict |
| Widget reads `elimination_result` to derive stability status | Widget reads `oos_metrics` directly; stability status already visible in existing Elimination card |

## Files Changed

| File | Change |
|---|---|
| `docs/oos_stability_reporting_surface_design_056C.md` | **Revised** — removed ratio display, fixed ASCII, added acceptance criteria |
| `docs/changelog.md` | Added Task 056C-Fix entry |
| `docs/task_board.md` | Task 056C-Fix -> Done |
| `docs/agent_reports/2026-06-06_task-056c-fix_oos-stability-reporting-surface-design-correction_deepseek.md` | **Created** — this report |

## Verification

- **No production code changed** (design-only correction).
- **`git diff --check`**: passes.
- **Engine/UI separation preserved**: corrected design displays only pre-computed structured data.
- **Git status**: Dirty only with expected docs files.

## Known Issues

- None.

## Risks

- None (design-only task).

## Suggested Next Task

**Task 056D — OOS Metrics Display Surface Implementation** with corrected scope:

```
app/widgets/validation_summary.py: Add OOS Metrics card (raw oos_metrics only)
reports/generator.py: Add OOS metrics line to both markdown + HTML formatters
app/ui/main_window.py: Add one-line OOS summary after elimination log
```

Full corrected scope and 7 acceptance criteria in `docs/oos_stability_reporting_surface_design_056C.md`.
