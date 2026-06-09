Completed:
- Batch 062H-Impl + 062I-Design — WF Equity Chart Widget Implementation and Price-Noise UI Config Controls Design.

Files changed:
- app/widgets/validation_summary.py (_WFEquityChart + wiring)
- tests/test_validation_summary.py (6 tests)
- docs/price_noise_ui_controls_design_062I.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. _WFEquityChart: PySide6-only QGraphicsView line chart, green/red for pass/fail, height 200px.
2. Chart appears after WF Equity Summary text section when equity data present.
3. 6 widget tests: chart visible with equity, absent without windows, absent with all None, partial equity, single point < 2, height constraint.
4. 062I design: Validate page controls (checkbox + 3 spinboxes), PipelineConfig mapping, 5 tests.

Tests run:
- Widget tests: 28 passed.
- Pipeline tests: 40 passed.

Assumptions:
- _WFEquityChart class name is checked in tests via string comparison (no private import).
- Chart uses fixed scene width proportional to longest equity curve.

Known risks:
- Very long equity curves (>1000 bars) may produce wide scenes — scroll area handles it.
- No axis labels yet (only lines).

Reviewer focus:
- _WFEquityChart._draw_chart() rendering logic (scaling, scene rect, QPolygonF).
- Chart wiring after WF Equity Summary section.
- 6 tests covering all visibility states.
