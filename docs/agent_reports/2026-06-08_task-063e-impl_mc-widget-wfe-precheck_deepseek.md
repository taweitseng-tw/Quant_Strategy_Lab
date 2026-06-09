Completed:
- Task 063E-Impl — MC Worst-Case Equity Widget + WF Efficiency Display + Precheck UI Controls.

Files changed:
- app/widgets/validation_summary.py (_MCEquityChart widget, MC chart wiring, WFE line)
- app/ui/main_window.py (precheck controls + PipelineConfig wiring)
- tests/test_validation_summary.py (7 new tests)
- tests/test_wfe_ui_wiring.py (5 new tests)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. MC worst-case equity line chart appears when worst_case_equity_curve >= 2 points. Labeled "trade_step".
2. WF Efficiency line appears in Walk-Forward card when WFE keys present. None rendered as N/A.
3. IS Baseline Quality Precheck controls (parent + dependent non-positive checkbox). Non-positive disabled unless parent checked.
4. PipelineConfig receives precheck fields: run_is_baseline_quality_precheck, fail_is_baseline_on_nonpositive_pnl.

Tests run:
- Widget tests: 41 passed (34 existing + 7 new).
- Pipeline + MC tests: 98 passed.

Assumptions:
- MC equity chart is labeled with curve_type from serialized data (default "trade_step").
- WFE avg/median are None when not computed (walk-forward without WFE).

Known risks:
- MC equity chart shows trade-step curve, not bar-by-bar equity.
- WFE display assumes average_wfe and median_wfe are optional keys.

Reviewer focus:
- _MCEquityChart widget and wiring conditional on curve length >= 2.
- WFE line display logic (None → N/A).
- Precheck controls: nonpositive checkbox enabled/disabled with parent.
- Precheck PipelineConfig wiring in _handle_run (fail_nonpositive = run_precheck && checked).
