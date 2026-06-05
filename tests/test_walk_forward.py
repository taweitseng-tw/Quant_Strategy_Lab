"""Tests for fixed-window walk-forward validator — Task 016."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.models.strategy import Condition, Strategy, StrategyBlock
from backtest_engine.runner import run_backtest
from validation_engine.walk_forward import (
    WalkForwardResult,
    WalkForwardWindow,
    walk_forward,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_test_df(n_bars: int = 1000) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="1min")
    # Mild uptrend to produce some positive-window results.
    close = 100.0 + np.cumsum(rng.normal(0.02, 0.5, n_bars))
    close = np.maximum(close, 10.0)
    noise = rng.uniform(0.3, 1.5, n_bars)
    return pd.DataFrame({
        "datetime": times,
        "open":  close - noise * 0.3,
        "high":  close + noise,
        "low":   close - noise,
        "close": close,
        "volume": rng.integers(500, 5000, n_bars),
    })


def _make_sma_strategy(period: int = 10) -> Strategy:
    return Strategy(
        name="wf_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": period}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": period}, operator="<"),
        ], logic="AND"),
    )


# ---------------------------------------------------------------------------
# Window construction
# ---------------------------------------------------------------------------


def test_walk_forward_correct_window_count():
    """1000 bars, train=400, test=100 → 6 non-overlapping windows.
    (start=0..399 train, 400..499 test; advance by 100; last: 900..999)"""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=400, test_bars=100)

    # Windows at start=0, 100, 200, 300, 400, 500 → 6 windows
    assert result.window_count == 6
    assert len(result.windows) == 6


def test_walk_forward_step_size_controls_overlap():
    """step_bars=50 with train=200, test=100 produces overlapping windows."""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=200, test_bars=100, step_bars=50)

    # start=0, 50, 100, ... until start+200+100 > 1000 → 700 → 15 windows
    # Actually: 0, 50, 100, ..., 700 → 15 windows (0..14)
    assert result.window_count >= 10  # many overlapping windows


def test_walk_forward_no_overlap_between_train_and_test():
    """Train and test segments within each window must not overlap."""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=300, test_bars=100)

    for w in result.windows:
        train_end = pd.Timestamp(w.train_end)
        test_start = pd.Timestamp(w.test_start)
        assert train_end < test_start  # train ends before test begins


def test_walk_forward_chronological_order():
    """Windows must be chronologically ordered."""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=200, test_bars=100)

    for i in range(1, len(result.windows)):
        prev = pd.Timestamp(result.windows[i - 1].test_end)
        curr = pd.Timestamp(result.windows[i].test_start)
        assert prev <= curr  # non-decreasing


def test_walk_forward_window_metadata():
    """Each window must have train/test start/end and bar counts."""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=200, test_bars=100)

    for w in result.windows:
        assert isinstance(w, WalkForwardWindow)
        assert w.train_bars == 200
        assert w.test_bars == 100
        assert w.train_start
        assert w.train_end
        assert w.test_start
        assert w.test_end
        assert isinstance(w.metrics, dict)
        assert isinstance(w.passed, bool)


# ---------------------------------------------------------------------------
# Pass rate and aggregate
# ---------------------------------------------------------------------------


def test_walk_forward_pass_rate_calculation():
    """pass_rate must equal pass_count / window_count."""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=300, test_bars=100)

    assert result.pass_count == sum(1 for w in result.windows if w.passed)
    assert result.pass_rate == pytest.approx(
        result.pass_count / result.window_count if result.window_count > 0 else 0.0
    )


def test_walk_forward_aggregate_metrics():
    """Aggregate must include mean, median, min, max for key metrics."""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=300, test_bars=100)

    for key in ("total_pnl", "profit_factor", "max_drawdown_pnl", "win_rate", "avg_trade", "total_trades"):
        assert key in result.aggregate_metrics
        agg = result.aggregate_metrics[key]
        assert "mean" in agg
        assert "median" in agg
        assert "min" in agg
        assert "max" in agg
        assert agg["min"] <= agg["max"]


def test_walk_forward_structured_result():
    """WalkForwardResult must have all required top-level fields."""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=200, test_bars=100)

    assert isinstance(result, WalkForwardResult)
    assert result.window_count >= 0
    assert result.pass_count >= 0
    assert 0.0 <= result.pass_rate <= 1.0
    assert isinstance(result.windows, list)
    assert isinstance(result.aggregate_metrics, dict)
    assert isinstance(result.assumptions, dict)
    assert isinstance(result.warnings, list)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_walk_forward_too_short_dataset():
    """Dataset shorter than train+test must return zero windows with warning."""
    df = _make_test_df(50)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=300, test_bars=100)

    assert result.window_count == 0
    assert len(result.warnings) >= 1
    assert "too short" in result.warnings[0].lower()


def test_walk_forward_missing_datetime():
    """DataFrame without datetime column must return zero windows with warning."""
    df = pd.DataFrame({"open": [1.0], "high": [2.0], "low": [0.5], "close": [1.5], "volume": [100]})
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=10, test_bars=5)

    assert result.window_count == 0
    assert any("datetime" in w.lower() for w in result.warnings)


def test_walk_forward_does_not_mutate_source_df():
    """The source DataFrame must be unchanged after walk-forward."""
    df = _make_test_df(1000)
    df_copy = df.copy()
    strat = _make_sma_strategy(10)

    walk_forward(strat, df, train_bars=200, test_bars=100)
    pd.testing.assert_frame_equal(df, df_copy)


def test_walk_forward_pass_rate_bounded():
    """pass_rate must be in [0, 1]."""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=200, test_bars=100)

    assert 0.0 <= result.pass_rate <= 1.0


# ---------------------------------------------------------------------------
# Task 043B1: Enhancements (Pass Criteria + Stability Score)
# ---------------------------------------------------------------------------


def test_walk_forward_default_pass_behavior_unchanged():
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=200, test_bars=100)

    for w in result.windows:
        assert w.passed == (w.metrics.get("total_pnl", 0.0) > 0)


def test_walk_forward_custom_min_total_pnl():
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=200, test_bars=100, pass_criteria={"min_total_pnl": 999999.0})
    for w in result.windows:
        if w.metrics.get("total_pnl", 0.0) < 999999.0:
            assert not w.passed


def test_walk_forward_custom_min_profit_factor():
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=200, test_bars=100, pass_criteria={"min_profit_factor": 2.0})
    for w in result.windows:
        if w.metrics.get("profit_factor", 0.0) < 2.0:
            assert not w.passed


def test_walk_forward_custom_max_drawdown_pnl():
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=200, test_bars=100, pass_criteria={"max_drawdown_pnl": 0.0})
    for w in result.windows:
        if w.metrics.get("max_drawdown_pnl", 0.0) > 0.0:
            assert not w.passed


def test_walk_forward_unknown_pass_criterion_ignored_or_warning():
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=200, test_bars=100, pass_criteria={"unknown_criterion": 100.0})
    assert result.window_count > 0


def test_walk_forward_stability_score_present():
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=200, test_bars=100)
    assert result.window_count >= 2
    if result.stability_score is not None:
        pnls = [w.metrics.get("total_pnl", 0.0) for w in result.windows]
        import statistics
        expected_score = (sum(pnls)/len(pnls)) / statistics.stdev(pnls)
        assert result.stability_score == pytest.approx(expected_score)


def test_walk_forward_stability_score_none_for_one_window():
    df = _make_test_df(400)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=200, test_bars=150)
    assert result.window_count == 1
    assert result.stability_score is None


def test_walk_forward_stability_score_none_when_std_zero():
    df = _make_test_df(1000)
    # Empty strategy -> 0 trades -> 0 PnL for all windows -> std 0
    strat = Strategy("empty")
    result = walk_forward(strat, df, train_bars=200, test_bars=100)
    assert result.window_count > 1
    for w in result.windows:
        assert w.metrics.get("total_pnl", 0.0) == 0.0
    assert result.stability_score is None


def test_walk_forward_result_stability_score_serializable():
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=200, test_bars=100)
    
    import json
    from dataclasses import asdict
    
    # Must not raise an exception
    d = asdict(result)
    s = json.dumps(d)
    assert "stability_score" in s


# ---------------------------------------------------------------------------
# Task 044B: Walk-Forward Efficiency (WFE) Tests
# ---------------------------------------------------------------------------


def test_wf_wfe_disabled():
    """Default calc_wfe=False preserves existing behavior and adds empty fields."""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=200, test_bars=100)
    
    assert result.average_wfe is None
    assert result.median_wfe is None
    assert result.defined_wfe_count == 0
    assert result.undefined_wfe_count == result.window_count
    
    for w in result.windows:
        assert w.wfe is None
        assert w.train_metrics == {}


def test_wf_wfe_calculation():
    """WFE is calculated as test_total_pnl / train_total_pnl."""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    result = walk_forward(strat, df, train_bars=200, test_bars=100, calc_wfe=True)
    
    assert result.window_count > 0
    for w in result.windows:
        assert w.train_metrics != {}
        train_pnl = w.train_metrics.get("total_pnl", 0.0)
        test_pnl = w.metrics.get("total_pnl", 0.0)
        
        if train_pnl > 1e-9:
            assert w.wfe == pytest.approx(test_pnl / train_pnl)
        else:
            assert w.wfe is None


def test_wf_wfe_zero_train_pnl():
    """train_total_pnl == 0 gives wfe=None."""
    df = _make_test_df(1000)
    strat = Strategy("empty")
    result = walk_forward(strat, df, train_bars=200, test_bars=100, calc_wfe=True)
    
    for w in result.windows:
        assert w.train_metrics.get("total_pnl", 0.0) == 0.0
        assert w.wfe is None
        
    assert result.average_wfe is None
    assert result.median_wfe is None
    assert result.defined_wfe_count == 0
    assert result.undefined_wfe_count == result.window_count


def test_wf_wfe_negative_train_pnl():
    """train_total_pnl < 0 gives wfe=None."""
    # Create an inverse strategy that loses money
    df = _make_test_df(1000)
    # Reversing the SMA logic to generate losses
    strat = Strategy(
        name="losing_strat",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator="<"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator=">"),
        ], logic="AND"),
    )
    result = walk_forward(strat, df, train_bars=200, test_bars=100, calc_wfe=True)
    
    for w in result.windows:
        train_pnl = w.train_metrics.get("total_pnl", 0.0)
        if train_pnl < 0:
            assert w.wfe is None


def test_wf_wfe_all_none():
    """If all WFEs are None, aggregate is None."""
    df = _make_test_df(500)
    strat = Strategy("empty")
    result = walk_forward(strat, df, train_bars=200, test_bars=100, calc_wfe=True)
    assert result.average_wfe is None
    assert result.median_wfe is None


def test_wf_wfe_does_not_affect_pass_rate():
    """Running with calc_wfe=True should not change pass results vs calc_wfe=False."""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    
    res_false = walk_forward(strat, df, train_bars=200, test_bars=100, calc_wfe=False)
    res_true = walk_forward(strat, df, train_bars=200, test_bars=100, calc_wfe=True)
    
    assert res_false.pass_rate == res_true.pass_rate
    assert res_false.pass_count == res_true.pass_count
    for w_f, w_t in zip(res_false.windows, res_true.windows):
        assert w_f.passed == w_t.passed
        assert w_f.metrics == w_t.metrics


from unittest import mock

def test_wf_wfe_call_count_disabled():
    """calc_wfe=False calls run_backtest exactly once per window."""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    
    with mock.patch("validation_engine.walk_forward.run_backtest") as mock_run_backtest:
        from types import SimpleNamespace
        mock_run_backtest.return_value = SimpleNamespace(
            strategy=strat.name,
            trades=[],
            metrics={"total_pnl": 100.0},
            equity_curve=[],
            drawdown_curve=[],
            assumptions={}
        )
        
        result = walk_forward(strat, df, train_bars=200, test_bars=100, calc_wfe=False)
        assert mock_run_backtest.call_count == result.window_count


def test_wf_wfe_call_count_enabled():
    """calc_wfe=True calls run_backtest exactly twice per window."""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    
    with mock.patch("validation_engine.walk_forward.run_backtest") as mock_run_backtest:
        from types import SimpleNamespace
        def side_effect(*args, **kwargs):
            return SimpleNamespace(
                strategy=strat.name,
                trades=[],
                metrics={"total_pnl": 100.0},
                equity_curve=[],
                drawdown_curve=[],
                assumptions={}
            )
        mock_run_backtest.side_effect = side_effect
        
        result = walk_forward(strat, df, train_bars=200, test_bars=100, calc_wfe=True)
        assert mock_run_backtest.call_count == result.window_count * 2
        
        # Verify train/test isolation
        for w in result.windows:
            assert w.metrics is not w.train_metrics


def test_wf_wfe_microscopic_train_pnl():
    """train_total_pnl <= 1e-9 gives wfe=None."""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    
    with mock.patch("validation_engine.walk_forward.run_backtest") as mock_run_backtest:
        from types import SimpleNamespace
        
        # We will cycle through microscopic values
        values = [1e-10, 1e-9, -1e-9]
        def side_effect(*args, **kwargs):
            val = values.pop(0) if values else 1e-10
            return SimpleNamespace(
                strategy=strat.name, trades=[],
                metrics={"total_pnl": val},
                equity_curve=[], drawdown_curve=[], assumptions={}
            )
        
        mock_run_backtest.side_effect = side_effect
        result = walk_forward(strat, df, train_bars=200, test_bars=100, calc_wfe=True)
        
        for w in result.windows:
            assert w.wfe is None


def test_wf_wfe_missing_metrics():
    """Missing train or test metrics safely gives wfe=None."""
    df = _make_test_df(1000)
    strat = _make_sma_strategy(10)
    
    with mock.patch("validation_engine.walk_forward.run_backtest") as mock_run_backtest:
        from types import SimpleNamespace
        
        # Alternating missing total_pnl
        # Window 1: Train missing, Test present
        # Window 2: Train present, Test missing
        rets = [
            SimpleNamespace(strategy=strat.name, trades=[], metrics={}, equity_curve=[], drawdown_curve=[], assumptions={}),
            SimpleNamespace(strategy=strat.name, trades=[], metrics={"total_pnl": 100.0}, equity_curve=[], drawdown_curve=[], assumptions={}),
            SimpleNamespace(strategy=strat.name, trades=[], metrics={"total_pnl": 100.0}, equity_curve=[], drawdown_curve=[], assumptions={}),
            SimpleNamespace(strategy=strat.name, trades=[], metrics={}, equity_curve=[], drawdown_curve=[], assumptions={}),
        ]
        
        def side_effect(*args, **kwargs):
            return rets.pop(0) if rets else SimpleNamespace(strategy=strat.name, trades=[], metrics={"total_pnl": 100.0}, equity_curve=[], drawdown_curve=[], assumptions={})
            
        mock_run_backtest.side_effect = side_effect
        result = walk_forward(strat, df, train_bars=200, test_bars=100, calc_wfe=True)
        
        assert result.windows[0].wfe is None
        assert result.windows[1].wfe is None
