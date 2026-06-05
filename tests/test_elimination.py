"""Tests for strategy elimination rules engine — Task 017."""

from __future__ import annotations

import pytest

from validation_engine.elimination import (
    EliminationConfig,
    EliminationResult,
    evaluate_elimination,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _good_metrics() -> dict:
    return {
        "total_trades": 50,
        "winning_trades": 30,
        "losing_trades": 20,
        "win_rate": 0.6,
        "total_pnl": 25000.0,
        "avg_trade": 500.0,
        "gross_profit": 50000.0,
        "gross_loss": 25000.0,
        "profit_factor": 2.0,
        "max_drawdown_pnl": 5000.0,
    }


def _bad_metrics() -> dict:
    return {
        "total_trades": 3,
        "winning_trades": 1,
        "losing_trades": 2,
        "win_rate": 0.33,
        "total_pnl": -5000.0,
        "avg_trade": -1666.0,
        "gross_profit": 1000.0,
        "gross_loss": 6000.0,
        "profit_factor": 0.17,
        "max_drawdown_pnl": 8000.0,
    }


# ---------------------------------------------------------------------------
# Pass all thresholds
# ---------------------------------------------------------------------------


def test_pass_all_thresholds():
    """Good metrics with lenient config must pass."""
    config = EliminationConfig(
        min_total_pnl=0.0,
        min_profit_factor=1.0,
        max_drawdown_pnl=10000.0,
        min_trade_count=20,
    )
    result = evaluate_elimination(_good_metrics(), config)
    assert result.passed
    assert result.failed_rules == []


# ---------------------------------------------------------------------------
# Fail each major threshold
# ---------------------------------------------------------------------------


def test_fail_min_total_pnl():
    config = EliminationConfig(min_total_pnl=30000.0)
    result = evaluate_elimination(_good_metrics(), config)
    assert not result.passed
    assert any("min_total_pnl" in r for r in result.failed_rules)


def test_fail_min_profit_factor():
    config = EliminationConfig(min_profit_factor=3.0)
    result = evaluate_elimination(_good_metrics(), config)
    assert not result.passed


def test_fail_max_drawdown():
    config = EliminationConfig(max_drawdown_pnl=1000.0)
    result = evaluate_elimination(_good_metrics(), config)
    assert not result.passed
    assert any("max_drawdown_pnl" in r for r in result.failed_rules)


def test_fail_min_avg_trade():
    config = EliminationConfig(min_avg_trade=1000.0)
    result = evaluate_elimination(_good_metrics(), config)
    assert not result.passed


def test_fail_min_trade_count():
    config = EliminationConfig(min_trade_count=100)
    result = evaluate_elimination(_good_metrics(), config)
    assert not result.passed


def test_fail_min_win_rate():
    config = EliminationConfig(min_win_rate=0.8)
    result = evaluate_elimination(_good_metrics(), config)
    assert not result.passed


def test_fail_multiple_rules():
    """Bad metrics with strict config must fail multiple rules."""
    config = EliminationConfig(
        min_total_pnl=0.0,
        min_profit_factor=1.0,
        max_drawdown_pnl=2000.0,
        min_trade_count=10,
    )
    result = evaluate_elimination(_bad_metrics(), config)
    assert not result.passed
    assert len(result.failed_rules) >= 3


# ---------------------------------------------------------------------------
# Optional OOS / stress / MC / WF thresholds
# ---------------------------------------------------------------------------


def test_oos_thresholds_applied_when_provided():
    config = EliminationConfig(min_oos_total_pnl=5000.0)
    oos = {"total_pnl": 3000.0, "profit_factor": 1.5}
    result = evaluate_elimination(_good_metrics(), config, oos_metrics=oos)
    assert not result.passed
    assert any("min_oos_total_pnl" in r for r in result.failed_rules)


def test_oos_missing_warns_by_default():
    """When OOS thresholds are set but no OOS data, warn (don't fail)."""
    config = EliminationConfig(min_oos_total_pnl=5000.0)
    result = evaluate_elimination(_good_metrics(), config)
    assert result.passed  # not failed — just warned
    assert any("OOS" in w for w in result.warnings)


def test_oos_missing_fails_when_required():
    """When require_optional=True, missing OOS data with OOS thresholds → fail."""
    config = EliminationConfig(min_oos_total_pnl=5000.0, require_optional=True)
    result = evaluate_elimination(_good_metrics(), config)
    assert not result.passed
    assert any("OOS" in r for r in result.failed_rules)


def test_stress_pass_rate_applied():
    config = EliminationConfig(min_stress_pass_rate=0.8)
    stress = [
        {"passed": True},
        {"passed": True},
        {"passed": False},  # 2/3 = 0.67 < 0.8
    ]
    result = evaluate_elimination(_good_metrics(), config, stress_results=stress)
    assert not result.passed
    assert any("stress_pass_rate" in r for r in result.failed_rules)


def test_monte_carlo_p05_pnl_applied():
    config = EliminationConfig(min_monte_carlo_p05_pnl=10000.0)
    mc = {"worst_case": {"total_pnl": 5000.0}}  # p05 = 5000 < 10000
    result = evaluate_elimination(_good_metrics(), config, mc_result=mc)
    assert not result.passed
    assert any("monte_carlo_p05_pnl" in r for r in result.failed_rules)


def test_walk_forward_pass_rate_applied():
    config = EliminationConfig(min_walk_forward_pass_rate=0.5)
    wf = {"pass_rate": 0.3}  # 0.3 < 0.5
    result = evaluate_elimination(_good_metrics(), config, wf_result=wf)
    assert not result.passed
    assert any("walk_forward_pass_rate" in r for r in result.failed_rules)


# ---------------------------------------------------------------------------
# Structured output
# ---------------------------------------------------------------------------


def test_elimination_result_structure():
    """Result must have all required fields."""
    config = EliminationConfig(min_total_pnl=0.0)
    result = evaluate_elimination(_good_metrics(), config)

    assert isinstance(result, EliminationResult)
    assert isinstance(result.passed, bool)
    assert isinstance(result.failed_rules, list)
    assert isinstance(result.warnings, list)
    assert isinstance(result.metrics_snapshot, dict)
    assert isinstance(result.config_snapshot, dict)
    assert result.metrics_snapshot == _good_metrics()


def test_elimination_does_not_mutate_inputs():
    """Input metrics dict must not be modified."""
    metrics = _good_metrics()
    metrics_copy = dict(metrics)
    config = EliminationConfig(min_total_pnl=0.0)

    evaluate_elimination(metrics, config)
    assert metrics == metrics_copy


def test_config_is_serializable():
    """EliminationConfig.to_dict() must return a plain dict."""
    config = EliminationConfig(min_total_pnl=1000.0, min_trade_count=10)
    d = config.to_dict()
    assert isinstance(d, dict)
    assert d["min_total_pnl"] == 1000.0
    assert d["min_trade_count"] == 10
    assert d["min_profit_factor"] is None


def test_empty_config_passes_everything():
    """An EliminationConfig with all defaults (None) must pass any metrics."""
    config = EliminationConfig()
    result = evaluate_elimination(_bad_metrics(), config)
    assert result.passed
    assert result.failed_rules == []
