"""Acceptance smoke tests for remove-best-N-trades stress feature — Task 056I.

Verifies the end-to-end chain:
  PipelineConfig -> pipeline -> stress result -> widget display -> report display -> UI controls
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

# For UI control tests
from PySide6.QtWidgets import QApplication
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


# ---------------------------------------------------------------------------
# Pipeline acceptance
# ---------------------------------------------------------------------------


def test_pipeline_enabled_produces_remove_best_n_result():
    """Enabled pipeline config must produce a remove_best_n_trades stress result."""
    df = _make_df(200)
    strat = _make_strategy()

    cfg = PipelineConfig(
        run_remove_best_n_trades_stress=True,
        remove_best_n_trades_n=2,
        remove_best_n_trades_degradation_threshold=0.50,
    )
    result = run_validation_pipeline(df, strat, config=cfg, commission=2.0)

    test_names = [s["test_name"] for s in result.stress_results]
    assert "remove_best_n_trades" in test_names

    n_trades = next(s for s in result.stress_results if s["test_name"] == "remove_best_n_trades")
    assert "assumptions" in n_trades
    assert n_trades["assumptions"]["n"] == 2
    assert "pnl_loss_ratio" in n_trades["assumptions"]
    assert "warnings" in n_trades
    assert "threshold" in n_trades


def test_pipeline_default_omits_remove_best_n():
    """Default PipelineConfig must not include remove_best_n_trades."""
    df = _make_df(200)
    strat = _make_strategy()

    result = run_validation_pipeline(df, strat, commission=2.0)
    test_names = [s["test_name"] for s in result.stress_results]
    assert "remove_best_n_trades" not in test_names


# ---------------------------------------------------------------------------
# Widget display acceptance
# ---------------------------------------------------------------------------


def test_widget_renders_remove_best_n_detail():
    """ValidationSummary must show remove_best_n detail sub-lines."""
    qapp = QApplication.instance() or QApplication(["pytest"])

    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0, "total_trades": 4},
        "stress_results": [
            {"test_name": "remove_best_n_trades", "passed": False,
             "degradation": {"total_pnl": -0.83},
             "assumptions": {
                 "n": 2, "removed_count": 2, "surviving_count": 2,
                 "pnl_loss_ratio": 0.833,
             },
             "warnings": ["Test warning message."],
             "threshold": {"max_pnl_loss": 0.30},
            },
        ],
        "elimination_result": {"passed": True, "failed_rules": []},
    }
    widget = ValidationSummary()
    widget.update_from_result(result)

    # Collect text from QLabels (same pattern as test_validation_summary.py).
    from PySide6.QtWidgets import QLabel
    texts = []
    for i in range(widget._layout.count()):
        item = widget._layout.itemAt(i)
        if item and item.widget():
            for child in item.widget().findChildren(QLabel):
                texts.append(str(child.text()))
    text = "\n".join(texts)

    assert "remove_best_n_trades" in text
    assert "Removed:" in text
    assert "n=2" in text
    assert "pnl_loss=0.833" in text
    assert "Test warning message." in text


# ---------------------------------------------------------------------------
# Report acceptance
# ---------------------------------------------------------------------------


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


def _make_validation_with_remove_best_n():
    return {
        "split_metadata": {"train_rows": 60, "validation_rows": 20, "oos_rows": 20},
        "baseline_metrics": {"total_pnl": 100.0, "profit_factor": 1.5, "total_trades": 4},
        "stress_results": [
            {"test_name": "remove_best_n_trades", "passed": False,
             "degradation": {"total_pnl": -0.83},
             "assumptions": {
                 "n": 2, "removed_count": 2, "surviving_count": 2,
                 "pnl_loss_ratio": 0.833,
             },
             "warnings": ["Acceptance warning."],
             "threshold": {"max_pnl_loss": 0.30},
            },
        ],
        "elimination_result": {"passed": True, "failed_rules": []},
    }


def test_markdown_report_includes_remove_best_n():
    """Markdown report must include remove_best_n detail lines."""
    strat = _make_strategy_for_report()
    bt_result = _make_backtest_result()
    vr = _make_validation_with_remove_best_n()

    md = generate_markdown_report(strat, bt_result, validation_result=vr)

    assert "remove_best_n_trades" in md
    assert "Removed:" in md
    assert "n=2" in md
    assert "pnl_loss=0.833" in md
    assert "WARNING:" in md
    assert "Acceptance warning." in md


def test_html_report_includes_remove_best_n():
    """HTML report must include remove_best_n detail lines."""
    strat = _make_strategy_for_report()
    bt_result = _make_backtest_result()
    vr = _make_validation_with_remove_best_n()

    html_out = generate_html_report(strat, bt_result, validation_result=vr)

    assert "remove_best_n_trades" in html_out
    assert "stress-detail" in html_out
    assert "Removed:" in html_out
    assert "n=2" in html_out
    assert "Acceptance warning." in html_out


def test_html_report_escapes_stress_detail():
    """HTML report must escape malicious stress detail values."""
    strat = _make_strategy_for_report()
    bt_result = _make_backtest_result()
    vr = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0},
        "stress_results": [
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
        ],
        "elimination_result": {"passed": True, "failed_rules": []},
    }

    html_out = generate_html_report(strat, bt_result, validation_result=vr)

    assert "<script>x</script>" not in html_out
    assert "<img src=x>" not in html_out
    assert "<b>bad</b>" not in html_out
    assert "&lt;script&gt;x&lt;/script&gt;" in html_out
    assert "&lt;img src=x&gt;" in html_out
    assert "&lt;b&gt;bad&lt;/b&gt;" in html_out


# ---------------------------------------------------------------------------
# UI control acceptance
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
def test_ui_enabled_config_reaches_pipeline(mock_run, main_window):
    """UI controls must pass enabled + custom values into PipelineConfig."""
    main_window.remove_best_n_checkbox.setChecked(True)
    main_window.remove_best_n_n_spin.setValue(7)
    main_window.remove_best_n_threshold_spin.setValue(0.15)

    main_window._handle_run()

    mock_run.assert_called_once()
    config = mock_run.call_args.kwargs["config"]
    assert config.run_remove_best_n_trades_stress is True
    assert config.remove_best_n_trades_n == 7
    assert config.remove_best_n_trades_degradation_threshold == 0.15


@patch("app.ui.main_window.run_validation_pipeline")
def test_ui_disabled_default_omits_stress(mock_run, main_window):
    """UI controls unchecked must pass run_remove_best_n_trades_stress=False."""
    main_window.remove_best_n_checkbox.setChecked(False)

    main_window._handle_run()

    mock_run.assert_called_once()
    config = mock_run.call_args.kwargs["config"]
    assert config.run_remove_best_n_trades_stress is False
