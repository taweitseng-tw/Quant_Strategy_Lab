"""Tests for report generation and ReportService — Task 007."""

from __future__ import annotations

import os
import tempfile
import pandas as pd
import pytest

from core.models.strategy import Strategy, StrategyBlock, Condition
from core.models.backtest_result import BacktestResult, Trade
from reports import generate_markdown_report, generate_html_report
from app.services.report_service import ReportService


@pytest.fixture
def mock_strategy() -> Strategy:
    """Fixture to build a simple four-block strategy."""
    return Strategy(
        name="test_strategy_007",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20}, operator=">")]
        ),
        long_exit=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 10}, operator="<")]
        ),
    )


@pytest.fixture
def mock_backtest_result() -> BacktestResult:
    """Fixture to build a mock BacktestResult with complete trades and metrics."""
    trades = [
        Trade(
            entry_time=pd.Timestamp("2026-01-01 09:30:00"),
            exit_time=pd.Timestamp("2026-01-01 10:00:00"),
            direction="long",
            entry_price=100.0,
            exit_price=105.0,
            quantity=1,
            pnl=5.0,
            exit_reason="signal",
        ),
        Trade(
            entry_time=pd.Timestamp("2026-01-02 09:30:00"),
            exit_time=pd.Timestamp("2026-01-02 10:15:00"),
            direction="short",
            entry_price=150.0,
            exit_price=152.0,
            quantity=1,
            pnl=-2.0,
            exit_reason="signal",
        ),
    ]

    metrics = {
        "total_trades": 2,
        "winning_trades": 1,
        "losing_trades": 1,
        "win_rate": 0.5,
        "total_pnl": 3.0,
        "avg_trade": 1.5,
        "gross_profit": 5.0,
        "gross_loss": 2.0,
        "profit_factor": 2.5,
        "max_drawdown_pnl": 2.0,
    }

    assumptions = {
        "execution_model": "next_bar_open",
        "signal_confirmation": "bar_close",
        "initial_capital": 100000.0,
        "commission_per_side": 1.0,
        "slippage_per_side_ticks": 0.0,
        "tick_size": 1.0,
    }

    warnings = ["Signal fired on last bar but cannot execute."]

    return BacktestResult(
        trades=trades,
        metrics=metrics,
        assumptions=assumptions,
        warnings=warnings,
    )


def test_markdown_report_generation(mock_strategy, mock_backtest_result) -> None:
    """Verify that Markdown report contains all required metrics, assumptions, and disclaimers."""
    provenance = {
        "generator_version": "0.1.0",
        "random_seed": 42,
        "rule_block_versions": {"SMA": "0.1.0"},
    }

    md = generate_markdown_report(mock_strategy, mock_backtest_result, provenance)

    # 1. Financial Safety Notice / Disclaimer check
    assert "This report is for research and backtesting purposes only." in md
    assert "Backtested performance does not guarantee future results." in md

    # 2. Strategy metadata / provenance check
    assert "test_strategy_007" in md
    assert "Random Seed" in md
    assert "42" in md

    # 3. Performance metrics check
    assert "$3.00" in md  # Net profit
    assert "2.50" in md   # Profit factor
    assert "$2.00" in md  # Drawdown

    # 4. Detailed trade table check
    assert "LONG" in md
    assert "SHORT" in md
    assert "$105.00" in md
    assert "$152.00" in md


def test_html_report_generation(mock_strategy, mock_backtest_result) -> None:
    """Verify that HTML report contains all required CSS layout structures and content."""
    provenance = {
        "generator_version": "0.1.0",
        "random_seed": 42,
        "rule_block_versions": {"SMA": "0.1.0"},
    }

    html = generate_html_report(mock_strategy, mock_backtest_result, provenance)

    # 1. HTML head & layout checks
    assert "<!DOCTYPE html>" in html
    assert "Outfit" in html  # Premium font import

    # 2. Financial safety disclaimer check
    assert "Financial Safety Notice &amp; Disclaimer" in html or "Financial Safety Notice" in html
    assert "Backtested performance does not guarantee future results." in html

    # 3. KPI structure check
    assert "$3.00" in html
    assert "2.50" in html

    # 4. Strategy logic check
    assert "test_strategy_007" in html
    assert "SMA(period=20)" in html


def test_report_service_exports(mock_strategy, mock_backtest_result) -> None:
    """Verify that ReportService correctly selects templates and writes files based on extension."""
    service = ReportService()

    provenance = {
        "generator_version": "0.1.0",
        "random_seed": 42,
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test Markdown write (.md)
        md_path = os.path.join(tmpdir, "report.md")
        service.export_report(mock_strategy, mock_backtest_result, md_path, provenance)
        assert os.path.exists(md_path)
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "# Quant Strategy Lab" in content
            assert "research and backtesting purposes" in content

        # Test HTML write (.html)
        html_path = os.path.join(tmpdir, "report.html")
        service.export_report(mock_strategy, mock_backtest_result, html_path, provenance)
        assert os.path.exists(html_path)
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "<!DOCTYPE html>" in content
            assert "Outfit" in content


def test_html_report_escaping_regression(mock_strategy, mock_backtest_result) -> None:
    """Verify that potentially malicious HTML/script tags in strategy name, warnings, and exit reasons are escaped."""
    malicious_strategy = Strategy(
        name="<script>alert('hack')</script>",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20}, operator=">")]
        ),
    )

    malicious_result = BacktestResult(
        trades=[
            Trade(
                entry_time=pd.Timestamp("2026-01-01 09:30:00"),
                exit_time=pd.Timestamp("2026-01-01 10:00:00"),
                direction="long",
                entry_price=100.0,
                exit_price=105.0,
                quantity=1,
                pnl=5.0,
                exit_reason="<img src=x onerror=alert(1)>",
            )
        ],
        metrics=mock_backtest_result.metrics,
        assumptions=mock_backtest_result.assumptions,
        warnings=["<div id='bad'>XSS</div>"],
    )

    provenance = {
        "generator_version": "<svg onload=alert(2)>",
        "random_seed": 42,
    }

    html_report = generate_html_report(malicious_strategy, malicious_result, provenance)

    # Assert that raw script, img, svg, div tags are NOT present in the HTML report
    assert "<script>alert('hack')</script>" not in html_report
    assert "<img src=x onerror=alert(1)>" not in html_report
    assert "<div id='bad'>XSS</div>" not in html_report
    assert "<svg onload=alert(2)>" not in html_report

    # Assert that their escaped representations ARE present
    assert "&lt;script&gt;alert(&#x27;hack&#x27;)&lt;/script&gt;" in html_report
    assert "&lt;img src=x onerror=alert(1)&gt;" in html_report
    assert "&lt;div id=&#x27;bad&#x27;&gt;XSS&lt;/div&gt;" in html_report
    assert "&lt;svg onload=alert(2)&gt;" in html_report


