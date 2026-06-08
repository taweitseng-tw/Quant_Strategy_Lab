"""Tests for stress test engine — Task 014."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.models.backtest_result import BacktestResult, Trade
from core.models.strategy import Condition, Strategy, StrategyBlock
from backtest_engine.runner import run_backtest
from backtest_engine.metrics import compute_metrics
from validation_engine.stress_test import (
    StressTestResult,
    _perturb_ohlc_price_noise,
    stress_commission_multiplier,
    stress_price_noise,
    stress_random_missed_trades,
    stress_remove_best_n_trades,
    stress_slippage_multiplier,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_test_df(n_bars: int = 200) -> pd.DataFrame:
    """Create uptrend OHLCV data that produces trades under SMA strategy."""
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


def _make_sma_strategy(sma_period: int = 10) -> Strategy:
    return Strategy(
        name="stress_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": sma_period}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": sma_period}, operator="<"),
        ], logic="AND"),
    )


# ---------------------------------------------------------------------------
# Commission stress
# ---------------------------------------------------------------------------


def test_commission_stress_worsens_pnl():
    """2× commission must not increase total PnL."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    result = stress_commission_multiplier(strat, df, baseline, multiplier=2.0)

    assert isinstance(result, StressTestResult)
    assert result.test_name == "commission_2.0x"
    assert result.passed
    assert result.stressed_metrics["total_pnl"] <= baseline.metrics["total_pnl"] + 1e-9
    assert result.degradation["total_pnl"] <= 1e-9


def test_commission_stress_structured_output():
    """Stress result must contain all required fields."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    result = stress_commission_multiplier(strat, df, baseline)

    assert result.test_name
    assert isinstance(result.passed, bool)
    assert isinstance(result.baseline_metrics, dict)
    assert isinstance(result.stressed_metrics, dict)
    assert isinstance(result.degradation, dict)
    assert isinstance(result.assumptions, dict)
    assert isinstance(result.warnings, list)


def test_commission_stress_does_not_mutate_baseline():
    """Baseline BacktestResult must be unchanged after stress test."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    metrics_before = dict(baseline.metrics)
    trades_before = len(baseline.trades)

    stress_commission_multiplier(strat, df, baseline, multiplier=2.0)

    assert baseline.metrics == metrics_before
    assert len(baseline.trades) == trades_before


# ---------------------------------------------------------------------------
# Slippage stress
# ---------------------------------------------------------------------------


def test_slippage_stress_worsens_pnl():
    """2× slippage must not increase total PnL."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    result = stress_slippage_multiplier(strat, df, baseline, multiplier=2.0)

    assert isinstance(result, StressTestResult)
    assert result.test_name == "slippage_2.0x"
    assert result.stressed_metrics["total_pnl"] <= baseline.metrics["total_pnl"] + 1e-9


def test_slippage_stress_does_not_mutate_baseline():
    """Baseline must be unchanged."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, slippage_ticks=1.0)

    metrics_before = dict(baseline.metrics)
    stress_slippage_multiplier(strat, df, baseline, multiplier=2.0)
    assert baseline.metrics == metrics_before


# ---------------------------------------------------------------------------
# Random missed trade stress
# ---------------------------------------------------------------------------


def test_random_missed_trades_is_deterministic():
    """Same seed must produce identical stress results."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    r1 = stress_random_missed_trades(baseline, seed=42)
    r2 = stress_random_missed_trades(baseline, seed=42)

    assert r1.stressed_metrics == r2.stressed_metrics
    assert r1.degradation == r2.degradation
    assert r1.passed == r2.passed


def test_random_missed_trades_reduces_trade_count():
    """After missing trades, trade count must be ≤ baseline."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    if baseline.metrics["total_trades"] > 5:
        result = stress_random_missed_trades(baseline, miss_probability=0.2, seed=1)
        assert result.stressed_metrics["total_trades"] <= baseline.metrics["total_trades"]


