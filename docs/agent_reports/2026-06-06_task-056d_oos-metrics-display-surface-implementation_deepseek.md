# Task 056D — OOS Metrics Display Surface Implementation

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### 1. ValidationSummary Widget (`app/widgets/validation_summary.py`)

Added "OOS Metrics" card between Walk-Forward Matrix and Elimination. Reads `result.oos_metrics` dict only:
- When present: displays PnL, PF, Trades, Max DD, Win Rate
- When absent: displays "No OOS data."
- No ratio computation in widget code.

### 2. Report Generator (`reports/generator.py`)

Added one OOS metrics line after the Baseline line in both formatters:

- `_format_markdown_validation()`: `"- **OOS**: PnL=..., PF=..., Trades=..., Max DD=..."`
- `_format_html_validation()`: `<p><b>OOS:</b> PnL=..., PF=..., Trades=..., Max DD=...</p>`
- Both silently skip the line when `oos_metrics` is absent.
- No ratio computation in report code.

### 3. Log Panel (`app/ui/main_window.py`)

Added one-line OOS summary after the elimination log line:
```python
f"OOS: PnL={...}, PF={...}, Trades={...}"
```
Only printed when `result.oos_metrics` is present.

### 4. Tests

| File | Tests |
|---|---|
| `tests/test_validation_summary.py` | `test_oos_metrics_card_displayed` — OOS card appears with correct values; `test_oos_metrics_missing_shows_placeholder` — shows "No OOS data." |
| `tests/test_report_export.py` | `test_markdown_includes_oos_line_when_present`; `test_markdown_omits_oos_when_absent`; `test_html_includes_oos_line_when_present`; `test_html_omits_oos_when_absent` |

## Files Changed

| File | Change |
|---|---|
| `app/widgets/validation_summary.py` | Added OOS Metrics card |
| `reports/generator.py` | Added OOS line to markdown + HTML formatters |
| `app/ui/main_window.py` | Added OOS summary log line |
| `tests/test_validation_summary.py` | 2 new tests |
| `tests/test_report_export.py` | 4 new tests |
| `docs/changelog.md` | Task 056D entry |
| `docs/task_board.md` | 056D -> Done |
| `docs/agent_reports/2026-06-06_task-056d_oos-metrics-display-surface-implementation_deepseek.md` | **Created** — this report |

## Verification

```
.venv\Scripts\python.exe -m pytest tests/test_validation_summary.py tests/test_report_export.py tests/test_active_dataset.py -v
-> 46 passed

.venv\Scripts\python.exe -m pytest -q
-> 992 passed, 1 warning

git diff --check -> passes
```

Acceptance criteria all met:
1. ✅ ValidationSummary displays OOS metrics when present.
2. ✅ ValidationSummary displays "No OOS data." when absent.
3. ✅ Markdown reports include OOS line when present.
4. ✅ HTML reports include OOS paragraph when present.
5. ✅ Markdown/HTML reports omit OOS line when absent.
6. ✅ Log panel prints OOS summary only when present.
7. ✅ No ratio computation in UI/report/log code.
8. ✅ Focused tests + full suite pass.
9. ✅ `git diff --check` passes.

## Known Issues

- None.

## Risks

- None. All display is purely additive on pre-computed structured data.

## Suggested Next Task

The OOS stability data path is now complete end-to-end:
- Engine computes OOS metrics + stability rules (Task 056B/B-Fix)
- UI/report/log surfaces display OOS metrics (Task 056D)

Remaining items from the 056A triage that could be picked up:
- **Remove Best N Trades stress test** (Gap B)
- **IS Baseline Quality Gate** (Gap D)
- **Engine-layer `oos_stability` payload** to enable ratio display in UI/report later
