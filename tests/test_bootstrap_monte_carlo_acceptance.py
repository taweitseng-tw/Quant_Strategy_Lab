"""Bootstrap Monte Carlo feature acceptance smoke tests — Task 057G-Impl.

Covers the full chain: PipelineConfig -> pipeline -> widget -> report -> UI.
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


def _make_validation_with_bootstrap():
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
                "profit_factor": {"ci_lower": 1.15, "ci_upper": 2.80, "ci_mean": 1.95},
                "max_drawdown_pnl": {"ci_lower": 500.0, "ci_upper": 12000.0, "ci_mean": 4200.0},
            },
        },
        "elimination_result": {"passed": True, "failed_rules": []},
    }


# ---------------------------------------------------------------------------
# Pipeline acceptance
# ---------------------------------------------------------------------------


def test_default_pipeline_omits_bootstrap():
    """Default PipelineConfig must not run bootstrap."""
    df = _make_df(200)
    strat = _make_strategy()
    result = run_validation_pipeline(df, strat, commission=2.0)
    assert result.bootstrap_monte_carlo_result is None
    assert result.config_snapshot["run_bootstrap_monte_carlo"] is False


def test_optin_pipeline_produces_bootstrap():
    """Opt-in PipelineConfig must produce bootstrap_monte_carlo_result."""
    df = _make_df(200)
    strat = _make_strategy()
    cfg = PipelineConfig(run_bootstrap_monte_carlo=True, bootstrap_iterations=50)
    result = run_validation_pipeline(df, strat, config=cfg, commission=2.0)
    assert result.bootstrap_monte_carlo_result is not None
    br = result.bootstrap_monte_carlo_result
    assert br["test_name"] == "bootstrap"
    assert "confidence_intervals" in br
    assert "total_pnl" in br["confidence_intervals"]


# ---------------------------------------------------------------------------
# Widget acceptance
# ---------------------------------------------------------------------------


def test_widget_shows_bootstrap_when_present():
    """Widget must show Bootstrap MC card when CI data is present."""
    qapp = QApplication.instance() or QApplication(["pytest"])
    result = _make_validation_with_bootstrap()
    widget = ValidationSummary()
    widget.update_from_result(result)

    texts = []
    for i in range(widget._layout.count()):
        item = widget._layout.itemAt(i)
        if item and item.widget():
            for child in item.widget().findChildren(QLabel):
                texts.append(str(child.text()))
    text = "\n".join(texts)

    assert "Bootstrap MC" in text
    assert "1,200" in text
    assert "9,800" in text


def test_widget_omits_bootstrap_when_ci_empty():
    """Widget must NOT show Bootstrap MC when CI is empty."""
    qapp = QApplication.instance() or QApplication(["pytest"])
    result = dict(_make_validation_with_bootstrap())
    result["bootstrap_monte_carlo_result"] = {
        "test_name": "bootstrap", "iterations": 200, "confidence_intervals": {},
    }
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


# ---------------------------------------------------------------------------
# Report acceptance
# ---------------------------------------------------------------------------


def test_markdown_shows_bootstrap():
    """Markdown report must show Bootstrap MC."""
    strat = _make_strategy_for_report()
    bt = _make_backtest_result()
    vr = _make_validation_with_bootstrap()
    md = generate_markdown_report(strat, bt, validation_result=vr)
    assert "**Bootstrap MC**" in md
    assert "1,200" in md


def test_html_shows_bootstrap():
    """HTML report must show Bootstrap MC."""
    strat = _make_strategy_for_report()
    bt = _make_backtest_result()
    vr = _make_validation_with_bootstrap()
    html_out = generate_html_report(strat, bt, validation_result=vr)
    assert "<b>Bootstrap MC</b>" in html_out
    assert "1,200" in html_out


def test_markdown_omits_bootstrap_when_ci_empty():
    """Markdown must omit Bootstrap MC when CI is empty."""
    strat = _make_strategy_for_report()
    bt = _make_backtest_result()
    vr = dict(_make_validation_with_bootstrap())
    vr["bootstrap_monte_carlo_result"] = {
        "test_name": "bootstrap", "iterations": 200, "confidence_intervals": {},
    }
    md = generate_markdown_report(strat, bt, validation_result=vr)
    assert "**Bootstrap MC**" not in md


def test_html_omits_bootstrap_when_ci_empty():
    """HTML must omit Bootstrap MC when CI is empty."""
    strat = _make_strategy_for_report()
    bt = _make_backtest_result()
    vr = dict(_make_validation_with_bootstrap())
    vr["bootstrap_monte_carlo_result"] = {
        "test_name": "bootstrap", "iterations": 200, "confidence_intervals": {},
    }
    html_out = generate_html_report(strat, bt, validation_result=vr)
    assert "<b>Bootstrap MC</b>" not in html_out


# ---------------------------------------------------------------------------
# UI controls acceptance
# ---------------------------------------------------------------------------


@pytest.fixture
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def main_window(app):
    window = MainWindow()
    yield window
    window.close()


@patch("app.ui.main_window.run_validation_pipeline")
def test_ui_controls_pass_bootstrap_to_pipeline(mock_run, main_window):
    """UI bootstrap controls must pass enabled + custom values to PipelineConfig."""
    main_window.bootstrap_checkbox.setChecked(True)
    main_window.bootstrap_iter_spin.setValue(500)
    main_window.bootstrap_conf_spin.setValue(0.90)
    main_window._handle_run()

    mock_run.assert_called_once()
    config = mock_run.call_args.kwargs["config"]
    assert config.run_bootstrap_monte_carlo is True
    assert config.bootstrap_iterations == 500
    assert config.bootstrap_confidence_level == 0.90


@patch("app.ui.main_window.run_validation_pipeline")
def test_ui_disabled_bootstrap_default(mock_run, main_window):
    """UI bootstrap controls disabled by default must pass False."""
    main_window.bootstrap_checkbox.setChecked(False)
    main_window._handle_run()

    mock_run.assert_called_once()
    config = mock_run.call_args.kwargs["config"]
    assert config.run_bootstrap_monte_carlo is False