def test_html_report_direction_class_is_whitelisted(mock_strategy, mock_backtest_result) -> None:
    """Verify that trade direction cannot inject arbitrary HTML attributes through CSS classes."""
    malicious_result = BacktestResult(
        trades=[
            Trade(
                entry_time=pd.Timestamp("2026-01-01 09:30:00"),
                exit_time=pd.Timestamp("2026-01-01 10:00:00"),
                direction='long" onclick="alert(1)',
                entry_price=100.0,
                exit_price=105.0,
                quantity=1,
                pnl=5.0,
                exit_reason="signal",
            )
        ],
        metrics=mock_backtest_result.metrics,
        assumptions=mock_backtest_result.assumptions,
        warnings=[],
    )

    html_report = generate_html_report(mock_strategy, malicious_result)

    assert 'direction-badge long" onclick="alert(1)' not in html_report
    assert 'class="direction-badge unknown"' in html_report
    assert "LONG&quot; ONCLICK=&quot;ALERT(1)" in html_report


def test_mock_labeling_in_reports(mock_strategy, mock_backtest_result) -> None:
    """Verify that generate_markdown_report and generate_html_report include the mock label when is_mock=True."""
    provenance = {
        "generator_version": "0.1.0",
        "random_seed": 42,
    }

    # 1. Markdown check
    md_report = generate_markdown_report(mock_strategy, mock_backtest_result, provenance, is_mock=True)
    assert "Sample / Mock Report (No Project Loaded)" in md_report

    # 2. HTML check
    html_report = generate_html_report(mock_strategy, mock_backtest_result, provenance, is_mock=True)
    assert "Sample / Mock Report (No Project Loaded)" in html_report
    assert "Sample / Mock Backtest Performance" in html_report


def test_report_service_export_mock_report() -> None:
    """Verify that ReportService.export_mock_report generates and saves a labeled mock report."""
    service = ReportService()

    with tempfile.TemporaryDirectory() as tmpdir:
        mock_path = os.path.join(tmpdir, "mock_report.html")
        service.export_mock_report(mock_path)
        assert os.path.exists(mock_path)

        with open(mock_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "<!DOCTYPE html>" in content
            assert "Sample / Mock Report (No Project Loaded)" in content


# ---------------------------------------------------------------------------
# Validation evidence — Task 027
# ---------------------------------------------------------------------------


def _make_validation_dict(**overrides) -> dict:
    result = {
        "split_metadata": {"train_rows": 60, "validation_rows": 20, "oos_rows": 20},
        "baseline_metrics": {"total_pnl": 5000.0, "profit_factor": 1.8, "total_trades": 22,
                             "max_drawdown_pnl": 2000.0, "win_rate": 0.55, "avg_trade": 227.0},
        "stress_results": [
            {"test_name": "commission_2.0x", "passed": True,
             "degradation": {"total_pnl": -0.15}},
        ],
        "monte_carlo_summary": {
            "iterations": 15,
            "percentile_summary": {"total_pnl": {"p5": 1000.0, "p50": 4800.0, "p95": 9000.0}},
            "worst_case": {"total_pnl": 1000.0},
        },
        "walk_forward_summary": {"window_count": 5, "pass_count": 3, "pass_rate": 0.6},
        "elimination_result": {"passed": True, "failed_rules": []},
    }
    result.update(overrides)
    return result


def test_markdown_includes_validation_sections(mock_strategy, mock_backtest_result):
    """Markdown report with validation_result must include all evidence sections."""
    vr = _make_validation_dict()
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)

    assert "## Validation Evidence" in md
    assert "Split" in md
    assert "Baseline" in md
    assert "Stress" in md
    assert "MC" in md
    assert "WF" in md
    assert "Elimination" in md


def test_html_includes_validation_sections(mock_strategy, mock_backtest_result):
    """HTML report with validation_result must include all evidence sections."""
    vr = _make_validation_dict()
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)

    assert "Validation Evidence" in html_out
    assert "Split:" in html_out
    assert "Baseline:" in html_out
    assert "Stress" in html_out
    assert "MC" in html_out
    assert "WF:" in html_out
    assert "Elimination" in html_out


def test_no_validation_shows_placeholder(mock_strategy, mock_backtest_result):
    """Without validation_result, both formats must show 'not included' message."""
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=None)
    assert "No validation evidence" in md

    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=None)
    assert "No validation evidence" in html_out


def test_elimination_failed_rules_in_report(mock_strategy, mock_backtest_result):
    """Elimination failure must list failed rules in both formats."""
    vr = _make_validation_dict(
        elimination_result={"passed": False,
                            "failed_rules": ["min_total_pnl (-500 < 0)", "min_trade_count (3 < 5)"]}
    )
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "ELIMINATED" in md
    assert "min_total_pnl" in md
    assert "min_trade_count" in md

    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "ELIMINATED" in html_out
    assert "min_total_pnl" in html_out


def test_elimination_thresholds_in_report(mock_strategy, mock_backtest_result):
    """Enabled config_snapshot thresholds must appear in both formats."""
    vr = _make_validation_dict(
        elimination_result={"passed": True, "failed_rules": [],
                            "warnings": [],
                            "config_snapshot": {
                                "min_trade_count": 5,
                                "min_profit_factor": 0.5,
                                "max_drawdown_pnl": None,
                                "min_win_rate": False,
                                "require_optional": False,
                            }}
    )
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "PASSED" in md
    assert "Thresholds applied:" in md
    assert "min_trade_count=5" in md
    assert "min_profit_factor=0.5" in md
    assert "max_drawdown_pnl" not in md
    assert "min_win_rate" not in md
    assert "require_optional" not in md

    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "PASSED" in html_out
    assert "Thresholds applied" in html_out
    assert "min_trade_count=5" in html_out
    assert "min_profit_factor=0.5" in html_out
    assert "max_drawdown_pnl" not in html_out
    assert "min_win_rate" not in html_out
    assert "require_optional" not in html_out


