"""Tests for multi-instrument report generation — Task 032C."""

from __future__ import annotations

import pandas as pd
import pytest

from core.models.strategy import Strategy, StrategyBlock, Condition
from core.models.backtest_result import BacktestResult
from app.services.multi_instrument_service import (
    MultiInstrumentBacktestResult,
    PerInstrumentBacktestResult,
)
from reports.generator import generate_markdown_report, generate_html_report


@pytest.fixture
def mock_strategy() -> Strategy:
    return Strategy(
        name="multi_test_strat",
        long_entry=StrategyBlock(conditions=[]),
    )


@pytest.fixture
def mock_backtest_result() -> BacktestResult:
    return BacktestResult(
        trades=[],
        metrics={"total_pnl": 100.0, "profit_factor": 1.5, "max_drawdown_pnl": 50.0},
        assumptions={"execution_model": "next_bar_open"},
        warnings=[],
    )


@pytest.fixture
def mock_mir() -> MultiInstrumentBacktestResult:
    return MultiInstrumentBacktestResult(
        instrument_count=2,
        success_count=1,
        failure_count=1,
        aggregate_metrics={
            "total_trades_sum": 5,
            "mean_total_pnl": 200.0,
            "median_total_pnl": 200.0,
            "min_total_pnl": 200.0,
            "max_total_pnl": 200.0,
            "worst_max_drawdown_pnl": 100.0,
            "mean_profit_factor": 2.0,
        },
        per_instrument=[
            PerInstrumentBacktestResult(
                label="ES_Success",
                success=True,
                metrics={"total_pnl": 200.0, "total_trades": 5, "profit_factor": 2.0, "max_drawdown_pnl": 100.0},
                warnings=[],
                error_message=None,
            ),
            PerInstrumentBacktestResult(
                label="NQ_Fail",
                success=False,
                metrics={},
                warnings=[],
                error_message="ZeroDivisionError: float division by zero",
            ),
        ],
        warnings=["One instrument failed."],
        assumptions={},
    )


def test_markdown_report_without_multi_instrument_unchanged_or_no_section(
    mock_strategy, mock_backtest_result
):
    md = generate_markdown_report(mock_strategy, mock_backtest_result)
    assert "Multi-Instrument Evidence" not in md
    assert "Strategy Logic" in md
    assert "Validation Evidence" in md


def test_markdown_report_includes_multi_instrument_evidence(
    mock_strategy, mock_backtest_result, mock_mir
):
    md = generate_markdown_report(
        mock_strategy, mock_backtest_result, multi_instrument_result=mock_mir
    )
    assert "Multi-Instrument Evidence" in md
    assert "Aggregate Metrics" in md
    assert "Per-Instrument Breakdown" in md
    assert "ES_Success" in md
    assert "NQ_Fail" in md


def test_html_report_includes_multi_instrument_evidence(
    mock_strategy, mock_backtest_result, mock_mir
):
    html_out = generate_html_report(
        mock_strategy, mock_backtest_result, multi_instrument_result=mock_mir
    )
    assert "Multi-Instrument Evidence" in html_out
    assert "Aggregate Metrics" in html_out
    assert "Per-Instrument Breakdown" in html_out
    assert "ES_Success" in html_out
    assert "NQ_Fail" in html_out


def test_multi_instrument_report_includes_aggregate_metrics(
    mock_strategy, mock_backtest_result, mock_mir
):
    md = generate_markdown_report(
        mock_strategy, mock_backtest_result, multi_instrument_result=mock_mir
    )
    assert "1 passed / 1 failed" in md
    assert "Total: 2" in md
    assert "Median Total PnL" in md
    assert "$200.00" in md
    assert "Worst Max Drawdown" in md


def test_multi_instrument_report_includes_success_and_failure_rows(
    mock_strategy, mock_backtest_result, mock_mir
):
    md = generate_markdown_report(
        mock_strategy, mock_backtest_result, multi_instrument_result=mock_mir
    )
    # Success row check
    assert "| ES_Success | PASSED | 5 | $200.00 | 2.00 | $100.00 | - |" in md
    # Failure row check
    assert "| NQ_Fail | FAILED | - | - | - | - | ZeroDivisionError: float division by zero |" in md


def test_multi_instrument_report_includes_warnings(
    mock_strategy, mock_backtest_result, mock_mir
):
    md = generate_markdown_report(
        mock_strategy, mock_backtest_result, multi_instrument_result=mock_mir
    )
    assert "One instrument failed." in md

    html_out = generate_html_report(
        mock_strategy, mock_backtest_result, multi_instrument_result=mock_mir
    )
    assert "One instrument failed." in html_out


