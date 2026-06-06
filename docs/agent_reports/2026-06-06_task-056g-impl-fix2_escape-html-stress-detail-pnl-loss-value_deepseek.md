# Task 056G-Impl-Fix2 — Escape HTML Stress Detail PnL Loss Value

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### Fix (`reports/generator.py`)

One-line change: `pnl_loss={pnl_loss}` → `pnl_loss={html.escape(str(pnl_loss))}`.

Before: when `assumptions["pnl_loss_ratio"]` was not a float, the raw value was injected directly into HTML without escaping.

After: `pnl_loss` is always `html.escape(str(pnl_loss))` — safe for both float-formatted `"0.500"` and malicious `"<img src=x>"`.

### Test Strengthened

`test_html_stress_detail_values_escaped` now also injects `<img src=x>` as `pnl_loss_ratio` and asserts:
- Raw `<img src=x>` does NOT appear
- `&lt;img src=x&gt;` DOES appear

## Files Changed

| File | Change |
|---|---|
| `reports/generator.py` | Escaped `pnl_loss` in stress-detail div |
| `tests/test_report_export.py` | Added `<img src=x>` case to escaping test |
| `docs/changelog.md` | Task 056G-Impl-Fix2 entry |
| `docs/task_board.md` | 056G-Impl-Fix2 -> Done |

## Verification

```
report tests: 30 passed
combined widget + report: 41 passed
Full suite: 1012 passed, 1 warning
git diff --check -> passes
```

## Known Issues

- None.