def test_elimination_warnings_in_report(mock_strategy, mock_backtest_result):
    """Elimination warnings must appear in both formats."""
    vr = _make_validation_dict(
        elimination_result={"passed": True, "failed_rules": [],
                            "warnings": ["OOS data not provided. Skipping OOS rules."]}
    )
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "Warning:" in md
    assert "OOS data not provided" in md

    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "Warning:" in html_out
    assert "OOS data not provided" in html_out


def test_elimination_no_thresholds_when_none_enabled(mock_strategy, mock_backtest_result):
    """When no config_snapshot thresholds are enabled, omit the thresholds line."""
    vr = _make_validation_dict(
        elimination_result={"passed": True, "failed_rules": [],
                            "warnings": [],
                            "config_snapshot": {
                                "min_trade_count": None,
                                "min_profit_factor": None,
                                "min_win_rate": False,
                                "require_optional": False,
                            }}
    )
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "Thresholds applied:" not in md
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "Thresholds applied" not in html_out


def test_malicious_validation_string_escaped_in_html(mock_strategy, mock_backtest_result):
    """HTML report must escape malicious strings in validation evidence."""
    vr = _make_validation_dict(
        elimination_result={"passed": False,
                            "failed_rules": ["<script>alert('xss')</script>"]}
    )
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "<script>" not in html_out
    assert "&lt;script&gt;" in html_out


def test_report_service_passes_validation_result(mock_strategy, mock_backtest_result):
    """ReportService must pass validation_result through to the generator."""
    import tempfile, os
    service = ReportService()
    vr = _make_validation_dict()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Markdown
        md_path = os.path.join(tmpdir, "test_vr.md")
        service.export_report(mock_strategy, mock_backtest_result, md_path,
                              validation_result=vr)
        with open(md_path, "r") as f:
            assert "Validation Evidence" in f.read()

        # HTML
        html_path = os.path.join(tmpdir, "test_vr.html")
        service.export_report(mock_strategy, mock_backtest_result, html_path,
                              validation_result=vr)
        with open(html_path, "r") as f:
            assert "Validation Evidence" in f.read()

def test_pdf_report_export_creates_pdf_file_and_has_magic_bytes(mock_strategy, mock_backtest_result):
    """ReportService must export a real PDF using QPdfWriter starting with %PDF."""
    import tempfile, os
    from PySide6.QtWidgets import QApplication

    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()

    service = ReportService()

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "test_report.pdf")
        service.export_report(mock_strategy, mock_backtest_result, pdf_path)

        assert os.path.exists(pdf_path)
        with open(pdf_path, "rb") as f:
            header = f.read(4)
            assert header == b"%PDF"


def test_pdf_report_export_uses_html_generation_and_passes_results(mock_strategy, mock_backtest_result):
    """
    Verify the PDF branch delegates to HTML generation and includes all
    validation, multi-instrument, and disclaimer components in the printed content.
    We mock QTextDocument.setHtml to inspect the exact string being fed to the PDF writer.
    This mock doesn't hide the behavior under test; it just lets us read the content
    before it is rasterized into a binary PDF format.
    """
    import tempfile, os
    from unittest.mock import patch
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QTextDocument
    from app.services.multi_instrument_service import MultiInstrumentBacktestResult

    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()

    service = ReportService()

    vr = {"elimination_result": {"passed": True}}
    mir = MultiInstrumentBacktestResult(
        instrument_count=1, success_count=1, failure_count=0,
        aggregate_metrics={"mean_total_pnl": 100.0},
        per_instrument=[], warnings=[], assumptions={}
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "test_plumbing.pdf")

        with patch.object(QTextDocument, "setHtml") as mock_setHtml:
            service.export_report(
                mock_strategy, mock_backtest_result, pdf_path,
                validation_result=vr, multi_instrument_result=mir
            )

            mock_setHtml.assert_called_once()
            html_content = mock_setHtml.call_args[0][0]

            # test_pdf_report_export_uses_html_generation
            assert "<!DOCTYPE html>" in html_content

            # test_pdf_report_export_passes_validation_result
            assert "Validation Evidence" in html_content
            assert "PASSED" in html_content

            # test_pdf_report_export_passes_multi_instrument_result
            assert "Multi-Instrument Evidence" in html_content

            # test_pdf_report_export_preserves_disclaimer_source
            assert "Backtested performance does not guarantee future results." in html_content


def test_markdown_and_html_report_export_still_work(mock_strategy, mock_backtest_result):
    """Ensure adding PDF support did not break the existing Markdown and HTML paths."""
    import tempfile, os
    service = ReportService()

    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = os.path.join(tmpdir, "test_report.md")
        html_path = os.path.join(tmpdir, "test_report.html")

        service.export_report(mock_strategy, mock_backtest_result, md_path)
        service.export_report(mock_strategy, mock_backtest_result, html_path)

        assert os.path.exists(md_path)
        assert os.path.exists(html_path)

        with open(md_path, "r", encoding="utf-8") as f:
            assert "Strategy Logic" in f.read()

        with open(html_path, "r", encoding="utf-8") as f:
            assert "<!DOCTYPE html>" in f.read()


def test_report_export_walk_forward_summary_compatible_with_stability_score(mock_strategy, mock_backtest_result):
    """Report generators must not crash when walk_forward_summary has stability_score, and should optionally render it."""
    vr = _make_validation_dict()
    vr["walk_forward_summary"]["stability_score"] = 5.67

    # Should not crash
    md_report = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    html_report = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)

    assert "Validation Evidence" in md_report
    assert "Validation Evidence" in html_report


# ---------------------------------------------------------------------------
# Task 044D: WFE Reporting Tests
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# OOS Metrics in reports (Task 056D)
# ---------------------------------------------------------------------------


def test_markdown_includes_oos_line_when_present(mock_strategy, mock_backtest_result):
    """Markdown validation section must include OOS line when oos_metrics exists."""
    vr = _make_validation_dict(oos_metrics={
        "total_trades": 8, "total_pnl": 1200.0, "profit_factor": 1.25,
        "max_drawdown_pnl": 3000.0, "win_rate": 0.50, "avg_trade": 150.0,
    })
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "**OOS**:" in md
    assert "1,200" in md
    assert "1.25" in md
    assert "3,000" in md


