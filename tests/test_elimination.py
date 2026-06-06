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


# ---------------------------------------------------------------------------
# IS/OOS Stability ratio rules (Task 056B)
# ---------------------------------------------------------------------------


def _oos_good_oos() -> dict:
    """OOS metrics that are close to IS: passes PF degradation, DD ratio, avg trade degradation."""
    return {
        "total_pnl": 20000.0,
        "profit_factor": 1.8,  # IS=2.0 → 0.90 degradation
        "max_drawdown_pnl": 6000.0,  # IS=5000 → 1.2× ratio
        "total_trades": 40,
        "avg_trade": 400.0,  # IS=500 → 0.80 degradation
        "win_rate": 0.55,
    }


def _oos_bad_pf() -> dict:
    """OOS PF severely degraded: 0.5 / 2.0 = 0.25."""
    return {
        "total_pnl": 5000.0,
        "profit_factor": 0.5,
        "max_drawdown_pnl": 6000.0,
        "total_trades": 40,
        "avg_trade": 100.0,
        "win_rate": 0.40,
    }


def _oos_bad_dd() -> dict:
    """OOS DD severely inflated: 20000 / 5000 = 4.0."""
    return {
        "total_pnl": 15000.0,
        "profit_factor": 1.5,
        "max_drawdown_pnl": 20000.0,
        "total_trades": 40,
        "avg_trade": 300.0,
        "win_rate": 0.50,
    }


def _oos_bad_avg_trade() -> dict:
    """OOS avg trade severely degraded: 50 / 500 = 0.10."""
    return {
        "total_pnl": 1000.0,
        "profit_factor": 1.5,
        "max_drawdown_pnl": 6000.0,
        "total_trades": 40,
        "avg_trade": 50.0,
        "win_rate": 0.50,
    }


def test_stability_pf_degradation_passes():
    """OOS PF close to IS PF must pass with a lenient threshold."""
    config = EliminationConfig(max_oos_pf_degradation=0.5)  # allow down to 50%
    result = evaluate_elimination(_good_metrics(), config, oos_metrics=_oos_good_oos())
    assert result.passed


def test_stability_pf_degradation_fails():
    """OOS PF too low vs IS PF must fail."""
    config = EliminationConfig(max_oos_pf_degradation=0.5)  # 0.25 < 0.5
    result = evaluate_elimination(_good_metrics(), config, oos_metrics=_oos_bad_pf())
    assert not result.passed
    assert any("max_oos_pf_degradation" in r for r in result.failed_rules)


def test_stability_drawdown_ratio_passes():
    """OOS DD within bounds must pass."""
    config = EliminationConfig(max_oos_drawdown_ratio=2.0)  # allow up to 2×
    result = evaluate_elimination(_good_metrics(), config, oos_metrics=_oos_good_oos())
    assert result.passed


def test_stability_drawdown_ratio_fails():
    """OOS DD too high vs IS DD must fail."""
    config = EliminationConfig(max_oos_drawdown_ratio=2.0)  # 4.0 > 2.0
    result = evaluate_elimination(_good_metrics(), config, oos_metrics=_oos_bad_dd())
    assert not result.passed
    assert any("max_oos_drawdown_ratio" in r for r in result.failed_rules)


def test_stability_avg_trade_degradation_passes():
    """OOS avg trade close to IS avg trade must pass."""
    config = EliminationConfig(max_oos_avg_trade_degradation=0.5)  # allow down to 50%
    result = evaluate_elimination(_good_metrics(), config, oos_metrics=_oos_good_oos())
    assert result.passed


def test_stability_avg_trade_degradation_fails():
    """OOS avg trade too low vs IS avg trade must fail."""
    config = EliminationConfig(max_oos_avg_trade_degradation=0.5)  # 0.10 < 0.5
    result = evaluate_elimination(_good_metrics(), config, oos_metrics=_oos_bad_avg_trade())
    assert not result.passed
    assert any("max_oos_avg_trade_degradation" in r for r in result.failed_rules)


def test_stability_all_three_pass():
    """All three stability rules pass simultaneously with good OOS."""
    config = EliminationConfig(
        max_oos_pf_degradation=0.5,
        max_oos_drawdown_ratio=2.0,
        max_oos_avg_trade_degradation=0.5,
    )
    result = evaluate_elimination(_good_metrics(), config, oos_metrics=_oos_good_oos())
    assert result.passed


