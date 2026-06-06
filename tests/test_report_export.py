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
