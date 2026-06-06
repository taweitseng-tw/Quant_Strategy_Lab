# 057 Validation Expansion Acceptance Smoke Design — Task 057M

> Design-only. No production code changed.

## 1. Scope

Final acceptance smoke for the 057 validation expansion series covering bootstrap MC + WF equity storage + widget/report display.

## 2. Test File

`tests/test_validation_expansion_acceptance_smoke.py`

## 3. Test List (8 tests)

| # | Test | Chain verifies |
|---|---|---|
| 1 | `test_bootstrap_pipeline_chain` | Pipeline opt-in -> CI in result |
| 2 | `test_bootstrap_widget_chain` | Widget renders bootstrap card |
| 3 | `test_bootstrap_report_chain` | Markdown + HTML render bootstrap |
| 4 | `test_bootstrap_ui_chain` | UI controls -> PipelineConfig |
| 5 | `test_wf_equity_widget_chain` | Widget renders WF equity summary |
| 6 | `test_wf_equity_report_chain` | Markdown + HTML render WF equity table |
| 7 | `test_default_pipeline_no_extra_output` | Default config omits bootstrap + WF equity |
| 8 | `test_empty_ci_and_equity_omitted` | Missing/bootstrap empty CI, missing equity -> no output |

## 4. Fixtures

Reuse helpers from `test_bootstrap_monte_carlo_acceptance.py` and `test_validation_pipeline_service.py`.

## 5. Verification

```
pytest tests/test_validation_expansion_acceptance_smoke.py -v
```

## 6. Non-Goals

- Not implemented in this design-only task.
- No new production code.

## 7. Triage metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Dependencies**: 057L-Impl (report tables) — Done
