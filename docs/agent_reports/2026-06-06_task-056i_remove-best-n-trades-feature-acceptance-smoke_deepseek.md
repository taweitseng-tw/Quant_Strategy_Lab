# Task 056I — Remove Best N Trades Feature Acceptance Smoke

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### Acceptance Smoke Tests (`tests/test_remove_best_n_trades_acceptance.py`)

8 high-level tests covering the full remove-best-N feature chain:

| # | Test | Chain verified |
|---|---|---|
| 1 | `test_pipeline_enabled_produces_remove_best_n_result` | Pipeline -> stress result with assumptions/warnings/threshold |
| 2 | `test_pipeline_default_omits_remove_best_n` | Default config omits the test |
| 3 | `test_widget_renders_remove_best_n_detail` | ValidationSummary shows detail sub-lines |
| 4 | `test_markdown_report_includes_remove_best_n` | Markdown report includes detail lines |
| 5 | `test_html_report_includes_remove_best_n` | HTML report includes detail lines |
| 6 | `test_html_report_escapes_stress_detail` | HTML report escapes malicious `<script>`, `<img>`, `<b>` |
| 7 | `test_ui_enabled_config_reaches_pipeline` | UI controls -> PipelineConfig with enabled + custom |
| 8 | `test_ui_disabled_default_omits_stress` | UI controls -> PipelineConfig with disabled default |

## Files Changed

| File | Change |
|---|---|
| `tests/test_remove_best_n_trades_acceptance.py` | **Created** — 8 acceptance smoke tests |
| `docs/changelog.md` | Task 056I entry |
| `docs/task_board.md` | 056I -> Done |

## Verification

```
acceptance: 8 passed
regression (pipeline + widget + report + UI): 69 passed
Full suite: 1024 passed, 1 warning
git diff --check -> passes
```

Acceptance criteria:
1. ✅ Enabled pipeline output includes `remove_best_n_trades`.
2. ✅ Assumptions/warnings/threshold available.
3. ✅ ValidationSummary includes remove-best-N details.
4. ✅ Markdown and HTML reports include remove-best-N details.
5. ✅ HTML escaping for stress detail values.
6. ✅ UI controls pass enabled/custom values into PipelineConfig.
7. ✅ No production code changed.
8. ✅ Focused tests pass.
9. ✅ Full suite passes.
10. ✅ `git diff --check` passes.

## Known Issues

- None.

## Risks

- None. Test-only smoke coverage.
