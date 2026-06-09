"""Tests for Monte Carlo simulation engine — Task 015."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.models.strategy import Condition, Strategy, StrategyBlock
from core.models.backtest_result import BacktestResult, Trade
from backtest_engine.runner import run_backtest
from validation_engine.monte_carlo import (
    MonteCarloResult,
    _is_worse_iteration,
    run_missed_trade_monte_carlo,
    run_slippage_monte_carlo,
    run_combined_monte_carlo,
    run_bootstrap_monte_carlo,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_test_df(n_bars: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="1min")
    close = np.linspace(100.0, 150.0, n_bars)
    noise = rng.uniform(0.5, 2.0, n_bars)
    return pd.DataFrame({
        "datetime": times,
        "open":  close - noise * 0.3,
        "high":  close + noise,
        "low":   close - noise,
        "close": close,
        "volume": rng.integers(1000, 5000, n_bars),
    })


def _make_sma_strategy(period: int = 10) -> Strategy:
    return Strategy(
        name="mc_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": period}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": period}, operator="<"),
        ], logic="AND"),
    )


# ---------------------------------------------------------------------------
# Missed trade Monte Carlo
# ---------------------------------------------------------------------------


def test_missed_trade_mc_runs_correct_iterations():
    """Monte Carlo must run exactly `iterations` simulations."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    result = run_missed_trade_monte_carlo(baseline, iterations=30, base_seed=1)

    assert result.iterations == 30
    assert len(result.all_metrics) == 30


def test_missed_trade_mc_is_deterministic():
    """Same seed must produce identical Monte Carlo results."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    r1 = run_missed_trade_monte_carlo(baseline, iterations=20, base_seed=42)
    r2 = run_missed_trade_monte_carlo(baseline, iterations=20, base_seed=42)

    assert r1.percentile_summary == r2.percentile_summary
    assert r1.all_metrics == r2.all_metrics


def test_missed_trade_mc_different_seeds_diverge():
    """Different seeds should produce different metric distributions."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    r1 = run_missed_trade_monte_carlo(baseline, iterations=20, base_seed=1)
    r2 = run_missed_trade_monte_carlo(baseline, iterations=20, base_seed=999)

    # With enough trades, different seeds should produce different p50 PnL.
    if baseline.metrics["total_trades"] > 10:
        p50_1 = r1.percentile_summary["total_pnl"]["p50"]
        p50_2 = r2.percentile_summary["total_pnl"]["p50"]
        assert p50_1 != pytest.approx(p50_2)


def test_missed_trade_mc_percentile_summary():
    """Percentile summary must have p5, p25, p50, p75, p95 for each metric."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    result = run_missed_trade_monte_carlo(baseline, iterations=50, base_seed=1)

    for key in ("total_pnl", "profit_factor", "max_drawdown_pnl", "win_rate", "avg_trade", "total_trades"):
        assert key in result.percentile_summary, f"Missing {key} in percentile_summary"
        for p in ("p5", "p25", "p50", "p75", "p95"):
            assert p in result.percentile_summary[key], f"Missing {p} in {key}"


def test_missed_trade_mc_worst_case():
    """Worst case uses p5 for PnL and p95 for drawdown."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    result = run_missed_trade_monte_carlo(baseline, iterations=50, base_seed=1)

    assert result.worst_case["total_pnl"] == result.percentile_summary["total_pnl"]["p5"]
    assert result.worst_case["max_drawdown_pnl"] == result.percentile_summary["max_drawdown_pnl"]["p95"]


def test_missed_trade_mc_structured_output():
    """Result must have all MonteCarloResult fields."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    result = run_missed_trade_monte_carlo(baseline, iterations=10, base_seed=1)

    assert isinstance(result, MonteCarloResult)
    assert result.test_name == "missed_trade_mc"
    assert result.iterations == 10
    assert isinstance(result.baseline_metrics, dict)
    assert isinstance(result.percentile_summary, dict)
    assert isinstance(result.all_metrics, list)
    assert isinstance(result.worst_case, dict)
    assert isinstance(result.assumptions, dict)


def test_missed_trade_mc_zero_trades():
    """Zero baseline trades must produce a vacuous result with warning."""
    df = _make_test_df(10)
    strat = Strategy(name="empty")
    baseline = run_backtest(strat, df)

    result = run_missed_trade_monte_carlo(baseline, iterations=10)
    assert len(result.warnings) >= 1
    assert result.all_metrics == []


# ---------------------------------------------------------------------------
# Slippage perturbation Monte Carlo
# ---------------------------------------------------------------------------


def test_slippage_mc_runs_correct_iterations():
    """Slippage MC must run exactly `iterations` backtests."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    result = run_slippage_monte_carlo(strat, df, baseline, iterations=20, base_seed=1)

    assert result.iterations == 20
    assert len(result.all_metrics) == 20


