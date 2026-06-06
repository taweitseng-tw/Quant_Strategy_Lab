# Codex Review - Task 056G-Impl-Fix HTML Stress Detail Value Escaping

## Verdict

Needs fix before acceptance.

## Score

8.6 / 10

## Review Summary

The fix correctly escapes several HTML stress-detail values and adds a regression test for malicious `n` and `threshold` values. Focused report tests pass.

However, the task explicitly required escaping `pnl_loss` as well. The current implementation formats `pnl_loss` when it is a float, but leaves non-float values unescaped. A malformed validation dict can still inject raw HTML through `assumptions["pnl_loss_ratio"]`.

## Blocking Finding

### P1 - `pnl_loss` remains unescaped for non-float values

File: `reports/generator.py`

Codex probe:

```text
raw_script= False
raw_b= False
raw_img= True
escaped_img= False
<div class="stress-detail">Removed: 1 of 3 trades (n=&lt;script&gt;x&lt;/script&gt;, pnl_loss=<img src=x>, threshold=&lt;b&gt;bad&lt;/b&gt;)</div>
```

This violates the Task 056G-Impl-Fix acceptance criteria because `pnl_loss` was explicitly listed as a dynamic value that must be escaped.

## Verified

```powershell
.venv\Scripts\python.exe -m pytest tests/test_report_export.py -v
git diff --check
```

Results:

- Focused report tests: 30 passed.
- `git diff --check`: passed.
- Manual HTML escaping probe: failed for non-float `pnl_loss_ratio`.

## Required Fix

Escape the final `pnl_loss` text inserted into the HTML `stress-detail` line, while preserving normal float formatting such as `0.500`.
