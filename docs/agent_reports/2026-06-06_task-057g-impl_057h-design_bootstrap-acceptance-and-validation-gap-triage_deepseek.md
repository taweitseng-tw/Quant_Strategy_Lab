# Batch 057G-Impl + 057H-Design — Bootstrap Acceptance Smoke and Validation Gap Triage

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### 057G-Impl — Acceptance Smoke

`tests/test_bootstrap_monte_carlo_acceptance.py`: 10 tests covering the full bootstrap feature chain:

| # | Test | Chain verifies |
|---|---|---|
| 1 | `test_default_pipeline_omits_bootstrap` | Pipeline default off |
| 2 | `test_optin_pipeline_produces_bootstrap` | Pipeline enabled -> CI |
| 3 | `test_widget_shows_bootstrap_when_present` | Widget render |
| 4 | `test_widget_omits_bootstrap_when_ci_empty` | Widget empty CI |
| 5 | `test_markdown_shows_bootstrap` | Markdown render |
| 6 | `test_html_shows_bootstrap` | HTML render |
| 7 | `test_markdown_omits_bootstrap_when_ci_empty` | Markdown empty CI |
| 8 | `test_html_omits_bootstrap_when_ci_empty` | HTML empty CI |
| 9 | `test_ui_controls_pass_bootstrap_to_pipeline` | UI enabled |
| 10 | `test_ui_disabled_bootstrap_default` | UI disabled |

### 057H-Design

`docs/validation_gap_triage_057H.md` — Recommends WF per-window equity chart display as next task.

## Files Changed

| File | Change |
|---|---|
| `tests/test_bootstrap_monte_carlo_acceptance.py` | **Created** |
| `docs/validation_gap_triage_057H.md` | **Created** |
| `docs/changelog.md` | Batch entry |
| `docs/task_board.md` | Batch -> Done |

## Verification

```
acceptance: 10 passed
Full suite: 1084 passed, 1 warning
git diff --check -> passes
```
