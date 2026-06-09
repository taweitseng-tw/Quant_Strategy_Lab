Completed:
- Batch 062L-Impl + 062M-Design — Report Price-Noise Display and Price-Noise Widget Display Design.

Files changed:
- reports/generator.py (price_noise detail sub-lines in markdown + HTML)
- tests/test_report_export.py (4 tests)
- docs/price_noise_widget_display_design_062M.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. Markdown reports now show price_noise detail sub-lines (noise_pct, iterations, warnings) when stress result with test_name="price_noise" exists.
2. HTML reports show equivalent detail sub-lines.
3. 4 report tests cover markdown/HTML include and omit cases.
4. 062M design: widget display contract for price-noise stress results.

Tests run:
- Report tests: 49 passed.

Assumptions:
- Price-noise stress data includes "assumptions" dict with noise_pct and iterations.
- Warnings are rendered with ⚠ prefix.

Known risks:
- price_noise results only appear in reports if run_price_noise_stress=True during pipeline run.
- Indentation errors in generator.py were fixed during this batch.

Reviewer focus:
- price_noise detail sub-lines in both formatters (markdown lines 801-808, HTML lines 930-937).
- 4 report tests cover include/omit for both formats.
