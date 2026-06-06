# Batch 057J-Impl + 057L-Design — WF Equity Summary Widget and Report Surface Design

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### 057J-Impl — WF Equity Summary Widget

- Added WF Equity Summary section after Walk-Forward card
- Shows per-window equity start/end/change% and PASSED/FAILED for up to 5 windows
- "... N more windows" suffix when >5
- Omits when equity data missing/empty

### 057L-Design

`docs/wf_equity_report_surface_design_057L.md` — markdown/HTML table design.

### Tests

4 new widget tests: shown when present, absent when no equity, absent when no windows key, capped at 5.

## Files Changed

| File | Change |
|---|---|
| `app/widgets/validation_summary.py` | WF Equity Summary section |
| `tests/test_validation_summary.py` | 4 tests |
| `docs/wf_equity_report_surface_design_057L.md` | **Created** |
| `docs/changelog.md` | Batch entry |
| `docs/task_board.md` | Batch -> Done |

## Verification

```
widget tests: 21 passed
Full suite: 1088 passed, 1 warning
git diff --check -> passes
```