def test_multi_instrument_html_escapes_dynamic_text(
    mock_strategy, mock_backtest_result
):
    malicious_mir = MultiInstrumentBacktestResult(
        instrument_count=1,
        success_count=0,
        failure_count=1,
        aggregate_metrics={},
        per_instrument=[
            PerInstrumentBacktestResult(
                label="<script>alert(1)</script>",
                success=False,
                error_message="<img src=x onerror=alert(2)>",
            )
        ],
        warnings=["<div id='bad'>XSS</div>"],
        assumptions={},
    )
    html_out = generate_html_report(
        mock_strategy, mock_backtest_result, multi_instrument_result=malicious_mir
    )
    
    assert "<script>alert(1)</script>" not in html_out
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_out

    assert "<img src=x onerror=alert(2)>" not in html_out
    assert "&lt;img src=x onerror=alert(2)&gt;" in html_out

    assert "<div id='bad'>XSS</div>" not in html_out
    assert "&lt;div id=&#x27;bad&#x27;&gt;XSS&lt;/div&gt;" in html_out


def test_multi_instrument_report_preserves_financial_disclaimer(
    mock_strategy, mock_backtest_result, mock_mir
):
    md = generate_markdown_report(
        mock_strategy, mock_backtest_result, multi_instrument_result=mock_mir
    )
    assert "Backtested performance does not guarantee future results." in md

    html_out = generate_html_report(
        mock_strategy, mock_backtest_result, multi_instrument_result=mock_mir
    )
    assert "Backtested performance does not guarantee future results." in html_out


def test_multi_instrument_report_preserves_validation_evidence(
    mock_strategy, mock_backtest_result, mock_mir
):
    vr = {"elimination_result": {"passed": True}}
    md = generate_markdown_report(
        mock_strategy, mock_backtest_result, validation_result=vr, multi_instrument_result=mock_mir
    )
    assert "Validation Evidence" in md
    assert "PASSED" in md

    html_out = generate_html_report(
        mock_strategy, mock_backtest_result, validation_result=vr, multi_instrument_result=mock_mir
    )
    assert "Validation Evidence" in html_out
    assert "PASSED" in html_out


def test_multi_instrument_markdown_escapes_pipes_in_table(
    mock_strategy, mock_backtest_result
):
    mir = MultiInstrumentBacktestResult(
        instrument_count=1, success_count=0, failure_count=1,
        aggregate_metrics={},
        per_instrument=[
            PerInstrumentBacktestResult(
                label="ES|M24",
                success=False,
                error_message="Error | Value",
            )
        ],
        warnings=[],
        assumptions={},
    )
    md = generate_markdown_report(mock_strategy, mock_backtest_result, multi_instrument_result=mir)
    
    assert "| ES\\|M24 | FAILED | - | - | - | - | Error \\| Value |" in md


def test_multi_instrument_markdown_removes_newlines_in_table_and_warnings(
    mock_strategy, mock_backtest_result
):
    mir = MultiInstrumentBacktestResult(
        instrument_count=1, success_count=0, failure_count=1,
        aggregate_metrics={},
        per_instrument=[
            PerInstrumentBacktestResult(
                label="ES\n123",
                success=False,
                error_message="Line1\nLine2",
            )
        ],
        warnings=["Warning1\nWarning2"],
        assumptions={},
    )
    md = generate_markdown_report(mock_strategy, mock_backtest_result, multi_instrument_result=mir)
    
    assert "| ES 123 | FAILED | - | - | - | - | Line1 Line2 |" in md
    assert "- Warning1 Warning2" in md


def test_multi_instrument_html_escaping_still_passes(
    mock_strategy, mock_backtest_result
):
    mir = MultiInstrumentBacktestResult(
        instrument_count=1, success_count=0, failure_count=1,
        aggregate_metrics={},
        per_instrument=[
            PerInstrumentBacktestResult(
                label="ES<script>",
                success=False,
                error_message="Error<img src=x>",
            )
        ],
        warnings=["Warning<br>"],
        assumptions={},
    )
    html_out = generate_html_report(mock_strategy, mock_backtest_result, multi_instrument_result=mir)
    
    assert "ES&lt;script&gt;" in html_out
    assert "Error&lt;img src=x&gt;" in html_out
    assert "Warning&lt;br&gt;" in html_out