def test_markdown_omits_oos_when_absent(mock_strategy, mock_backtest_result):
    """Markdown validation section must NOT include OOS line when oos_metrics is missing."""
    vr = _make_validation_dict()  # no oos_metrics key
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "**OOS**:" not in md


def test_html_includes_oos_line_when_present(mock_strategy, mock_backtest_result):
    """HTML validation section must include OOS line when oos_metrics exists."""
    vr = _make_validation_dict(oos_metrics={
        "total_trades": 8, "total_pnl": 1200.0, "profit_factor": 1.25,
        "max_drawdown_pnl": 3000.0,
    })
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "<b>OOS:</b>" in html_out
    assert "1,200" in html_out
    assert "1.25" in html_out
    assert "3,000" in html_out


def test_html_omits_oos_when_absent(mock_strategy, mock_backtest_result):
    """HTML validation section must NOT include OOS line when oos_metrics is missing."""
    vr = _make_validation_dict()  # no oos_metrics key
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "<b>OOS:</b>" not in html_out


def test_report_export_wfe_rendering_with_wfe(mock_strategy, mock_backtest_result):
    """Reports must render WFE fields when provided in the summary."""
    vr = _make_validation_dict()
    vr["walk_forward_summary"].update({
        "average_wfe": 0.854,
        "median_wfe": 0.81,
        "defined_wfe_count": 4,
        "undefined_wfe_count": 1,
    })

    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)

    # Markdown checks
    assert "Avg=0.85" in md
    assert "Median=0.81" in md
    assert "Defined Windows=4" in md
    assert "Undefined Windows=1" in md

    # HTML checks
    assert "Avg=0.85" in html_out
    assert "Median=0.81" in html_out
    assert "Defined Windows=4" in html_out
    assert "Undefined Windows=1" in html_out


def test_report_export_wfe_rendering_with_none_wfe(mock_strategy, mock_backtest_result):
    """Reports must safely render None WFE fields as N/A."""
    vr = _make_validation_dict()
    vr["walk_forward_summary"].update({
        "average_wfe": None,
        "median_wfe": None,
        "defined_wfe_count": 0,
        "undefined_wfe_count": 5,
    })

    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)

    assert "Avg=N/A" in md
    assert "Median=N/A" in md
    assert "Undefined Windows=5" in md

    assert "Avg=N/A" in html_out
    assert "Median=N/A" in html_out
    assert "Undefined Windows=5" in html_out


# ---------------------------------------------------------------------------
# Task 049F: MTF Report Safety
# ---------------------------------------------------------------------------

def test_report_base_condition_description_unchanged():
    from reports.generator import format_block_desc
    block = StrategyBlock(conditions=[Condition(indicator="SMA", params={"period": 20}, operator=">")])
    desc = format_block_desc(block)
    assert desc == "close > SMA(period=20)"

def test_report_condition_description_includes_timeframe():
    from reports.generator import format_block_desc
    block = StrategyBlock(conditions=[Condition(indicator="SMA", params={"period": 20, "timeframe": 5}, operator=">")])
    desc = format_block_desc(block)
    assert desc == "close > SMA(period=20) [TF: 5m]"

def test_report_does_not_crash_with_mtf_conditions(mock_strategy, mock_backtest_result):
    from reports import generate_markdown_report, generate_html_report
    mock_strategy.long_entry.conditions.append(
        Condition(indicator="SMA", params={"period": 50, "timeframe": 15}, operator=">")
    )
    md = generate_markdown_report(mock_strategy, mock_backtest_result)
    html = generate_html_report(mock_strategy, mock_backtest_result)

    assert "[TF: 15m]" in md
    assert "[TF: 15m]" in html


# ---------------------------------------------------------------------------
# Stress detail sub-lines in reports (Task 056G-Impl)
# ---------------------------------------------------------------------------


def test_markdown_includes_remove_best_n_detail_lines(mock_strategy, mock_backtest_result):
    """Markdown report must show remove_best_n sub-lines with assumptions."""
    vr = _make_validation_dict(stress_results=[
        {"test_name": "commission_2.0x", "passed": True,
         "degradation": {"total_pnl": -0.15}},
        {"test_name": "remove_best_n_trades", "passed": False,
         "degradation": {"total_pnl": -0.83},
         "assumptions": {
             "n": 2, "removed_count": 2, "surviving_count": 2,
             "pnl_loss_ratio": 0.833,
         },
         "warnings": ["Insufficient trades for remove-best-n stress test."],
         "threshold": {"max_pnl_loss": 0.30},
        },
    ])
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)

    assert "commission_2.0x" in md
    assert "remove_best_n_trades" in md
    assert "Removed:" in md
    assert "n=2" in md
    assert "pnl_loss=0.833" in md
    assert "threshold=0.30" in md
    assert "WARNING:" in md
    assert "Insufficient trades" in md


def test_html_includes_remove_best_n_detail_lines(mock_strategy, mock_backtest_result):
    """HTML report must show remove_best_n sub-lines with escaped text."""
    vr = _make_validation_dict(stress_results=[
        {"test_name": "remove_best_n_trades", "passed": False,
         "degradation": {"total_pnl": -0.83},
         "assumptions": {
             "n": 2, "removed_count": 2, "surviving_count": 2,
             "pnl_loss_ratio": 0.833,
         },
         "warnings": ["Test <script>alert(1)</script>."],
         "threshold": {"max_pnl_loss": 0.30},
        },
    ])
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)

    assert "remove_best_n_trades" in html_out
    assert "stress-detail" in html_out
    assert "Removed:" in html_out
    assert "n=2" in html_out
    assert "pnl_loss=0.833" in html_out
    assert "threshold=0.30" in html_out
    assert "warning-item" in html_out
    # HTML warning must be escaped.
    assert "&lt;script&gt;" in html_out
    assert "<script>" not in html_out


def test_markdown_no_detail_lines_for_basic_stress(mock_strategy, mock_backtest_result):
    """Basic stress tests must NOT have detail sub-lines."""
    vr = _make_validation_dict(stress_results=[
        {"test_name": "commission_2.0x", "passed": True,
         "degradation": {"total_pnl": -0.15}},
    ])
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "commission_2.0x" in md
    assert "Removed:" not in md
    assert "pnl_loss" not in md


