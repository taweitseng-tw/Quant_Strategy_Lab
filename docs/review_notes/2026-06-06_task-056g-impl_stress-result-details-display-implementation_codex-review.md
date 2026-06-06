# Codex Review - Task 056G-Impl Stress Result Details Display Implementation

## Verdict

Needs fix before acceptance.

## Score

8.4 / 10

## Review Summary

The implementation is mostly aligned with the approved 056G design: it adds compact detail sub-lines for `remove_best_n_trades` in the validation widget, Markdown report, and HTML report while leaving basic stress tests compact. Focused tests pass and the implementation does not touch engine or pipeline behavior.

However, the task explicitly required HTML output to escape dynamic warning/detail values. Warnings are escaped, but the detail values inserted into `<div class="stress-detail">...</div>` are not escaped.

## Blocking Finding

### P1 - HTML stress detail values are not escaped

File: `reports/generator.py`

The HTML formatter directly interpolates `removed`, `total`, `n_val`, `pnl_loss`, and `threshold` into the stress-detail div. A malformed validation dict can render raw HTML from detail fields such as `assumptions["n"]` or `threshold["max_pnl_loss"]`.

Codex probe:

```text
raw_script= True
raw_b= True
<div class="stress-detail">Removed: 1 of 3 trades (n=<script>x</script>, pnl_loss=0.500, threshold=<b>bad</b>)</div>
```

This violates acceptance criterion 3 from Task 056G-Impl.

## Verified

```powershell
.venv\Scripts\python.exe -m pytest tests/test_validation_summary.py tests/test_report_export.py -v
git diff --check
```

Results:

- Focused tests: 40 passed.
- `git diff --check`: passed.
- Manual HTML escaping probe: failed for detail values.

## Required Fix

Escape every dynamic value inserted into the HTML `stress-detail` line and add a regression test that proves raw `<script>` and `<b>` detail values do not appear in HTML output.
