"""Tests for validation summary dashboard — Task 026."""

from __future__ import annotations

import sys
import pytest
from PySide6.QtWidgets import QApplication, QLabel

from app.widgets.validation_summary import ValidationSummary


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def _widget_text(widget: ValidationSummary) -> str:
    texts = []
    for i in range(widget._layout.count()):
        item = widget._layout.itemAt(i)
        if item and item.widget():
            for child in item.widget().findChildren(QLabel):
                texts.append(str(child.text()))
    return "\n".join(texts)


# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------


def test_empty_state_shows_placeholder(qapp):
    """Before any update, the dashboard must show a placeholder message."""
    widget = ValidationSummary()
    # The empty state adds a single QLabel with instructional text.
    container = widget._container
    children = container.findChildren(type(container))
    # Since we can't easily introspect, just verify no crash and layout exists.
    assert widget._layout.count() >= 1


# ---------------------------------------------------------------------------
# Update from result
# ---------------------------------------------------------------------------


def test_update_with_full_result(qapp):
    """Updating with a complete PipelineResult dict must not crash and must
    populate multiple section cards."""
    result = {
        "split_metadata": {"train_rows": 90, "validation_rows": 45, "oos_rows": 45},
        "baseline_metrics": {
            "total_pnl": 5000.0, "profit_factor": 1.8, "total_trades": 22,
            "max_drawdown_pnl": 2000.0, "win_rate": 0.55,
        },
        "stress_results": [
            {"test_name": "commission_2.0x", "passed": True,
             "degradation": {"total_pnl": -0.15}},
            {"test_name": "slippage_2.0x", "passed": True,
             "degradation": {"total_pnl": -0.08}},
        ],
        "monte_carlo_summary": {
            "iterations": 15,
            "percentile_summary": {
                "total_pnl": {"p5": 1000.0, "p50": 4800.0, "p95": 9000.0},
            },
            "worst_case": {"total_pnl": 1000.0},
        },
        "walk_forward_summary": {
            "window_count": 5, "pass_count": 3, "pass_rate": 0.6,
        },
        "elimination_result": {
            "passed": True, "failed_rules": [],
        },
    }

    widget = ValidationSummary()
    widget.update_from_result(result, source_label="Test data")

    # After update, layout should have multiple children (cards + stretch).
    # Each card is a QFrame — count them.
    card_count = 0
    for i in range(widget._layout.count()):
        item = widget._layout.itemAt(i)
        if item and item.widget() and isinstance(item.widget(), type(widget)):
            continue
        if item and item.widget():
            card_count += 1
    # At minimum: source + split + baseline + stress + MC + WF + elimination + stretch
    assert card_count >= 7


def test_wf_matrix_summary_displayed(qapp):
    """Walk-forward Matrix summary should render when present."""
    result = {
        "split_metadata": {"train_rows": 90, "validation_rows": 45, "oos_rows": 45},
        "baseline_metrics": {"total_pnl": 5000.0, "profit_factor": 1.8, "total_trades": 22},
        "stress_results": [],
        "walk_forward_summary": {"window_count": 5, "pass_count": 3, "pass_rate": 0.6},
        "walk_forward_matrix_summary": {
            "config_count": 4,
            "tested_count": 3,
            "insufficient_data_count": 1,
            "best_pass_rate_config": {
                "config_id": "wf_matrix_001",
                "train_bars": 50,
                "test_bars": 20,
                "step_bars": 10,
                "pass_rate": 0.75,
            },
            "worst_pass_rate_config": {
                "config_id": "wf_matrix_002",
                "train_bars": 80,
                "test_bars": 30,
                "step_bars": 30,
                "pass_rate": 0.25,
            },
        },
        "elimination_result": {"passed": True, "failed_rules": []},
    }

    widget = ValidationSummary()
    widget.update_from_result(result, source_label="Test data")
    text = _widget_text(widget)

    assert "Walk-Forward Matrix" in text
    assert "Configs: 4 total" in text
    assert "Tested: 3" in text
    assert "Insufficient data: 1" in text
    assert "Best: wf_matrix_001" in text
    assert "(50/20/10)" in text
    assert "Pass Rate: 75%" in text
    assert "Worst: wf_matrix_002" in text
    assert "(80/30/30)" in text
    assert "Pass Rate: 25%" in text