def test_html_stress_detail_values_escaped(mock_strategy, mock_backtest_result):
    """Malicious detail values in remove_best_n_trades must be HTML-escaped."""
    vr = _make_validation_dict(stress_results=[
        {"test_name": "remove_best_n_trades", "passed": False,
         "degradation": {"total_pnl": -0.50},
         "assumptions": {
             "n": "<script>x</script>",
             "removed_count": 1,
             "surviving_count": 3,
             "pnl_loss_ratio": "<img src=x>",
         },
         "threshold": {"max_pnl_loss": "<b>bad</b>"},
        },
    ])
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)

    # Raw malicious HTML must not appear.
    assert "<script>x</script>" not in html_out
    assert "<b>bad</b>" not in html_out
    assert "<img src=x>" not in html_out
    # Escaped equivalents must appear.
    assert "&lt;script&gt;x&lt;/script&gt;" in html_out
    assert "&lt;b&gt;bad&lt;/b&gt;" in html_out
    assert "&lt;img src=x&gt;" in html_out


# ---------------------------------------------------------------------------
# Precheck visibility in reports (Task 056K-Impl)
# ---------------------------------------------------------------------------


def test_markdown_includes_precheck_line(mock_strategy, mock_backtest_result):
    """Markdown report must include precheck line when precheck_failed=True."""
    vr = _make_validation_dict(precheck_failed=True, elimination_result={
        "passed": False,
        "failed_rules": ["Precheck: zero trades."],
    })
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "**Precheck**:" in md
    assert "FAILED" in md
    assert "zero trades" in md


def test_markdown_omits_precheck_when_false(mock_strategy, mock_backtest_result):
    """Markdown report must NOT include precheck line when precheck_failed=False."""
    vr = _make_validation_dict(precheck_failed=False)
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "**Precheck**:" not in md


def test_html_includes_precheck_line(mock_strategy, mock_backtest_result):
    """HTML report must include precheck line when precheck_failed=True."""
    vr = _make_validation_dict(precheck_failed=True, elimination_result={
        "passed": False,
        "failed_rules": ["Precheck: zero trades."],
    })
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "<b>Precheck:</b>" in html_out
    assert "FAILED" in html_out
    assert "zero trades" in html_out


def test_html_precheck_reason_escaped(mock_strategy, mock_backtest_result):
    """HTML precheck reason must be escaped."""
    vr = _make_validation_dict(precheck_failed=True, elimination_result={
        "passed": False,
        "failed_rules": ["Precheck: <script>x</script>"],
    })
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "<script>x</script>" not in html_out
    assert "&lt;script&gt;x&lt;/script&gt;" in html_out


# ---------------------------------------------------------------------------
# Bootstrap MC display in reports (Task 057E-Impl)
# ---------------------------------------------------------------------------


def _make_bootstrap_validation_dict():
    return _make_validation_dict(bootstrap_monte_carlo_result={
        "test_name": "bootstrap",
        "iterations": 200,
        "stability_score": 0.85,
        "confidence_intervals": {
            "total_pnl": {"ci_lower": 1200.0, "ci_upper": 9800.0, "ci_mean": 5400.0},
            "profit_factor": {"ci_lower": 1.15, "ci_upper": 2.80, "ci_mean": 1.95},
            "max_drawdown_pnl": {"ci_lower": 500.0, "ci_upper": 12000.0, "ci_mean": 4200.0},
        },
    })


def test_markdown_includes_bootstrap_mc(mock_strategy, mock_backtest_result):
    """Markdown report must include Bootstrap MC section when data is present."""
    vr = _make_bootstrap_validation_dict()
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "**Bootstrap MC**" in md
    assert "200 iter" in md
    assert "0.85" in md
    assert "1,200" in md
    assert "9,800" in md


def test_markdown_omits_bootstrap_when_absent(mock_strategy, mock_backtest_result):
    """Markdown report must NOT include Bootstrap MC when data is missing."""
    vr = _make_validation_dict()
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "Bootstrap MC" not in md


def test_html_includes_bootstrap_mc(mock_strategy, mock_backtest_result):
    """HTML report must include Bootstrap MC section when data is present."""
    vr = _make_bootstrap_validation_dict()
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "<b>Bootstrap MC</b>" in html_out
    assert "200 iter" in html_out
    assert "0.85" in html_out
    assert "1,200" in html_out


def test_html_omits_bootstrap_when_absent(mock_strategy, mock_backtest_result):
    """HTML report must NOT include Bootstrap MC when data is missing."""
    vr = _make_validation_dict()
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "Bootstrap MC" not in html_out


def test_markdown_omits_bootstrap_when_ci_empty(mock_strategy, mock_backtest_result):
    """Markdown must omit Bootstrap MC when CI is empty."""
    vr = _make_validation_dict(bootstrap_monte_carlo_result={
        "test_name": "bootstrap", "iterations": 200, "confidence_intervals": {},
    })
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "Bootstrap MC" not in md


def test_html_omits_bootstrap_when_ci_empty(mock_strategy, mock_backtest_result):
    """HTML must omit Bootstrap MC when CI is empty."""
    vr = _make_validation_dict(bootstrap_monte_carlo_result={
        "test_name": "bootstrap", "iterations": 200, "confidence_intervals": {},
    })
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "Bootstrap MC" not in html_out


# ---------------------------------------------------------------------------
# WF Equity tables in reports (Task 057L-Impl)
# ---------------------------------------------------------------------------


def test_markdown_wf_equity_table_shown(mock_strategy, mock_backtest_result):
    """Markdown must show WF equity table when equity curves are present."""
    vr = _make_validation_dict(walk_forward_summary={
        "window_count": 3, "pass_count": 2, "pass_rate": 0.67,
        "windows": [
            {"index": 0, "equity_curve": [100000.0, 100500.0, 101000.0], "passed": True},
            {"index": 1, "equity_curve": [100000.0, 99000.0], "passed": False},
        ],
    })
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "WF Equity by Window" in md
    assert "101,000" in md
    assert "+1.0%" in md
    assert "PASSED" in md