def test_slippage_mc_is_deterministic():
    """Same seed must produce identical slippage MC results."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    r1 = run_slippage_monte_carlo(strat, df, baseline, iterations=15, base_seed=42)
    r2 = run_slippage_monte_carlo(strat, df, baseline, iterations=15, base_seed=42)

    assert r1.percentile_summary == r2.percentile_summary


def test_slippage_mc_percentile_summary():
    """Slippage MC must produce valid percentile distribution."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    result = run_slippage_monte_carlo(strat, df, baseline, iterations=30, base_seed=1)

    for key in ("total_pnl", "profit_factor"):
        assert key in result.percentile_summary
        assert result.percentile_summary[key]["p5"] <= result.percentile_summary[key]["p95"]


def test_slippage_mc_does_not_mutate_baseline():
    """Baseline BacktestResult must be unchanged."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    metrics_before = dict(baseline.metrics)
    run_slippage_monte_carlo(strat, df, baseline, iterations=10, base_seed=1)
    assert baseline.metrics == metrics_before


# ---------------------------------------------------------------------------
# Task 042B1 - Configurable Percentiles and Stability Score
# ---------------------------------------------------------------------------


def test_monte_carlo_default_percentiles_unchanged():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    result = run_missed_trade_monte_carlo(baseline, iterations=10)
    
    assert result.percentiles_used == (5.0, 25.0, 50.0, 75.0, 95.0)
    assert "total_pnl" in result.percentile_summary
    for p in ("p5", "p25", "p50", "p75", "p95"):
        assert p in result.percentile_summary["total_pnl"]


def test_monte_carlo_custom_percentiles_structure():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    result = run_missed_trade_monte_carlo(baseline, iterations=10, percentiles=(1.0, 10.0, 90.0, 99.0))
    
    assert result.percentiles_used == (1.0, 10.0, 90.0, 99.0)
    assert "p1" in result.percentile_summary["total_pnl"]
    assert "p10" in result.percentile_summary["total_pnl"]
    assert "p90" in result.percentile_summary["total_pnl"]
    assert "p99" in result.percentile_summary["total_pnl"]
    assert "p5" not in result.percentile_summary["total_pnl"]


def test_monte_carlo_percentiles_used_recorded():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    result = run_slippage_monte_carlo(strat, df, baseline, iterations=10, percentiles=(15.0, 85.0))
    assert result.percentiles_used == (15.0, 85.0)


def test_monte_carlo_stability_score_computed():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    result = run_missed_trade_monte_carlo(baseline, iterations=10, percentiles=(5.0, 50.0, 95.0))
    
    # We should have a float stability score assuming baseline has trades and p50 != 0
    if baseline.metrics.get("total_trades", 0) > 0 and abs(result.percentile_summary["total_pnl"]["p50"]) > 1e-9:
        assert isinstance(result.stability_score, float)
        expected = result.percentile_summary["total_pnl"]["p5"] / abs(result.percentile_summary["total_pnl"]["p50"])
        assert result.stability_score == pytest.approx(expected)


def test_monte_carlo_stability_score_none_when_p50_zero():
    # Force a baseline with zero pnl everywhere by giving empty df or bad strat
    df = _make_test_df(10)
    strat = Strategy(name="empty")
    baseline = run_backtest(strat, df)

    result = run_missed_trade_monte_carlo(baseline, iterations=10)
    # Vacuous MC should handle stability_score = None
    assert result.stability_score is None


def test_monte_carlo_custom_percentiles_deterministic():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    r1 = run_missed_trade_monte_carlo(baseline, iterations=10, base_seed=42, percentiles=(10.0, 50.0, 90.0))
    r2 = run_missed_trade_monte_carlo(baseline, iterations=10, base_seed=42, percentiles=(10.0, 50.0, 90.0))

    assert r1.percentile_summary == r2.percentile_summary
    assert r1.stability_score == r2.stability_score


def test_slippage_monte_carlo_custom_percentiles():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    result = run_slippage_monte_carlo(strat, df, baseline, iterations=10, percentiles=(1.0, 99.0))
    assert "p1" in result.percentile_summary["total_pnl"]
    assert "p99" in result.percentile_summary["total_pnl"]


def test_missed_trade_monte_carlo_no_baseline_mutation_still_passes():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    metrics_before = dict(baseline.metrics)
    trades_len_before = len(baseline.trades)
    
    run_missed_trade_monte_carlo(baseline, iterations=10, percentiles=(1.0, 99.0))
    
    assert baseline.metrics == metrics_before
    assert len(baseline.trades) == trades_len_before


def test_monte_carlo_empty_percentiles_safe_behavior():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)
    result = run_missed_trade_monte_carlo(baseline, iterations=10, percentiles=())
    assert result.percentiles_used == (5.0, 25.0, 50.0, 75.0, 95.0)


def test_monte_carlo_duplicate_percentiles_deduped_or_documented():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)
    result = run_missed_trade_monte_carlo(baseline, iterations=10, percentiles=(50.0, 50.0, 95.0, 5.0))
    assert result.percentiles_used == (5.0, 50.0, 95.0)


def test_monte_carlo_invalid_percentiles_rejected():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)
    with pytest.raises(ValueError, match="out of bounds"):
        run_missed_trade_monte_carlo(baseline, iterations=10, percentiles=(-1.0, 50.0))
    with pytest.raises(ValueError, match="out of bounds"):
        run_missed_trade_monte_carlo(baseline, iterations=10, percentiles=(50.0, 101.0))


def test_monte_carlo_percentiles_without_50_stability_none():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)
    result = run_missed_trade_monte_carlo(baseline, iterations=10, percentiles=(5.0, 95.0))
    assert result.stability_score is None


def test_monte_carlo_percentiles_used_stable_ordering():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)
    result = run_missed_trade_monte_carlo(baseline, iterations=10, percentiles=(90.0, 10.0, 50.0))
    assert result.percentiles_used == (10.0, 50.0, 90.0)


def test_monte_carlo_default_worst_case_unchanged():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)
    result = run_missed_trade_monte_carlo(baseline, iterations=10)
    assert result.worst_case["total_pnl"] == result.percentile_summary["total_pnl"]["p5"]
    assert result.worst_case["max_drawdown_pnl"] == result.percentile_summary["max_drawdown_pnl"]["p95"]


# ---------------------------------------------------------------------------
# Task 042B2 - Combined Missed-Trade + Slippage Monte Carlo
# ---------------------------------------------------------------------------


def test_combined_monte_carlo_returns_structured_result():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    result = run_combined_monte_carlo(strat, df, baseline, iterations=5, base_seed=42)
    assert isinstance(result, MonteCarloResult)
    assert result.test_name == "combined_slippage_missed_trades_mc"


def test_combined_monte_carlo_iterations_count():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    result = run_combined_monte_carlo(strat, df, baseline, iterations=7, base_seed=42)
    assert result.iterations == 7
    assert len(result.all_metrics) == 7


def test_combined_monte_carlo_deterministic():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    r1 = run_combined_monte_carlo(strat, df, baseline, iterations=10, base_seed=42)
    r2 = run_combined_monte_carlo(strat, df, baseline, iterations=10, base_seed=42)

    assert r1.percentile_summary == r2.percentile_summary
    assert r1.worst_case == r2.worst_case


def test_combined_monte_carlo_seed_divergence():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    r1 = run_combined_monte_carlo(strat, df, baseline, iterations=10, base_seed=42)
    r2 = run_combined_monte_carlo(strat, df, baseline, iterations=10, base_seed=99)

    assert r1.percentile_summary != r2.percentile_summary


def test_combined_monte_carlo_no_baseline_mutation():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    metrics_before = dict(baseline.metrics)
    trades_len_before = len(baseline.trades)

    run_combined_monte_carlo(strat, df, baseline, iterations=5, base_seed=42)

    assert baseline.metrics == metrics_before
    assert len(baseline.trades) == trades_len_before


def test_combined_monte_carlo_percentile_summary():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    result = run_combined_monte_carlo(strat, df, baseline, iterations=5, base_seed=42)
    assert "total_pnl" in result.percentile_summary
    assert "p50" in result.percentile_summary["total_pnl"]


def test_combined_monte_carlo_custom_percentiles():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    result = run_combined_monte_carlo(strat, df, baseline, iterations=5, base_seed=42, percentiles=(1.0, 99.0))
    assert "p1" in result.percentile_summary["total_pnl"]
    assert "p99" in result.percentile_summary["total_pnl"]
    assert result.percentiles_used == (1.0, 99.0)


def test_combined_monte_carlo_assumptions():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    result = run_combined_monte_carlo(
        strat, df, baseline, iterations=5, base_slippage_ticks=1.5,
        perturbation_pct=0.3, miss_probability=0.15, base_seed=77
    )
    
    a = result.assumptions
    assert a["method"] == "combined_slippage_missed_trades"
    assert a["base_slippage_ticks"] == 1.5
    assert a["perturbation_pct"] == 0.3
    assert a["miss_probability"] == 0.15
    assert a["base_seed"] == 77


def test_combined_monte_carlo_reuses_stress_random_missed_trades():
    from unittest.mock import patch, MagicMock
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    mock_stress_res = MagicMock()
    mock_stress_res.stressed_metrics = baseline.metrics

    with patch("validation_engine.monte_carlo.stress_random_missed_trades", return_value=mock_stress_res) as mock_stress:
        run_combined_monte_carlo(strat, df, baseline, iterations=5, base_seed=42)
        assert mock_stress.call_count == 5


def test_combined_monte_carlo_reuses_run_backtest():
    from unittest.mock import patch
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    with patch("validation_engine.monte_carlo.run_backtest", return_value=baseline) as mock_run:
        run_combined_monte_carlo(strat, df, baseline, iterations=5, base_seed=42)
        assert mock_run.call_count == 5


def test_combined_monte_carlo_zero_iterations_safe_behavior():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)
    
    result = run_combined_monte_carlo(strat, df, baseline, iterations=0)
    assert len(result.warnings) > 0
    assert "No metrics collected" in result.warnings[0]


def test_combined_monte_carlo_invalid_miss_probability_rejected_or_clamped():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)
    
    # Should clamp -1.5 to 0.0 and 2.5 to 1.0
    r1 = run_combined_monte_carlo(strat, df, baseline, iterations=2, miss_probability=-1.5)
    assert r1.assumptions["miss_probability"] == 0.0
    
    r2 = run_combined_monte_carlo(strat, df, baseline, iterations=2, miss_probability=2.5)
    assert r2.assumptions["miss_probability"] == 1.0


def test_combined_monte_carlo_invalid_slippage_range_rejected_or_clamped():
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)
    
    # Should clamp -0.5 to 0.0
    r1 = run_combined_monte_carlo(strat, df, baseline, iterations=2, perturbation_pct=-0.5)
    assert r1.assumptions["perturbation_pct"] == 0.0


def test_combined_monte_carlo_run_backtest_receives_perturbed_slippage():
    from unittest.mock import patch
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)
    
    with patch("validation_engine.monte_carlo.run_backtest", return_value=baseline) as mock_run:
        # base_slippage=10.0, perturbation_pct=0.5 -> slip between 5.0 and 15.0
        run_combined_monte_carlo(
            strat, df, baseline, iterations=10,
            base_slippage_ticks=10.0, perturbation_pct=0.5
        )
        
        calls = mock_run.call_args_list
        for call in calls:
            kwargs = call.kwargs
            assert "slippage_ticks" in kwargs
            assert 5.0 <= kwargs["slippage_ticks"] <= 15.0


# ---------------------------------------------------------------------------
# Bootstrap Monte Carlo (Task 057A-Impl)
# ---------------------------------------------------------------------------


def test_bootstrap_mc_deterministic():
    """Same baseline + seed must produce identical bootstrap results."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    r1 = run_bootstrap_monte_carlo(baseline, iterations=20, base_seed=42)
    r2 = run_bootstrap_monte_carlo(baseline, iterations=20, base_seed=42)
    assert r1.percentile_summary == r2.percentile_summary
    assert r1.confidence_intervals == r2.confidence_intervals


