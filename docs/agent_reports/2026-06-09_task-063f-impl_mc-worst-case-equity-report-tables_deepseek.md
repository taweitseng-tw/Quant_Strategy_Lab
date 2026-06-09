Completed:
- Task 063F-Impl — MC Worst-Case Equity Report Tables + WF Efficiency Report Display.

Files changed:
- reports/generator.py (MC worst-case equity evidence in markdown + HTML)
- tests/test_report_export.py (7 new tests)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. Markdown report shows MC worst-case equity when worst_case_equity_curve ≥ 2 points: label (trade_step), start/end equity, % change, disclaimer.
2. HTML report shows equivalent content with proper escaping and italic disclaimer.
3. WFE display already existed in reports (unmodified).

Tests run:
- Report tests: 57 passed.
- Widget + pipeline + MC tests: 140 passed.

Assumptions:
- MC worst_case_equity_curve_type defaults to "trade_step" when absent.
- WFE keys (average_wfe, median_wfe) are present only when WFE was computed.

Known risks:
- MC equity disclaimer text is static — no distinction between curve types beyond label.
- WFE report behavior was already implemented in 057 series; this task only added tests.

Reviewer focus:
- MC worst-case equity evidence in both formatters (markdown lines 829-836, HTML lines 968-976).
- Trade-step label and disclaimer text.
- 7 tests covering include/omit for both formats.