def test_markdown_wf_equity_table_absent(mock_strategy, mock_backtest_result):
    """Markdown must omit WF equity table when no equity data."""
    vr = _make_validation_dict(walk_forward_summary={
        "window_count": 2, "pass_count": 1, "pass_rate": 0.5,
        "windows": [
            {"index": 0, "equity_curve": None, "passed": True},
        ],
    })
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "WF Equity by Window" not in md


def test_html_wf_equity_table_shown(mock_strategy, mock_backtest_result):
    """HTML must show WF equity table when equity curves are present."""
    vr = _make_validation_dict(walk_forward_summary={
        "window_count": 2, "pass_count": 1, "pass_rate": 0.5,
        "windows": [
            {"index": 0, "equity_curve": [100000.0, 105000.0], "passed": True},
            {"index": 1, "equity_curve": [100000.0, 98000.0], "passed": False},
        ],
    })
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "WF Equity by Window" in html_out
    assert "pnl-positive" in html_out
    assert "pnl-negative" in html_out
    assert "PASSED" in html_out


def test_html_wf_equity_table_absent(mock_strategy, mock_backtest_result):
    """HTML must omit WF equity table when no equity data."""
    vr = _make_validation_dict(walk_forward_summary={
        "window_count": 2, "pass_count": 1, "pass_rate": 0.5,
    })
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "WF Equity by Window" not in html_out


def test_wf_equity_table_capped_at_5(mock_strategy, mock_backtest_result):
    """WF equity table must show '... more windows' when >5 windows."""
    windows = []
    for i in range(7):
        windows.append({
            "index": i, "equity_curve": [100000.0, 100000.0 + i * 100.0], "passed": True,
        })
    vr = _make_validation_dict(walk_forward_summary={
        "window_count": 7, "pass_count": 7, "pass_rate": 1.0, "windows": windows,
    })
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "WF Equity by Window" in md
    assert "2 more" in md


# ---------------------------------------------------------------------------
# Price-noise stress display in reports (Task 062L-Impl)
# ---------------------------------------------------------------------------


def _with_price_noise(vr: dict) -> dict:
    """Add a price_noise stress result to a validation dict."""
    vr = dict(vr)
    vr["stress_results"] = list(vr.get("stress_results", [])) + [
        {
            "test_name": "price_noise",
            "passed": True,
            "degradation": {"total_pnl": -0.05},
            "assumptions": {
                "noise_pct": 0.005,
                "iterations": 50,
                "method": "ohlc_preserving_gaussian_noise",
                "research_only": True,
            },
            "warnings": [
                "Price-noise stress test is an approximate robustness diagnostic. "
                "It does not prove live-trading robustness."
            ],
        },
    ]
    return vr


def test_markdown_includes_price_noise_when_opt_in(mock_strategy, mock_backtest_result):
    """Markdown must include price_noise sub-lines when opt-in."""
    vr = _make_validation_dict()
    vr = _with_price_noise(vr)
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "price_noise" in md
    assert "noise_pct=0.5%" in md
    assert "iterations" in md
    assert "method=ohlc_preserving_gaussian_noise" in md
    assert "research_only=True" in md
    assert "WARNING:" in md
    assert "does not prove live-trading robustness" in md


def test_markdown_omits_price_noise_by_default(mock_strategy, mock_backtest_result):
    """Markdown must NOT include price_noise when default."""
    vr = _make_validation_dict()
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "price_noise" not in md


def test_html_includes_price_noise_when_opt_in(mock_strategy, mock_backtest_result):
    """HTML must include price_noise sub-lines when opt-in."""
    vr = _make_validation_dict()
    vr = _with_price_noise(vr)
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "price_noise" in html_out
    assert "noise_pct=0.5%" in html_out
    assert "iterations=50" in html_out
    assert "method=ohlc_preserving_gaussian_noise" in html_out
    assert "research_only=True" in html_out
    assert "warning-item" in html_out
    assert "does not prove live-trading robustness" in html_out


def test_html_price_noise_detail_and_warning_are_escaped(mock_strategy, mock_backtest_result):
    """HTML price-noise detail and warning values must be escaped."""
    vr = _make_validation_dict(stress_results=[
        {
            "test_name": "price_noise",
            "passed": False,
            "degradation": {"total_pnl": -0.10},
            "assumptions": {
                "noise_pct": "<script>bad</script>",
                "iterations": "<img src=x onerror=alert(1)>",
                "method": "<b>bad</b>",
                "research_only": True,
            },
            "warnings": ["Warning <script>alert(1)</script>"],
        },
    ])
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)

    assert "&lt;script&gt;bad&lt;/script&gt;" in html_out
    assert "&lt;img src=x onerror=alert(1)&gt;" in html_out
    assert "&lt;b&gt;bad&lt;/b&gt;" in html_out
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_out
    assert "<script>" not in html_out
    assert "<img src=x" not in html_out


def test_html_omits_price_noise_by_default(mock_strategy, mock_backtest_result):
    """HTML must NOT include price_noise when default."""
    vr = _make_validation_dict()
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert "price_noise" not in html_out


# ---------------------------------------------------------------------------
# MC Worst-Case Equity report display (Task 063F-Impl)
# ---------------------------------------------------------------------------


def _with_mc_worst_case_equity(vr: dict) -> dict:
    """Add worst_case_equity_curve to a validation dict."""
    vr = dict(vr)
    mc = dict(vr.get('monte_carlo_summary', {}))
    mc['worst_case_equity_curve'] = [100000.0, 99000.0, 97000.0, 95000.0]
    mc['worst_case_equity_curve_type'] = 'trade_step'
    vr['monte_carlo_summary'] = mc
    return vr


def test_markdown_includes_mc_worst_case_equity_when_present(mock_strategy, mock_backtest_result):
    """Markdown must include MC worst-case equity when curve has >= 2 points."""
    vr = _make_validation_dict()
    vr = _with_mc_worst_case_equity(vr)
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert 'MC Worst-Case Equity' in md
    assert 'trade-step' in md
    assert 'trade_step' not in md
    assert 'surviving trades only' in md
    assert 'not a bar-by-bar equity curve' in md


def test_markdown_omits_mc_worst_case_equity_when_absent(mock_strategy, mock_backtest_result):
    """Markdown must omit MC worst-case equity when curve is absent."""
    vr = _make_validation_dict()
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert 'MC Worst-Case Equity' not in md