def test_bootstrap_mc_structured_output():
    """Result must have all MonteCarloResult fields + confidence_intervals."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    result = run_bootstrap_monte_carlo(baseline, iterations=10, base_seed=1)
    assert isinstance(result, MonteCarloResult)
    assert result.test_name == "bootstrap"
    assert result.iterations == 10
    assert isinstance(result.percentile_summary, dict)
    assert isinstance(result.confidence_intervals, dict)
    for key in ("total_pnl", "profit_factor", "max_drawdown_pnl"):
        assert key in result.confidence_intervals
        assert "ci_lower" in result.confidence_intervals[key]
        assert "ci_upper" in result.confidence_intervals[key]
        assert "ci_mean" in result.confidence_intervals[key]
        assert result.confidence_intervals[key]["ci_lower"] <= result.confidence_intervals[key]["ci_upper"]


def test_bootstrap_mc_zero_trades():
    """Zero baseline trades must produce vacuous result with warning."""
    df = _make_test_df(10)
    strat = Strategy(name="empty")
    baseline = run_backtest(strat, df)

    result = run_bootstrap_monte_carlo(baseline, iterations=10)
    assert len(result.warnings) >= 1
    assert "zero trades" in result.warnings[0].lower()
    assert result.confidence_intervals is None


def test_bootstrap_mc_single_trade():
    """Single trade must still bootstrap (all resamples have 1 element)."""
    from core.models.backtest_result import BacktestResult, Trade
    from backtest_engine.metrics import compute_metrics

    t = Trade(pd.Timestamp("2024-01-01 09:30"), pd.Timestamp("2024-01-01 10:00"),
              "long", 100.0, 105.0, 1, 5.0, "signal")
    baseline = BacktestResult(trades=[t], metrics=compute_metrics([t]),
                              assumptions={}, warnings=[])
    result = run_bootstrap_monte_carlo(baseline, iterations=100, base_seed=1)
    assert result.iterations == 100
    assert result.confidence_intervals is not None


def test_bootstrap_mc_does_not_mutate():
    """Baseline trades must be unchanged."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)
    trades_before = [t.pnl for t in baseline.trades]
    metrics_before = dict(baseline.metrics)

    run_bootstrap_monte_carlo(baseline, iterations=10, base_seed=1)
    assert [t.pnl for t in baseline.trades] == trades_before
    assert baseline.metrics == metrics_before