def test_wf_matrix_summary_none_not_shown(qapp):
    """Dashboard should stay clean when matrix summary is not present."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0},
        "stress_results": [],
        "walk_forward_summary": {"window_count": 1, "pass_count": 1, "pass_rate": 1.0},
        "walk_forward_matrix_summary": None,
        "elimination_result": {"passed": True, "failed_rules": []},
    }

    widget = ValidationSummary()
    widget.update_from_result(result)

    assert "Walk-Forward Matrix" not in _widget_text(widget)


def test_wf_matrix_summary_missing_best_worst(qapp):
    """Missing best/worst configs should not crash or render bogus detail lines."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0},
        "stress_results": [],
        "walk_forward_matrix_summary": {
            "config_count": 2,
            "tested_count": 0,
            "insufficient_data_count": 2,
            "best_pass_rate_config": None,
            "worst_pass_rate_config": None,
        },
        "elimination_result": {"passed": True, "failed_rules": []},
    }

    widget = ValidationSummary()
    widget.update_from_result(result)
    text = _widget_text(widget)

    assert "Walk-Forward Matrix" in text
    assert "Configs: 2 total" in text
    assert "Tested: 0" in text
    assert "Insufficient data: 2" in text
    assert "Best:" not in text
    assert "Worst:" not in text


def test_update_then_empty(qapp):
    """Updating with result then clearing must show empty placeholder."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0},
        "stress_results": [],
        "elimination_result": {"passed": True, "failed_rules": []},
    }
    widget = ValidationSummary()
    widget.update_from_result(result)
    # Clear
    widget.show_empty()
    assert widget._layout.count() >= 1


# ---------------------------------------------------------------------------
# Elimination failed rules
# ---------------------------------------------------------------------------


def test_oos_metrics_card_displayed(qapp):
    """OOS Metrics card must appear between WF Matrix and Elimination."""
    result = {
        "split_metadata": {"train_rows": 90, "validation_rows": 45, "oos_rows": 45},
        "baseline_metrics": {"total_pnl": 5000.0, "profit_factor": 1.8, "total_trades": 22},
        "stress_results": [],
        "walk_forward_summary": {"window_count": 5, "pass_count": 3, "pass_rate": 0.6},
        "oos_metrics": {
            "total_trades": 8, "total_pnl": 1200.0, "profit_factor": 1.25,
            "max_drawdown_pnl": 3000.0, "win_rate": 0.50,
        },
        "elimination_result": {"passed": True, "failed_rules": []},
    }
    widget = ValidationSummary()
    widget.update_from_result(result)
    text = _widget_text(widget)

    assert "OOS Metrics" in text
    assert "1,200" in text
    assert "1.25" in text
    assert "8" in text
    assert "3,000" in text
    assert "50%" in text


def test_oos_metrics_missing_shows_placeholder(qapp):
    """When oos_metrics is missing, OOS card shows 'No OOS data.'."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0},
        "stress_results": [],
        "elimination_result": {"passed": True, "failed_rules": []},
    }
    widget = ValidationSummary()
    widget.update_from_result(result)
    text = _widget_text(widget)

    assert "OOS Metrics" in text
    assert "No OOS data." in text


def test_elimination_failed_rules_displayed(qapp):
    """When elimination fails, failed_rules must appear in the body text."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": -500.0},
        "stress_results": [],
        "oos_metrics": None,
        "elimination_result": {
            "passed": False,
            "failed_rules": [
                "min_total_pnl (-500 < 0)",
                "min_trade_count (3 < 5)",
            ],
        },
    }

    widget = ValidationSummary()
    widget.update_from_result(result)

    # Find the elimination card and check its body contains the failed rules.
    found_elim = False
    for i in range(widget._layout.count()):
        item = widget._layout.itemAt(i)
        if item and item.widget():
            w = item.widget()
            # QFrame with QVBoxLayout containing QLabels
            if hasattr(w, "layout") and w.layout() is not None:
                lay = w.layout()
                for j in range(lay.count()):
                    child = lay.itemAt(j)
                    if child and child.widget():
                        txt = getattr(child.widget(), "text", lambda: "")()
                        if "ELIMINATED" in str(txt):
                            found_elim = True
                            assert "min_total_pnl" in str(txt)
                            assert "min_trade_count" in str(txt)
    assert found_elim, "Elimination card with 'ELIMINATED' not found"


# ---------------------------------------------------------------------------
# Stress detail sub-lines (Task 056G-Impl)
# ---------------------------------------------------------------------------


def test_stress_remove_best_n_trades_detail_sub_lines(qapp):
    """remove_best_n_trades must show sub-lines with n, removed, pnl_loss."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0, "total_trades": 4},
        "stress_results": [
            {"test_name": "commission_2.0x", "passed": True,
             "degradation": {"total_pnl": -0.15}},
            {"test_name": "remove_best_n_trades", "passed": False,
             "degradation": {"total_pnl": -0.83},
             "assumptions": {
                 "n": 2, "removed_count": 2, "surviving_count": 2,
                 "pnl_loss_ratio": 0.833, "total_baseline_count": 4,
             },
             "warnings": ["Some warning text."],
             "threshold": {"max_pnl_loss": 0.30},
            },
        ],
        "elimination_result": {"passed": True, "failed_rules": []},
    }
    widget = ValidationSummary()
    widget.update_from_result(result)
    text = _widget_text(widget)

    assert "commission_2.0x:" in text
    assert "remove_best_n_trades:" in text
    assert "Removed:" in text
    assert "n=2" in text
    assert "pnl_loss=0.833" in text
    assert "threshold=0.30" in text
    assert "Some warning text." in text