def test_html_includes_mc_worst_case_equity_when_present(mock_strategy, mock_backtest_result):
    """HTML must include MC worst-case equity when curve has >= 2 points."""
    vr = _make_validation_dict()
    vr = _with_mc_worst_case_equity(vr)
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert 'MC Worst-Case Equity' in html_out
    assert 'trade-step' in html_out
    assert 'trade_step' not in html_out
    assert 'surviving trades only' in html_out
    assert 'not a bar-by-bar equity curve' in html_out


def test_html_omits_mc_worst_case_equity_when_absent(mock_strategy, mock_backtest_result):
    """HTML must omit MC worst-case equity when curve is absent."""
    vr = _make_validation_dict()
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert 'MC Worst-Case Equity' not in html_out


def test_markdown_wfe_already_displayed_when_present(mock_strategy, mock_backtest_result):
    """WFE line must appear when average_wfe is present (existing behavior)."""
    vr = _make_validation_dict()
    vr['walk_forward_summary']['average_wfe'] = 1.25
    vr['walk_forward_summary']['median_wfe'] = 0.85
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert 'WF Efficiency' in md
    assert 'Avg=1.25' in md
    assert 'Median=0.85' in md


def test_markdown_wfe_none_renders_as_na(mock_strategy, mock_backtest_result):
    """WFE must render None avg/median as N/A."""
    vr = _make_validation_dict()
    vr['walk_forward_summary']['average_wfe'] = None
    vr['walk_forward_summary']['median_wfe'] = 0.85
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert 'WF Efficiency' in md
    assert 'Avg=N/A' in md
    assert 'Median=0.85' in md


def test_markdown_wfe_absent_when_keys_missing(mock_strategy, mock_backtest_result):
    """WFE line must be absent when average_wfe key is not present."""
    vr = _make_validation_dict()
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    assert 'WF Efficiency' not in md


def test_reports_wfe_shown_when_only_median_key_present(mock_strategy, mock_backtest_result):
    """WFE line must appear when median_wfe is present even if average_wfe is missing."""
    vr = _make_validation_dict()
    vr['walk_forward_summary']['median_wfe'] = 0.85

    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)

    assert 'WF Efficiency' in md
    assert 'Avg=N/A' in md
    assert 'Median=0.85' in md
    assert 'WF Efficiency' in html_out
    assert 'Avg=N/A' in html_out
    assert 'Median=0.85' in html_out


# ---------------------------------------------------------------------------
# Tasks 445-450: Strategy Explainability Report Section Tests
# ---------------------------------------------------------------------------


def test_explainability_header_present_in_markdown(mock_strategy, mock_backtest_result):
    """1. Explainability header present in Markdown."""
    md = generate_markdown_report(mock_strategy, mock_backtest_result)
    assert "## Strategy Explainability" in md


def test_explainability_panel_present_in_html(mock_strategy, mock_backtest_result):
    """2. Explainability panel present in HTML."""
    html_out = generate_html_report(mock_strategy, mock_backtest_result)
    assert 'class="panel explainability-panel"' in html_out
    assert 'Strategy Explainability' in html_out


def test_explainability_strategy_name_rendering(mock_strategy, mock_backtest_result):
    """3. Strategy name rendering in both formats."""
    md = generate_markdown_report(mock_strategy, mock_backtest_result)
    html_out = generate_html_report(mock_strategy, mock_backtest_result)

    assert "**Name:** test_strategy_007" in md
    assert "<b>Strategy Name:</b> test_strategy_007" in html_out


def test_explainability_rules_text_display(mock_strategy, mock_backtest_result):
    """4. Rules text display in both formats."""
    md = generate_markdown_report(mock_strategy, mock_backtest_result)
    html_out = generate_html_report(mock_strategy, mock_backtest_result)

    assert "- **Long Entry:** close &gt; SMA(period=20)" in md
    assert "- **Long Exit:** close &lt; SMA(period=10)" in md
    assert "- **Short Entry:** Inactive" in md
    assert "- **Short Exit:** Inactive" in md

    assert "close &gt; SMA(period=20)" in html_out
    assert "close &lt; SMA(period=10)" in html_out
    assert "class=\"rule-item inactive\"" in html_out


def test_explainability_provenance_rendering(mock_strategy, mock_backtest_result):
    """5. Provenance rendering and cleanup of defaults."""
    # Supplied provenance
    provenance = {
        "generator": "ga_search",
        "generator_version": "1.2.3",
        "random_seed": 999,
        "source_type": "generated",
    }
    md = generate_markdown_report(mock_strategy, mock_backtest_result, provenance=provenance)
    html_out = generate_html_report(mock_strategy, mock_backtest_result, provenance=provenance)

    assert "**Source:** Generated (ga_search v1.2.3, seed=999)" in md
    assert "Generated (ga_search v1.2.3, seed=999)" in html_out

    # Missing/Manual provenance
    provenance_manual = {"source_type": "manual"}
    md_manual = generate_markdown_report(mock_strategy, mock_backtest_result, provenance=provenance_manual)
    html_manual = generate_html_report(mock_strategy, mock_backtest_result, provenance=provenance_manual)

    assert "**Source:** Manual / Custom Strategy" in md_manual
    assert "Manual / Custom Strategy" in html_manual


def test_explainability_validation_data_inclusion(mock_strategy, mock_backtest_result):
    """6. Validation data inclusion (fitness, rank, elimination details)."""
    vr = _make_validation_dict(
        fitness=0.789,
        rank=2,
        total_strategies=15,
        elimination_result={
            "passed": True,
            "failed_rules": [],
            "config_snapshot": {
                "min_trade_count": 5,
                "min_profit_factor": 0.50,
                "max_drawdown_pnl": None,
                "min_win_rate": False,
            }
        }
    )
    md = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr)
    html_out = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr)

    assert "### Ranking & Validation Evidence" in md
    assert "**Fitness Score:** 0.789" in md
    assert "**Rank:** 2 / 15" in md
    assert "**Elimination Status:** PASSED" in md
    assert "**Thresholds Applied:** min_trade_count=5, min_profit_factor=0.5" in md

    assert "Ranking &amp; Validation Evidence" in html_out
    assert "Fitness Score" in html_out
    assert "0.789" in html_out
    assert "Rank" in html_out
    assert "2 / 15" in html_out
    assert "class=\"value status-passed\"" in html_out
    assert "PASSED" in html_out
    assert "min_trade_count=5, min_profit_factor=0.5" in html_out


