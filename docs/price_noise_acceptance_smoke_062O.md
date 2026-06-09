# Price-Noise Acceptance Smoke and Milestone Triage - Task 062O

> Acceptance smoke only. No production code changed.

## 1. Feature Chain Verification

| Layer | Evidence | Status |
|---|---|---|
| Engine | `stress_price_noise()` uses deterministic seeds, configurable iterations, and OHLC-preserving Gaussian reconstruction. | 34 stress tests passed |
| Pipeline | `PipelineConfig.run_price_noise_stress=False` by default; opt-in appends `test_name="price_noise"`. | 40 pipeline tests passed |
| UI controls | Validate page checkbox + three spinboxes are default-off and wire fraction-valued noise config into `PipelineConfig`. | 24 UI wiring tests passed |
| Widget | `ValidationSummary` shows price-noise details only when a `price_noise` stress result exists. | 35 widget tests passed |
| Report | Markdown and HTML reports show price-noise details only when a `price_noise` stress result exists, with HTML escaping. | 50 report tests passed |
| Full regression | Entire test suite. | 1291 tests passed |

## 2. Acceptance Points

- Default-off behavior is preserved across pipeline, UI controls, widget, and report surfaces.
- Price-noise evidence is shown only when the structured stress result exists.
- Research-only diagnostic wording is visible in widget and report warning paths.
- Reports include `method=ohlc_preserving_gaussian_noise` and `research_only=True` when supplied by the payload.
- Widget does not fabricate `research_only=True` when the payload omits that field.
- HTML report detail values and warnings are escaped.

## 3. Remaining Risks

| Risk | Severity | Notes |
|---|---|---|
| Price-noise is an approximate robustness diagnostic, not proof of live robustness. | Medium | Explicit warnings are preserved in engine payloads, widget output, and report output. |
| Long iteration counts can slow validation runs. | Low | UI default remains 50 iterations and the feature is opt-in. |
| Widget/report display depends on structured payload fields being present. | Low | Missing `research_only` renders as unknown in the widget rather than being invented. |

## 4. Verdict

Price-noise stress evidence is accepted as a research-only robustness diagnostic chain across engine, pipeline, UI controls, widget, and report surfaces.

It is not accepted as proof of live-trading robustness or as financial advice.

## 5. Verification

- `.\.venv\Scripts\python.exe -m pytest tests\test_stress_test.py -q` - 34 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_validation_pipeline_service.py -q` - 40 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_wfe_ui_wiring.py -q` - 24 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_validation_summary.py -q` - 35 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_report_export.py -q` - 50 passed.
- `.\.venv\Scripts\python.exe -m pytest tests -vv` - 1291 passed.
- `git diff --check` - passed with line-ending normalization warnings only.

## 6. Metadata

- Author: DeepSeek V4, corrected by Codex review
- Date: 2026-06-08