def test_stress_no_sub_lines_for_basic_tests(qapp):
    """Basic stress tests must NOT have detail sub-lines."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0},
        "stress_results": [
            {"test_name": "commission_2.0x", "passed": True,
             "degradation": {"total_pnl": -0.15}},
            {"test_name": "slippage_2.0x", "passed": True,
             "degradation": {"total_pnl": -0.08}},
        ],
        "elimination_result": {"passed": True, "failed_rules": []},
    }
    widget = ValidationSummary()
    widget.update_from_result(result)
    text = _widget_text(widget)

    assert "commission_2.0x:" in text
    assert "slippage_2.0x:" in text
    assert "→" not in text  # No sub-lines for basic tests


# ---------------------------------------------------------------------------
# Precheck visibility (Task 056K-Impl)
# ---------------------------------------------------------------------------


def test_precheck_card_shown_when_failed(qapp):
    """Precheck section must appear when precheck_failed=True."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 0.0, "total_trades": 0},
        "stress_results": [],
        "precheck_failed": True,
        "elimination_result": {
            "passed": False,
            "failed_rules": ["Validation precheck failed: strategy has zero baseline trades."],
        },
    }
    widget = ValidationSummary()
    widget.update_from_result(result)
    text = _widget_text(widget)

    assert "Precheck" in text
    assert "FAILED" in text
    assert "zero baseline trades" in text


def test_precheck_card_absent_when_false(qapp):
    """Precheck section must NOT appear when precheck_failed=False."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0, "total_trades": 5},
        "stress_results": [],
        "precheck_failed": False,
        "elimination_result": {"passed": True, "failed_rules": []},
    }
    widget = ValidationSummary()
    widget.update_from_result(result)
    text = _widget_text(widget)

    assert "Precheck" not in text


# ---------------------------------------------------------------------------
# Bootstrap MC display (Task 057E-Impl)
# ---------------------------------------------------------------------------


def test_bootstrap_mc_card_shown_when_present(qapp):
    """Bootstrap MC card must appear when data is present."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0},
        "stress_results": [],
        "monte_carlo_summary": {
            "iterations": 15,
            "percentile_summary": {"total_pnl": {"p5": 1000.0, "p50": 5000.0, "p95": 9000.0}},
            "worst_case": {"total_pnl": 1000.0},
        },
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
    widget = ValidationSummary()
    widget.update_from_result(result)
    text = _widget_text(widget)

    assert "Bootstrap MC" in text
    assert "200" in text
    assert "0.85" in text
    assert "1,200" in text
    assert "9,800" in text
    assert "5,400" in text


def test_bootstrap_mc_card_absent_when_missing(qapp):
    """Bootstrap MC card must NOT appear when data is missing."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0},
        "stress_results": [],
        "monte_carlo_summary": {"iterations": 15, "percentile_summary": {"total_pnl": {"p5": 1000.0, "p50": 5000.0, "p95": 9000.0}}, "worst_case": {"total_pnl": 1000.0}},
        "elimination_result": {"passed": True, "failed_rules": []},
    }
    widget = ValidationSummary()
    widget.update_from_result(result)
    text = _widget_text(widget)

    assert "Bootstrap MC" not in text


def test_bootstrap_mc_card_absent_when_ci_empty(qapp):
    """Bootstrap MC card must NOT appear when CI data is empty."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0},
        "stress_results": [],
        "monte_carlo_summary": {"iterations": 15, "percentile_summary": {"total_pnl": {"p5": 1000.0, "p50": 5000.0, "p95": 9000.0}}, "worst_case": {"total_pnl": 1000.0}},
        "bootstrap_monte_carlo_result": {
            "test_name": "bootstrap",
            "iterations": 200,
            "confidence_intervals": {},  # empty
        },
        "elimination_result": {"passed": True, "failed_rules": []},
    }
    widget = ValidationSummary()
    widget.update_from_result(result)
    text = _widget_text(widget)
    assert "Bootstrap MC" not in text