def test_bootstrap_mc_no_global_rng_mutation():
    """Bootstrap must not mutate global random state."""
    import random
    state_before = random.getstate()
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    run_bootstrap_monte_carlo(baseline, iterations=10, base_seed=1)
    state_after = random.getstate()
    assert state_before == state_after


def test_bootstrap_mc_invalid_iterations():
    """iterations <= 0 must raise ValueError."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)
    with pytest.raises(ValueError, match="iterations"):
        run_bootstrap_monte_carlo(baseline, iterations=0)
    with pytest.raises(ValueError, match="iterations"):
        run_bootstrap_monte_carlo(baseline, iterations=-5)


def test_bootstrap_mc_invalid_confidence_level():
    """confidence_level outside (0, 1) must raise ValueError."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)
    with pytest.raises(ValueError, match="confidence_level"):
        run_bootstrap_monte_carlo(baseline, iterations=10, confidence_level=0.0)
    with pytest.raises(ValueError, match="confidence_level"):
        run_bootstrap_monte_carlo(baseline, iterations=10, confidence_level=1.0)
    with pytest.raises(ValueError, match="confidence_level"):
        run_bootstrap_monte_carlo(baseline, iterations=10, confidence_level=1.5)


def test_bootstrap_mc_ci_lower_le_upper():
    """CI lower must be <= CI upper for each metric."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)
    result = run_bootstrap_monte_carlo(baseline, iterations=50, base_seed=1)
    for key, ci in result.confidence_intervals.items():
        assert ci["ci_lower"] <= ci["ci_upper"], f"{key}: lower={ci['ci_lower']} > upper={ci['ci_upper']}"


def test_bootstrap_mc_existing_mc_unchanged():
    """Existing MC functions must still pass and produce valid output."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    r = run_missed_trade_monte_carlo(baseline, iterations=10)
    assert isinstance(r, MonteCarloResult)
    assert r.confidence_intervals is None  # not set by non-bootstrap MC