def test_random_missed_trades_does_not_mutate_baseline():
    """Baseline trade list must be unchanged."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    trades_before = [t.pnl for t in baseline.trades]
    stress_random_missed_trades(baseline, seed=42)
    trades_after = [t.pnl for t in baseline.trades]

    assert trades_before == trades_after


def test_random_missed_trades_structured_output():
    """Result must have all required fields."""
    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    result = stress_random_missed_trades(baseline, seed=42)

    assert result.test_name == "random_missed_trades"
    assert isinstance(result.passed, bool)
    assert "seed" in result.assumptions


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_stress_no_baseline_trades():
    """Stress test with zero baseline trades must pass vacuously."""
    df = _make_test_df(10)
    strat = Strategy(name="empty")
    baseline = run_backtest(strat, df)

    assert baseline.metrics["total_trades"] == 0

    result = stress_commission_multiplier(strat, df, baseline, multiplier=2.0)
    assert result.passed  # vacuously true
    assert len(result.warnings) >= 1


def test_stress_pass_fail_thresholds():
    """When 2× commission does not worsen PnL (e.g. PnL was negative),
    the test should still pass (PnL did not improve)."""
    # Create data that produces negative PnL.
    n = 100
    times = pd.date_range("2024-01-02 08:30", periods=n, freq="1min")
    # Downtrend: decreasing close.
    close = np.linspace(150.0, 100.0, n)
    df = pd.DataFrame({
        "datetime": times,
        "open":  close - 0.5,
        "high":  close + 1.0,
        "low":   close - 1.0,
        "close": close,
        "volume": [1000] * n,
    })

    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    result = stress_commission_multiplier(strat, df, baseline, multiplier=3.0)

    # PnL must not improve (i.e. must not become less negative).
    assert result.stressed_metrics["total_pnl"] <= baseline.metrics["total_pnl"] + 1e-9


# ---------------------------------------------------------------------------
# One-bar execution delay stress
# ---------------------------------------------------------------------------


def test_one_bar_delay_runs_and_produces_structured_result():
    """One-bar delay must produce a valid StressTestResult with degradation info.

    Note: unlike cost-based stresses, shifting prices can improve or worsen
    PnL depending on the price path — the stress is informational, not
    a hard pass/fail on PnL direction.
    """
    from validation_engine.stress_test import stress_one_bar_delay

    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    result = stress_one_bar_delay(strat, df, baseline)

    assert isinstance(result, StressTestResult)
    assert result.test_name == "one_bar_delay"
    assert isinstance(result.passed, bool)
    assert result.stressed_metrics is not None
    assert result.stressed_metrics["total_trades"] >= 0
    assert "total_pnl" in result.degradation  # degradation is computed


def test_one_bar_delay_structured_output():
    """Result must have all required fields and correct assumptions."""
    from validation_engine.stress_test import stress_one_bar_delay

    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    result = stress_one_bar_delay(strat, df, baseline)

    assert result.test_name
    assert isinstance(result.passed, bool)
    assert result.assumptions["delay_bars"] == 1
    assert result.assumptions["method"] == "engine_native_delay"


def test_one_bar_delay_does_not_mutate_baseline():
    """Baseline must be unchanged after delay stress."""
    from validation_engine.stress_test import stress_one_bar_delay

    df = _make_test_df(200)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df, commission=2.0)

    metrics_before = dict(baseline.metrics)
    stress_one_bar_delay(strat, df, baseline)
    assert baseline.metrics == metrics_before


def test_one_bar_delay_too_short_dataframe():
    """DataFrame with < 2 bars must return early with a warning."""
    from validation_engine.stress_test import stress_one_bar_delay

    df = _make_test_df(1)
    strat = _make_sma_strategy(10)
    baseline = run_backtest(strat, df)

    result = stress_one_bar_delay(strat, df, baseline)
    assert result.passed
    assert any("too short" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# Remove Best N Trades stress test (Task 056E-Impl / 056E-Impl-Fix)
# ---------------------------------------------------------------------------


def _make_synthetic_baseline(pnls: list[float]) -> BacktestResult:
    """Build a deterministic baseline from explicit trade PnL values."""
    import math
    trades = [
        Trade(
            entry_time=pd.Timestamp("2024-01-01 09:30"),
            exit_time=pd.Timestamp("2024-01-01 10:00"),
            direction="long",
            entry_price=100.0,
            exit_price=110.0,
            quantity=1,
            pnl=pnl,
            exit_reason="signal",
        )
        for pnl in pnls
    ]
    metrics = compute_metrics(trades)
    return BacktestResult(
        trades=trades,
        metrics=metrics,
        assumptions={},
        warnings=[],
    )


def test_remove_best_n_trades_deterministic():
    """Same baseline must produce identical results."""
    baseline = _make_synthetic_baseline([100.0, 50.0, -20.0, -10.0])
    r1 = stress_remove_best_n_trades(baseline, n=1)
    r2 = stress_remove_best_n_trades(baseline, n=1)
    assert r1.stressed_metrics == r2.stressed_metrics
    assert r1.degradation == r2.degradation
    assert r1.passed == r2.passed


def test_remove_best_n_trades_worsens_pnl():
    """PnL must not improve after removing best trades."""
    baseline = _make_synthetic_baseline([100.0, 50.0, -20.0, -10.0])
    # baseline total_pnl=120, remove best (100) -> stressed_pnl=20
    result = stress_remove_best_n_trades(baseline, n=1)
    assert result.stressed_metrics["total_pnl"] == pytest.approx(20.0)
    assert result.stressed_metrics["total_pnl"] <= baseline.metrics["total_pnl"]


def test_remove_best_n_trades_exact_metrics():
    """Verify exact degradation and pnl_loss_ratio against known values."""
    baseline = _make_synthetic_baseline([100.0, 50.0, -20.0, -10.0])
    result = stress_remove_best_n_trades(baseline, n=1)

    # baseline total_pnl=120, stressed=20
    assert result.stressed_metrics["total_pnl"] == pytest.approx(20.0)
    assert result.degradation["total_pnl"] == pytest.approx(-0.833333, abs=1e-5)
    assert result.assumptions["pnl_loss_ratio"] == pytest.approx(0.833333, abs=1e-5)
    assert result.assumptions["removed_count"] == 1
    assert result.assumptions["surviving_count"] == 3


def test_remove_best_n_trades_fails_above_threshold():
    """Fails when pnl_loss_ratio > degradation_threshold."""
    baseline = _make_synthetic_baseline([100.0, 50.0, -20.0, -10.0])
    # pnl_loss_ratio ~0.833, threshold 0.30 -> fail
    result = stress_remove_best_n_trades(baseline, n=1, degradation_threshold=0.30)
    assert not result.passed


def test_remove_best_n_trades_passes_within_threshold():
    """Passes when pnl_loss_ratio <= degradation_threshold."""
    baseline = _make_synthetic_baseline([100.0, 50.0, -20.0, -10.0])
    # pnl_loss_ratio ~0.833, threshold 0.99 -> pass
    result = stress_remove_best_n_trades(baseline, n=1, degradation_threshold=0.99)
    assert result.passed
    assert "pnl_loss_ratio" in result.assumptions


def test_remove_best_n_trades_zero_trades():
    """Empty baseline -> vacuous pass with warning."""
    baseline = _make_synthetic_baseline([])
    assert baseline.metrics["total_trades"] == 0

    result = stress_remove_best_n_trades(baseline, n=2)
    assert result.passed
    assert len(result.warnings) >= 1
    assert "zero trades" in result.warnings[0].lower()


def test_remove_best_n_trades_insufficient_trades_fails():
    """0 < trades <= n -> passed=False with insufficient_trades."""
    baseline = _make_synthetic_baseline([100.0, 50.0])
    # 2 trades, n=5 -> insufficient
    result = stress_remove_best_n_trades(baseline, n=5)
    assert not result.passed
    assert result.assumptions.get("insufficient_trades") is True


def test_remove_best_n_trades_does_not_mutate_baseline():
    """Baseline trade list must be unchanged."""
    baseline = _make_synthetic_baseline([100.0, 50.0, -20.0, -10.0])
    trades_before = [t.pnl for t in baseline.trades]
    stress_remove_best_n_trades(baseline, n=1)
    trades_after = [t.pnl for t in baseline.trades]
    assert trades_before == trades_after


def test_remove_best_n_trades_structured_output():
    """Result must have all required fields."""
    baseline = _make_synthetic_baseline([100.0, 50.0, -20.0, -10.0])
    result = stress_remove_best_n_trades(baseline, n=1)

    assert result.test_name == "remove_best_n_trades"
    assert isinstance(result.passed, bool)
    assert isinstance(result.baseline_metrics, dict)
    assert isinstance(result.stressed_metrics, dict)
    assert isinstance(result.degradation, dict)
    assert isinstance(result.assumptions, dict)
    assert "pnl_loss_ratio" in result.assumptions
    assert "removed_count" in result.assumptions
    assert isinstance(result.warnings, list)


def test_remove_best_n_trades_negative_n_raises():
    """n < 0 raises ValueError."""
    baseline = _make_synthetic_baseline([100.0])
    with pytest.raises(ValueError, match="non-negative"):
        stress_remove_best_n_trades(baseline, n=-1)


def test_remove_best_n_trades_negative_threshold_raises():
    """degradation_threshold < 0 raises ValueError."""
    baseline = _make_synthetic_baseline([100.0])
    with pytest.raises(ValueError, match="non-negative"):
        stress_remove_best_n_trades(baseline, n=2, degradation_threshold=-0.1)


# ---------------------------------------------------------------------------
# Price-noise stress test (Task 062D-Impl)
# ---------------------------------------------------------------------------


def test_price_noise_returns_expected_structure():
    """stress_price_noise must return a StressTestResult with expected fields."""
    df = _make_test_df(200)
    strat = _make_sma_strategy()
    baseline = run_backtest(strat, df, commission=2.0)
    result = stress_price_noise(baseline, noise_pct=0.005, iterations=5,
                                strategy=strat, df=df)
    assert result.test_name == "price_noise"
    assert isinstance(result.stressed_metrics, dict)
    assert "total_pnl" in result.stressed_metrics
    assert "median_total_pnl" in result.stressed_metrics
    assert "survival_rate" in result.stressed_metrics
    assert "pnl_degradation_ratio" in result.degradation
    assert result.assumptions["method"] == "ohlc_preserving_gaussian_noise"
    assert result.assumptions["research_only"] is True


def test_price_noise_deterministic():
    """Same seed must produce identical results."""
    df = _make_test_df(200)
    strat = _make_sma_strategy()
    baseline = run_backtest(strat, df, commission=2.0)
    r1 = stress_price_noise(baseline, noise_pct=0.005, iterations=10, base_seed=42,
                            strategy=strat, df=df)
    r2 = stress_price_noise(baseline, noise_pct=0.005, iterations=10, base_seed=42,
                            strategy=strat, df=df)
    assert r1.stressed_metrics == r2.stressed_metrics
    assert r1.degradation == r2.degradation


def test_price_noise_zero_noise_identity():
    """noise_pct=0 must produce identical results (no perturbation)."""
    df = _make_test_df(200)
    strat = _make_sma_strategy()
    baseline = run_backtest(strat, df, commission=2.0)
    result = stress_price_noise(baseline, noise_pct=0.0, iterations=5,
                                strategy=strat, df=df)

    assert result.stressed_metrics["median_total_pnl"] == pytest.approx(
        baseline.metrics["total_pnl"]
    )
    assert result.stressed_metrics["median_profit_factor"] == pytest.approx(
        baseline.metrics["profit_factor"]
    )
    if baseline.metrics["total_pnl"] > 0:
        assert result.degradation["pnl_degradation_ratio"] == pytest.approx(1.0)
        assert not any("undefined" in w for w in result.warnings)


def test_price_noise_helper_preserves_ohlc_constraints_and_volume():
    """Perturbed bars must preserve OHLC invariants and leave volume unchanged."""
    df = _make_test_df(200)
    perturbed = _perturb_ohlc_price_noise(df, noise_pct=0.02, seed=123)

    assert (perturbed["high"] >= perturbed[["open", "close"]].max(axis=1)).all()
    assert (perturbed["low"] <= perturbed[["open", "close"]].min(axis=1)).all()
    assert (perturbed["high"] >= perturbed["low"]).all()
    pd.testing.assert_series_equal(perturbed["volume"], df["volume"])


def test_price_noise_nonzero_perturbation():
    """Non-zero noise must produce different results than baseline."""
    df = _make_test_df(200)
    strat = _make_sma_strategy()
    baseline = run_backtest(strat, df, commission=2.0)
    result = stress_price_noise(baseline, noise_pct=0.02, iterations=10,
                                strategy=strat, df=df)
    # With 2% noise, avg PnL should differ from baseline
    assert abs(result.degradation.get("total_pnl", 0.0)) > 0.001


def test_price_noise_baseline_pnl_warning():
    """Near-zero baseline PnL should produce a warning."""
    df = _make_test_df(50)
    strat = Strategy(name="empty")
    baseline = run_backtest(strat, df)
    result = stress_price_noise(baseline, noise_pct=0.005, iterations=5,
                                strategy=strat, df=df)
    assert len(result.warnings) > 0
    assert any("Baseline PnL" in w for w in result.warnings)
    assert result.degradation["pnl_degradation_ratio"] is None
    assert result.degradation["total_pnl"] is None
    assert result.passed is False


def test_price_noise_invalid_noise_pct():
    """noise_pct outside [0, 0.05] must raise ValueError."""
    df = _make_test_df(200)
    strat = _make_sma_strategy()
    baseline = run_backtest(strat, df)
    with pytest.raises(ValueError, match="noise_pct"):
        stress_price_noise(baseline, noise_pct=0.1, iterations=5,
                           strategy=strat, df=df)
    with pytest.raises(ValueError, match="noise_pct"):
        stress_price_noise(baseline, noise_pct=-0.001, iterations=5,
                           strategy=strat, df=df)


def test_price_noise_invalid_iterations():
    """iterations must be positive."""
    df = _make_test_df(200)
    strat = _make_sma_strategy()
    baseline = run_backtest(strat, df)
    with pytest.raises(ValueError, match="iterations"):
        stress_price_noise(baseline, noise_pct=0.005, iterations=0,
                           strategy=strat, df=df)
