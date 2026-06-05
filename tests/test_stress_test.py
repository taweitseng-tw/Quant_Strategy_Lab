"""Tests for stress test engine — Task 014."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.models.strategy import Condition, Strategy, StrategyBlock
from backtest_engine.runner import run_backtest
from validation_engine.stress_test import (
    StressTestResult,
    stress_commission_multiplier,
    stress_random_missed_trades,
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
    assert result.assumptions["method"] == "price_shift_forward"
    assert result.assumptions["stressed_rows"] == result.assumptions["baseline_rows"] - 1


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
