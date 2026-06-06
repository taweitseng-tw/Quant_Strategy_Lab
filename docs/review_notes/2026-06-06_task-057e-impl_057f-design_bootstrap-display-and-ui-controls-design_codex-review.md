# Batch 057E-Impl + 057F-Design Codex Review - Bootstrap Display and UI Controls Design

## Verdict

Needs fix before acceptance.

## Score

7.8 / 10

## Review Summary

The batch stayed within the requested file boundaries: it added display surfaces, report tests, widget tests, and a UI-controls design document without changing pipeline or engine code. The 057F UI controls design is acceptable and can move to implementation.

However, the 057E display implementation has two correctness issues that should be fixed before acceptance. The surfaces currently render Bootstrap MC whenever `bootstrap_monte_carlo_result` is present, even if `confidence_intervals` is missing or empty. The task acceptance criteria required the output to stay absent when bootstrap data has no CI data. Also, profit factor CI values are formatted with integer formatting, which turns values like `1.15` and `2.80` into `1` and `3`.

## Findings

- Blocking: Widget, markdown, and HTML output should not render Bootstrap MC when `confidence_intervals` is missing or empty.
- Blocking: Profit factor CI values should use two-decimal formatting, not integer formatting.
- Test gap: Existing tests cover missing bootstrap object, but not bootstrap object with missing/empty CI data.
- Test gap: Existing tests do not assert PF CI precision.

## Verification

- Reviewed `app/widgets/validation_summary.py`.
- Reviewed `reports/generator.py`.
- Reviewed `tests/test_validation_summary.py` and `tests/test_report_export.py`.
- Reviewed `docs/bootstrap_ui_config_controls_design_057F.md`.
- Ran focused widget/report tests: 53 passed.
- Ran `git diff --check`: passed.

## Next Task

Batch 057E-Fix + 057F-Impl - Bootstrap Display Hardening and UI Controls.