def test_stability_metrics_missing_warns_by_default():
    """Stability thresholds set but no OOS metrics → warn, don't fail."""
    config = EliminationConfig(max_oos_pf_degradation=0.5)
    result = evaluate_elimination(_good_metrics(), config)  # no oos_metrics
    assert result.passed
    assert any("OOS" in w for w in result.warnings)


def test_stability_metrics_missing_fails_when_required():
    """Stability thresholds + require_optional + no OOS data → fail."""
    config = EliminationConfig(max_oos_pf_degradation=0.5, require_optional=True)
    result = evaluate_elimination(_good_metrics(), config)
    assert not result.passed
    assert any("OOS" in r for r in result.failed_rules)


def test_stability_thresholds_none_by_default():
    """Default EliminationConfig sets all stability fields to None."""
    config = EliminationConfig()
    assert config.max_oos_pf_degradation is None
    assert config.max_oos_drawdown_ratio is None
    assert config.max_oos_avg_trade_degradation is None


def test_stability_all_none_skips_rules():
    """All stability thresholds None → rules are skipped even with OOS data."""
    config = EliminationConfig()  # all stability fields are None
    result = evaluate_elimination(_good_metrics(), config, oos_metrics=_oos_bad_pf())
    assert result.passed  # no stability rules to fail


# ---------------------------------------------------------------------------
# Uncomputable stability ratios (Task 056B-Fix)
# ---------------------------------------------------------------------------


def _is_zero_pf() -> dict:
    """IS with profit_factor=0.0 (non-positive)."""
    return dict(_good_metrics(), profit_factor=0.0)


def _is_zero_dd() -> dict:
    """IS with max_drawdown_pnl=0.0 (non-positive)."""
    return dict(_good_metrics(), max_drawdown_pnl=0.0)


def _is_zero_avg_trade() -> dict:
    """IS with avg_trade=0.0 (non-positive)."""
    return dict(_good_metrics(), avg_trade=0.0)


def test_stability_pf_degradation_undefined_warns():
    """PF threshold set but IS PF=0 → warn, don't fail by default."""
    config = EliminationConfig(max_oos_pf_degradation=0.5)
    result = evaluate_elimination(_is_zero_pf(), config, oos_metrics=_oos_good_oos())
    assert result.passed  # not failed — just warned
    assert any("max_oos_pf_degradation is set" in w for w in result.warnings)


def test_stability_pf_degradation_undefined_fails_with_require():
    """PF threshold set but IS PF=0 + require_optional → fail."""
    config = EliminationConfig(max_oos_pf_degradation=0.5, require_optional=True)
    result = evaluate_elimination(_is_zero_pf(), config, oos_metrics=_oos_good_oos())
    assert not result.passed
    assert any("max_oos_pf_degradation" in r for r in result.failed_rules)


def test_stability_drawdown_ratio_undefined_warns():
    """DD ratio threshold set but IS DD=0 → warn, don't fail by default."""
    config = EliminationConfig(max_oos_drawdown_ratio=2.0)
    result = evaluate_elimination(_is_zero_dd(), config, oos_metrics=_oos_good_oos())
    assert result.passed
    assert any("max_oos_drawdown_ratio is set" in w for w in result.warnings)


def test_stability_drawdown_ratio_undefined_fails_with_require():
    """DD ratio threshold set but IS DD=0 + require_optional → fail."""
    config = EliminationConfig(max_oos_drawdown_ratio=2.0, require_optional=True)
    result = evaluate_elimination(_is_zero_dd(), config, oos_metrics=_oos_good_oos())
    assert not result.passed
    assert any("max_oos_drawdown_ratio" in r for r in result.failed_rules)


def test_stability_avg_trade_degradation_undefined_warns():
    """Avg trade threshold set but IS avg trade=0 → warn, don't fail by default."""
    config = EliminationConfig(max_oos_avg_trade_degradation=0.5)
    result = evaluate_elimination(_is_zero_avg_trade(), config, oos_metrics=_oos_good_oos())
    assert result.passed
    assert any("max_oos_avg_trade_degradation is set" in w for w in result.warnings)


def test_stability_avg_trade_degradation_undefined_fails_with_require():
    """Avg trade threshold set but IS avg trade=0 + require_optional → fail."""
    config = EliminationConfig(max_oos_avg_trade_degradation=0.5, require_optional=True)
    result = evaluate_elimination(_is_zero_avg_trade(), config, oos_metrics=_oos_good_oos())
    assert not result.passed
    assert any("max_oos_avg_trade_degradation" in r for r in result.failed_rules)


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
