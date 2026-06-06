"""Final 057 validation expansion acceptance smoke tests — Task 057M-Impl.

Covers bootstrap MC + WF equity full chain across pipeline/widget/report/UI.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch

from core.models.strategy import Condition, Strategy, StrategyBlock
from app.services.validation_pipeline_service import (
    PipelineConfig,
    run_validation_pipeline,
)
from app.widgets.validation_summary import ValidationSummary
from reports import generate_markdown_report, generate_html_report
from PySide6.QtWidgets import QApplication, QLabel
from app.ui.main_window import MainWindow


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_df(n_bars: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(123)
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="1min")
    close = 100.0 + np.cumsum(rng.normal(0.01, 0.4, n_bars))
    close = np.maximum(close, 10.0)
    noise = rng.uniform(0.2, 1.0, n_bars)
    return pd.DataFrame({
        "datetime": times,
        "open":  close - noise * 0.3,
        "high":  close + noise,
        "low":   close - noise,
        "close": close,
        "volume": rng.integers(500, 5000, n_bars),
    })


def _make_strategy() -> Strategy:
    return Strategy(
        name="acceptance_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator="<"),
        ], logic="AND"),
    )


def _make_backtest_result():
    from core.models.backtest_result import BacktestResult, Trade
    return BacktestResult(
        trades=[
            Trade(pd.Timestamp("2024-01-01 09:30"), pd.Timestamp("2024-01-01 10:00"),
                  "long", 100.0, 105.0, 1, 5.0, "signal"),
        ],
        metrics={"total_pnl": 5.0, "profit_factor": 1.0, "total_trades": 1},
        assumptions={"execution_model": "next_bar_open"},
        warnings=[],
    )


def _make_strategy_for_report():
    return Strategy(
        name="smoke_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 20}, operator=">"),
        ]),
    )


def _make_rich_validation_dict():
    return {
        "split_metadata": {"train_rows": 60, "validation_rows": 20, "oos_rows": 20},
        "baseline_metrics": {"total_pnl": 100.0, "profit_factor": 1.5, "total_trades": 4},
        "stress_results": [],
        "monte_carlo_summary": {"iterations": 15,
            "percentile_summary": {"total_pnl": {"p5": 1000.0, "p50": 5000.0, "p95": 9000.0}},
            "worst_case": {"total_pnl": 1000.0}},
        "bootstrap_monte_carlo_result": {
            "test_name": "bootstrap",
            "iterations": 200,
            "stability_score": 0.85,
            "confidence_intervals": {
                "total_pnl": {"ci_lower": 1200.0, "ci_upper": 9800.0, "ci_mean": 5400.0},
            },
        },
        "walk_forward_summary": {
            "window_count": 2, "pass_count": 1, "pass_rate": 0.5,
            "windows": [
                {"index": 0, "equity_curve": [100000.0, 105000.0], "passed": True},
                {"index": 1, "equity_curve": [100000.0, 98000.0], "passed": False},
            ],
        },
        "elimination_result": {"passed": True, "failed_rules": []},
    }


# ---------------------------------------------------------------------------
# Bootstrap pipeline chain
# ---------------------------------------------------------------------------


def test_bootstrap_pipeline_chain():
    """Opt-in pipeline must produce bootstrap CI result."""
    df = _make_df(200)
    strat = _make_strategy()
    cfg = PipelineConfig(run_bootstrap_monte_carlo=True, bootstrap_iterations=50)
    result = run_validation_pipeline(df, strat, config=cfg, commission=2.0)
    assert result.bootstrap_monte_carlo_result is not None
    assert "confidence_intervals" in result.bootstrap_monte_carlo_result


def test_bootstrap_widget_chain():
    """Widget must render bootstrap card when CI is present."""
    qapp = QApplication.instance() or QApplication(["pytest"])
    widget = ValidationSummary()
    widget.update_from_result(_make_rich_validation_dict())
    texts = []
    for i in range(widget._layout.count()):
        item = widget._layout.itemAt(i)
        if item and item.widget():
            for child in item.widget().findChildren(QLabel):
                texts.append(str(child.text()))
    text = "\n".join(texts)
    assert "Bootstrap MC" in text


def test_bootstrap_report_chain():
    """Markdown + HTML must both render bootstrap output."""
    strat = _make_strategy_for_report()
    bt = _make_backtest_result()
    vr = _make_rich_validation_dict()
    md = generate_markdown_report(strat, bt, validation_result=vr)
    html_out = generate_html_report(strat, bt, validation_result=vr)
    assert "Bootstrap MC" in md
    assert "Bootstrap MC" in html_out


@patch("app.ui.main_window.run_validation_pipeline")
def test_bootstrap_ui_chain(mock_run, monkeypatch):
    """UI controls must pass bootstrap settings into PipelineConfig."""
    app = QApplication.instance() or QApplication(["pytest"])
    with monkeypatch.context() as m:
        m.setattr("app.ui.main_window.QApplication.instance", lambda: app)
    window = MainWindow()
    window.bootstrap_checkbox.setChecked(True)
    window.bootstrap_iter_spin.setValue(500)
    window.bootstrap_conf_spin.setValue(0.90)
    window._handle_run()
    window.close()
    mock_run.assert_called_once()
    config = mock_run.call_args.kwargs["config"]
    assert config.run_bootstrap_monte_carlo is True
    assert config.bootstrap_iterations == 500
    assert config.bootstrap_confidence_level == 0.90


# ---------------------------------------------------------------------------
# WF equity chain
# ---------------------------------------------------------------------------


def test_wf_equity_widget_chain():
    """Widget must render WF Equity Summary when equity is present."""
    qapp = QApplication.instance() or QApplication(["pytest"])
    widget = ValidationSummary()
    widget.update_from_result(_make_rich_validation_dict())
    texts = []
    for i in range(widget._layout.count()):
        item = widget._layout.itemAt(i)
        if item and item.widget():
            for child in item.widget().findChildren(QLabel):
                texts.append(str(child.text()))
    text = "\n".join(texts)
    assert "WF Equity Summary" in text


def test_wf_equity_report_chain():
    """Markdown + HTML must both render WF equity table."""
    strat = _make_strategy_for_report()
    bt = _make_backtest_result()
    vr = _make_rich_validation_dict()
    md = generate_markdown_report(strat, bt, validation_result=vr)
    html_out = generate_html_report(strat, bt, validation_result=vr)
    assert "WF Equity by Window" in md
    assert "WF Equity by Window" in html_out


# ---------------------------------------------------------------------------
# Default and empty behavior
# ---------------------------------------------------------------------------


def test_default_pipeline_no_extra_output():
    """Default PipelineConfig must not produce bootstrap or WF equity."""
    df = _make_df(200)
    strat = _make_strategy()
    result = run_validation_pipeline(df, strat, commission=2.0)
    assert result.bootstrap_monte_carlo_result is None
    wf = result.walk_forward_summary or {}
    assert "windows" not in wf


def test_empty_ci_and_equity_omitted():
    """Missing bootstrap CI or empty WF equity must not crash widget/reports.

    Asserts omission across all three surfaces: widget, Markdown, HTML."""
    qapp = QApplication.instance() or QApplication(["pytest"])
    result = dict(_make_rich_validation_dict())
    result["bootstrap_monte_carlo_result"] = {
        "test_name": "bootstrap", "iterations": 200, "confidence_intervals": {},
    }
    result["walk_forward_summary"] = {"window_count": 1, "pass_count": 0, "pass_rate": 0.0,
        "windows": [{"index": 0, "equity_curve": None, "passed": False}]}

    # Widget
    widget = ValidationSummary()
    widget.update_from_result(result)
    texts = []
    for i in range(widget._layout.count()):
        item = widget._layout.itemAt(i)
        if item and item.widget():
            for child in item.widget().findChildren(QLabel):
                texts.append(str(child.text()))
    text = "\n".join(texts)
    assert "Bootstrap MC" not in text
    assert "WF Equity Summary" not in text

    # Markdown
    strat = _make_strategy_for_report()
    bt = _make_backtest_result()
    md = generate_markdown_report(strat, bt, validation_result=result)
    assert "Bootstrap MC" not in md
    assert "WF Equity by Window" not in md

    # HTML
    html_out = generate_html_report(strat, bt, validation_result=result)
    assert "Bootstrap MC" not in html_out
    assert "WF Equity by Window" not in html_out