def test_explainability_html_escaping_validation(mock_strategy, mock_backtest_result):
    """7. HTML escaping validation for malicious parameters."""
    malicious_strategy = Strategy(
        name="<script>alert('name')</script>",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": "<img src=x>"}, operator=">")]
        ),
    )
    provenance = {
        "generator": "<svg onload=1>",
        "generator_version": "1.0",
        "random_seed": "<b>seed</b>",
    }
    vr = _make_validation_dict(
        fitness="<iframe src=y>",
        rank="<script>alert(2)</script>",
        elimination_result={
            "passed": False,
            "failed_rules": ["<script>alert('failed')</script>"],
            "config_snapshot": {
                "min_trade_count": "<script>alert('threshold')</script>",
            },
            "warnings": ["<script>alert('warning')</script>"],
        }
    )

    html_out = generate_html_report(malicious_strategy, mock_backtest_result, provenance=provenance, validation_result=vr)

    assert "<script>alert('name')</script>" not in html_out
    assert "<img src=x>" not in html_out
    assert "<svg onload=1>" not in html_out
    assert "<b>seed</b>" not in html_out
    assert "<iframe src=y>" not in html_out
    assert "<script>alert(2)</script>" not in html_out
    assert "<script>alert('failed')</script>" not in html_out
    assert "<script>alert('threshold')</script>" not in html_out
    assert "<script>alert('warning')</script>" not in html_out

    assert "&lt;script&gt;alert(&#x27;name&#x27;)&lt;/script&gt;" in html_out
    assert "&lt;img src=x&gt;" in html_out
    assert "&lt;svg onload=1&gt;" in html_out
    assert "&lt;b&gt;seed&lt;/b&gt;" in html_out
    assert "&lt;iframe src=y&gt;" in html_out
    assert "&lt;script&gt;alert(2)&lt;/script&gt;" in html_out
    assert "&lt;script&gt;alert(&#x27;failed&#x27;)&lt;/script&gt;" in html_out
    assert "&lt;script&gt;alert(&#x27;threshold&#x27;)&lt;/script&gt;" in html_out
    assert "&lt;script&gt;alert(&#x27;warning&#x27;)&lt;/script&gt;" in html_out


def test_explainability_markdown_sanitizes_dynamic_strings(mock_backtest_result):
    """Markdown explainability must sanitize dynamic strategy and validation strings."""
    malicious_strategy = Strategy(
        name="<script>alert('name')</script>",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": "<img src=x>"}, operator=">")]
        ),
    )
    provenance = {
        "generator": "<svg onload=1>",
        "generator_version": "1.0",
        "random_seed": "<b>seed</b>",
    }
    vr = _make_validation_dict(
        fitness="<iframe src=y>",
        rank="<script>alert(2)</script>",
        elimination_result={
            "passed": False,
            "failed_rules": ["<script>alert('failed')</script>"],
            "config_snapshot": {
                "min_trade_count": "<script>alert('threshold')</script>",
            },
            "warnings": ["<script>alert('warning')</script>"],
        }
    )

    md = generate_markdown_report(
        malicious_strategy,
        mock_backtest_result,
        provenance=provenance,
        validation_result=vr,
    )
    explainability_md = md.split("## Strategy Profile", 1)[0]

    assert "<script>alert('name')</script>" not in explainability_md
    assert "<img src=x>" not in explainability_md
    assert "<svg onload=1>" not in explainability_md
    assert "<b>seed</b>" not in explainability_md
    assert "<iframe src=y>" not in explainability_md
    assert "<script>alert(2)</script>" not in explainability_md
    assert "<script>alert('failed')</script>" not in explainability_md
    assert "<script>alert('threshold')</script>" not in explainability_md
    assert "<script>alert('warning')</script>" not in explainability_md
    assert "&lt;script&gt;alert('name')&lt;/script&gt;" in explainability_md
    assert "&lt;img src=x&gt;" in explainability_md
    assert "&lt;svg onload=1&gt;" in explainability_md
    assert "&lt;b&gt;seed&lt;/b&gt;" in explainability_md


def test_explainability_optional_validation_fields_exclusion(mock_strategy, mock_backtest_result):
    """8. Optional validation fields exclusion."""
    # 8.1 validation_result is None
    md_none = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=None)
    html_none = generate_html_report(mock_strategy, mock_backtest_result, validation_result=None)

    assert "Ranking & Validation Evidence" not in md_none
    assert "Ranking &amp; Validation Evidence" not in html_none

    # 8.2 validation_result has no fitness or rank
    vr_empty = _make_validation_dict(fitness=None, rank=None)
    md_empty = generate_markdown_report(mock_strategy, mock_backtest_result, validation_result=vr_empty)
    html_empty = generate_html_report(mock_strategy, mock_backtest_result, validation_result=vr_empty)

    assert "Fitness Score" not in md_empty
    assert "**Rank:**" not in md_empty
    assert "Fitness Score" not in html_empty
    assert '<li><span class="label">Rank</span>' not in html_empty


def test_explainability_risk_management_parameters(mock_strategy, mock_backtest_result):
    """9. Risk management parameters rendering."""
    # Configured risk parameters
    mock_strategy.risk_management.stop_loss_ticks = 15.0
    mock_strategy.risk_management.stop_loss_pct = 0.015
    mock_strategy.risk_management.take_profit_ticks = 40.0
    mock_strategy.risk_management.take_profit_pct = None
    mock_strategy.risk_management.close_end_of_session = True
    mock_strategy.risk_management.session_end_time = "13:45"

    md = generate_markdown_report(mock_strategy, mock_backtest_result)
    html_out = generate_html_report(mock_strategy, mock_backtest_result)

    assert "Stop-Loss: 15.0 ticks & 1.50%" in md
    assert "Take-Profit: 40.0 ticks" in md
    assert "Session exit: Yes (13:45)" in md

    assert "Stop-Loss: 15.0 ticks &amp; 1.50%" in html_out
    assert "Take-Profit: 40.0 ticks" in html_out
    assert "Session exit: Yes (13:45)" in html_out
