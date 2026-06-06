# Task 056G-Impl-Fix — HTML Stress Detail Value Escaping

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### HTML Escaping Fix (`reports/generator.py`)

Before:
```python
f'<div class="stress-detail">Removed: {removed} of {total} trades '
f'(n={n_val}, pnl_loss={pnl_loss}, threshold={threshold})</div>'
```

After:
```python
f'<div class="stress-detail">Removed: {html.escape(str(removed))} '
f'of {html.escape(str(total))} trades '
f'(n={html.escape(str(n_val))}, pnl_loss={pnl_loss}, '
f'threshold={html.escape(str(threshold))})</div>'
```

Four dynamic values (`removed`, `total`, `n_val`, `threshold`) are now HTML-escaped. `pnl_loss` is always formatted as a float via `{pnl_loss:.3f}` so it's already safe.

### Regression Test

`test_html_stress_detail_values_escaped`: injects `<script>x</script>` as `n` and `<b>bad</b>` as `threshold`, then asserts:
- Raw `<script>x</script>` does NOT appear
- Raw `<b>bad</b>` does NOT appear
- `&lt;script&gt;x&lt;/script&gt;` DOES appear
- `&lt;b&gt;bad&lt;/b&gt;` DOES appear

## Files Changed

| File | Change |
|---|---|
| `reports/generator.py` | Escaped 4 dynamic values in `stress-detail` div |
| `tests/test_report_export.py` | Added escaping regression test |
| `docs/changelog.md` | Task 056G-Impl-Fix entry |
| `docs/task_board.md` | 056G-Impl-Fix -> Done |

## Verification

```
.venv\Scripts\python.exe -m pytest tests/test_report_export.py -v
-> 30 passed

.venv\Scripts\python.exe -m pytest tests/test_validation_summary.py tests/test_report_export.py -v
-> 41 passed

.venv\Scripts\python.exe -m pytest -q
-> 1012 passed, 1 warning

git diff --check -> passes
```

Acceptance criteria:
1. ✅ HTML stress-detail values escaped.
2. ✅ Raw `<script>` and `<b>` cannot appear.
3. ✅ Escaped `&lt;script&gt;` and `&lt;b&gt;` do appear.
4. ✅ Existing warning escaping still works.
5. ✅ Normal numeric output remains readable.
6. ✅ Markdown unaffected (no HTML escaping needed).
7. ✅ Focused tests pass.
8. ✅ Full suite passes.
9. ✅ `git diff --check` passes.

## Known Issues

- None.

## Risks

- None. Defensive HTML escaping only; no behavior change for normal numeric inputs.