# ---------------------------------------------------------------------------
# Worst-case equity curve (Task 063D-Impl)
# ---------------------------------------------------------------------------


def test_worst_case_equity_default_none():
    """MonteCarloResult.worst_case_equity_curve must be None by default."""
    r = MonteCarloResult(test_name="test", iterations=0)
    assert r.worst_case_equity_curve is None


def test_worst_case_equity_collected_when_enabled():
    """Opt-in collect_worst_case_equity=True must populate the curve."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)
    r = run_missed_trade_monte_carlo(
        baseline,
        iterations=10,
        miss_probability=0.1,
        base_seed=42,
        collect_worst_case_equity=True,
    )
    assert r.worst_case_equity_curve is not None
    assert len(r.worst_case_equity_curve) >= 1
    assert r.worst_case_equity_curve[0] >= 0.0  # initial capital
    assert r.worst_case_equity_curve_type == "trade_step"
    assert any("trade-step" in w for w in r.warnings)


def test_worst_case_equity_not_collected_when_disabled():
    """Default collect_worst_case_equity=False must NOT populate the curve."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)
    r = run_missed_trade_monte_carlo(
        baseline,
        iterations=10,
        miss_probability=0.1,
        base_seed=42,
        collect_worst_case_equity=False,
    )
    assert r.worst_case_equity_curve is None


