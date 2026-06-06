# Task 056G-Impl — Stress Result Details Display Implementation

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### Widget (`app/widgets/validation_summary.py`)

Extended the stress rendering loop: after the main `test_name: ✓/✗  PnL Δ=X%` line, `remove_best_n_trades` now gets compact inline sub-lines showing:

```
remove_best_n_trades: ✗  PnL Δ=-83.3%
  → Removed: 2 of 4 trades (n=2, pnl_loss=0.833, threshold=0.30)
  → ⚠ Insufficient trades for remove-best-n stress test (trades=2, n=5)
```

Other stress tests (commission, slippage, delay, perturbation) unchanged.

### Markdown Report (`reports/generator.py`)

Added matching detail sub-lines in `_format_markdown_validation()`:
```markdown
- **Stress (remove_best_n_trades)**: FAIL PnL d=-83.3%
  - Removed: 2 of 4 trades (n=2, pnl_loss=0.833, threshold=0.30)
  - WARNING: Insufficient trades for remove-best-n stress test.
```

### HTML Report (`reports/generator.py`)

Added matching sub-lines in `_format_html_validation()` with `html.escape()` for warnings:
```html
<p><b>Stress (remove_best_n_trades):</b> PnL d=-83.3%</p>
<div class="stress-detail">Removed: 2 of 4 trades (n=2, pnl_loss=0.833, threshold=0.30)</div>
<div class="warning-item">⚠ Insecure &lt;script&gt; test.</div>
```

### Tests

| File | Tests |
|---|---|
| `test_validation_summary.py` | `test_stress_remove_best_n_trades_detail_sub_lines`, `test_stress_no_sub_lines_for_basic_tests` |
| `test_report_export.py` | `test_markdown_includes_remove_best_n_detail_lines`, `test_html_includes_remove_best_n_detail_lines`, `test_markdown_no_detail_lines_for_basic_stress` |

## Files Changed

| File | Change |
|---|---|
| `app/widgets/validation_summary.py` | Extended stress loop with remove_best_n sub-lines |
| `reports/generator.py` | Extended markdown + HTML stress formatters with sub-lines |
| `tests/test_validation_summary.py` | 2 new tests |
| `tests/test_report_export.py` | 3 new tests |
| `docs/changelog.md` | Task 056G-Impl entry |
| `docs/task_board.md` | 056G-Impl -> Done |

## Verification

```
.venv\Scripts\python.exe -m pytest tests/test_validation_summary.py tests/test_report_export.py -v
-> 40 passed

.venv\Scripts\python.exe -m pytest -q
-> 1011 passed, 1 warning

git diff --check -> passes
```

Acceptance criteria:
1. ✅ Widget shows remove-best-N detail sub-lines.
2. ✅ Markdown shows matching sub-lines.
3. ✅ HTML shows matching sub-lines with escaped text.
4. ✅ `n`, `removed_count`, `surviving_count`, `pnl_loss_ratio`, threshold visible.
5. ✅ Warnings visible when present.
6. ✅ Basic stress tests remain compact.
7. ✅ Missing assumptions/warnings doesn't crash.
8. ✅ Focused tests pass.
9. ✅ Full suite passes.
10. ✅ `git diff --check` passes.

## Known Issues

- None.

## Risks

- None. Display-only changes, no engine/pipeline/layout modifications.