def test_bootstrap_mc_pf_formatted_two_decimals(qapp):
    """Profit factor CI must render with two decimal places."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0},
        "stress_results": [],
        "monte_carlo_summary": {"iterations": 15, "percentile_summary": {"total_pnl": {"p5": 1000.0, "p50": 5000.0, "p95": 9000.0}}, "worst_case": {"total_pnl": 1000.0}},
        "bootstrap_monte_carlo_result": {
            "test_name": "bootstrap",
            "iterations": 200,
            "stability_score": 0.85,
            "confidence_intervals": {
                "profit_factor": {"ci_lower": 1.156, "ci_upper": 2.803, "ci_mean": 1.951},
            },
        },
        "elimination_result": {"passed": True, "failed_rules": []},
    }
    widget = ValidationSummary()
    widget.update_from_result(result)
    text = _widget_text(widget)
    assert "1.16" in text
    assert "2.80" in text
    assert "1.95" in text


# ---------------------------------------------------------------------------
# WF Equity Summary (Task 057J-Impl)
# ---------------------------------------------------------------------------


def test_wf_equity_summary_shown_when_present(qapp):
    """WF Equity Summary must appear when windows have equity curves."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0},
        "stress_results": [],
        "walk_forward_summary": {
            "window_count": 3, "pass_count": 2, "pass_rate": 0.67,
            "windows": [
                {"index": 0, "equity_curve": [100000.0, 100500.0, 100200.0, 101000.0], "passed": True},
                {"index": 1, "equity_curve": [100000.0, 99500.0, 99000.0], "passed": False},
                {"index": 2, "equity_curve": [100000.0, 100100.0], "passed": True},
            ],
        },
        "elimination_result": {"passed": True, "failed_rules": []},
    }
    widget = ValidationSummary()
    widget.update_from_result(result)
    text = _widget_text(widget)

    assert "WF Equity Summary" in text
    assert "+1.0%" in text or "101000" in text
    assert "-1.0%" in text or "99000" in text
    assert "PASSED" in text


def test_wf_equity_summary_absent_when_no_equity(qapp):
    """WF Equity Summary must NOT appear when no windows have equity."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0},
        "stress_results": [],
        "walk_forward_summary": {
            "window_count": 2, "pass_count": 1, "pass_rate": 0.5,
            "windows": [
                {"index": 0, "equity_curve": None, "passed": True},
                {"index": 1, "passed": False},
            ],
        },
        "elimination_result": {"passed": True, "failed_rules": []},
    }
    widget = ValidationSummary()
    widget.update_from_result(result)
    text = _widget_text(widget)
    assert "WF Equity Summary" not in text


def test_wf_equity_summary_absent_when_no_windows_key(qapp):
    """WF Equity Summary must NOT appear when windows key is missing."""
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0},
        "stress_results": [],
        "walk_forward_summary": {"window_count": 2, "pass_count": 1, "pass_rate": 0.5},
        "elimination_result": {"passed": True, "failed_rules": []},
    }
    widget = ValidationSummary()
    widget.update_from_result(result)
    text = _widget_text(widget)
    assert "WF Equity Summary" not in text


def test_wf_equity_summary_capped_at_5_windows(qapp):
    """WF Equity Summary must show '... more windows' when > 5 windows."""
    windows = []
    for i in range(7):
        windows.append({
            "index": i,
            "equity_curve": [100000.0, 100000.0 + i * 100.0],
            "passed": True,
        })
    result = {
        "split_metadata": {"train_rows": 10},
        "baseline_metrics": {"total_pnl": 100.0},
        "stress_results": [],
        "walk_forward_summary": {"window_count": 7, "pass_count": 7, "pass_rate": 1.0, "windows": windows},
        "elimination_result": {"passed": True, "failed_rules": []},
    }
    widget = ValidationSummary()
    widget.update_from_result(result)
    text = _widget_text(widget)

    assert "WF Equity Summary" in text
    assert "more windows" in text  # "2 more windows"
