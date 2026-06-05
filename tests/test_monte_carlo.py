"""Tests for Monte Carlo simulation engine — Task 015."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.models.strategy import Condition, Strategy, StrategyBlock
from backtest_engine.runner import run_backtest
from validation_engine.monte_carlo import (
    MonteCarloResult,
    run_missed_trade_monte_carlo,
    run_slippage_monte_carlo,
    run_combined_monte_carlo,
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

