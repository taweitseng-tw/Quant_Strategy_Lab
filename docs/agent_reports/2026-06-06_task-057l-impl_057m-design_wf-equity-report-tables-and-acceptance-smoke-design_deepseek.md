# Batch 057L-Impl + 057M-Design — WF Equity Report Tables and 057 Acceptance Smoke Design

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### 057L-Impl — Report Tables

- Markdown: `| # | Start | End | Change | Result |` table after WF section
- HTML: `<table>` with `pnl-positive`/`pnl-negative` CSS classes
- Both capped at 5 windows with "... more windows" overflow row
- 5 new tests

### 057M-Design

`docs/validation_expansion_acceptance_smoke_design_057M.md` — 8 acceptance tests for the full 057 chain.

## Files Changed

| File | Change |
|---|---|
| `reports/generator.py` | Markdown + HTML WF equity tables |
| `tests/test_report_export.py` | 5 tests |
| `docs/validation_expansion_acceptance_smoke_design_057M.md` | **Created** |
| `docs/changelog.md` | Batch entry |
| `docs/task_board.md` | Batch -> Done |

## Verification

```
report tests: 45 passed
Full suite: 1093 passed, 1 warning
git diff --check -> passes
```