def test_worst_case_equity_deterministic():
    """Same seed must produce identical worst-case equity curves."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)
    r1 = run_missed_trade_monte_carlo(
        baseline, iterations=10, miss_probability=0.1,
        base_seed=42, collect_worst_case_equity=True,
    )
    r2 = run_missed_trade_monte_carlo(
        baseline, iterations=10, miss_probability=0.1,
        base_seed=42, collect_worst_case_equity=True,
    )
    assert r1.worst_case_equity_curve == r2.worst_case_equity_curve


def test_worst_case_equity_zero_trades_vacuously_empty():
    """Zero-trade baseline should not crash."""
    df = _make_test_df(50)
    strat = Strategy(name="empty")
    baseline = run_backtest(strat, df)
    r = run_missed_trade_monte_carlo(
        baseline, iterations=5, miss_probability=0.1,
        base_seed=42, collect_worst_case_equity=True,
    )
    assert r.worst_case_equity_curve is None


def test_worst_iteration_tie_break_prefers_lower_pnl_then_higher_drawdown():
    """Worst selection must use PnL first, then absolute drawdown."""
    current = {"total_pnl": -100.0, "max_drawdown_pnl": 25.0}

    assert _is_worse_iteration(
        {"total_pnl": -101.0, "max_drawdown_pnl": 1.0},
        current,
    )
    assert _is_worse_iteration(
        {"total_pnl": -100.0, "max_drawdown_pnl": 30.0},
        current,
    )
    assert not _is_worse_iteration(
        {"total_pnl": -100.0, "max_drawdown_pnl": 25.0},
        current,
    )


def test_worst_case_equity_uses_trade_step_curve_for_selected_worst_iteration(monkeypatch):
    """Collection must keep the selected worst iteration curve, not a percentile curve."""
    trades = [
        Trade(pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-01 00:01"), "long", 1.0, 1.0, pnl=10.0),
        Trade(pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-01 00:02"), "long", 1.0, 1.0, pnl=-50.0),
    ]
    baseline = BacktestResult(
        trades=trades,
        metrics={"total_trades": 2, "total_pnl": -40.0, "max_drawdown_pnl": 50.0},
        assumptions={"initial_capital": 1000.0},
    )
    calls = [
        {"total_trades": 2, "total_pnl": 10.0, "max_drawdown_pnl": 5.0},
        {"total_trades": 1, "total_pnl": -50.0, "max_drawdown_pnl": 50.0},
        {"total_trades": 2, "total_pnl": -50.0, "max_drawdown_pnl": 60.0},
    ]

    def fake_stress_random_missed_trades(_baseline, *, miss_probability, seed):
        from types import SimpleNamespace
        metrics = calls[seed]
        if seed == 1:
            assumptions = {"stressed_trade_count": 1, "baseline_trade_count": 2}
        else:
            assumptions = {"stressed_trade_count": 2, "baseline_trade_count": 2}
        return SimpleNamespace(stressed_metrics=metrics, assumptions=assumptions)

    random_sequences = {
        0: [0.2, 0.2],  # both trades survive -> 1000, 1010, 960
        1: [0.0, 0.2],  # only second survives -> 1000, 950
        2: [0.2, 0.2],  # both survive; tie on PnL, worse DD -> selected
    }

    class FakeRandom:
        def __init__(self, seed):
            self.values = iter(random_sequences[seed])

        def random(self):
            return next(self.values)

    monkeypatch.setattr("validation_engine.monte_carlo.stress_random_missed_trades", fake_stress_random_missed_trades)
    monkeypatch.setattr("validation_engine.monte_carlo.random.Random", FakeRandom)

    result = run_missed_trade_monte_carlo(
        baseline,
        iterations=3,
        miss_probability=0.1,
        base_seed=0,
        collect_worst_case_equity=True,
    )

    assert result.worst_case_equity_curve == [1000.0, 1010.0, 960.0]
    assert result.worst_case_equity_curve_type == "trade_step"
