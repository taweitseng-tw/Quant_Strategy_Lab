# Batch 058B-Fix + 058C-Design — Widget MC Worst-case Defensive Fix and Normalizer Warning Triage

> Agent: DeepSeek V4 Pro
> Date: 2026-06-07

## Completed

### 058B-Fix — MC Worst-case Defensive

- `app/widgets/validation_summary.py`: `wc_pnl` checked with `isinstance` before `:,.0f` formatting. Falls back to `"?"` string.
- `tests/test_validation_summary.py`: 2 tests (missing `worst_case`, missing `total_pnl`).

### 058C-Design

`docs/normalizer_datetime_warning_triage_058C.md` — recommends test-level suppression (Option A).

## Files Changed

| File | Change |
|---|---|
| `app/widgets/validation_summary.py` | Defensive `wc_pnl` format |
| `tests/test_validation_summary.py` | 2 tests |
| `docs/normalizer_datetime_warning_triage_058C.md` | **Created** |
| `docs/changelog.md` | Batch entry |
| `docs/task_board.md` | Batch -> Done |

## Verification

```
widget tests: 23 passed
Full suite: 1103 passed, 1 warning
git diff --check -> passes
```
