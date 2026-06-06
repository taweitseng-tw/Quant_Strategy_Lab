"""Tests for one-bar execution delay stress test — Task 053F."""

import numpy as np
import pandas as pd
import pytest

from core.models.strategy import Condition, Strategy, StrategyBlock
from backtest_engine.runner import run_backtest

def _make_test_df(n_bars: int = 10) -> pd.DataFrame:
    """Create a simple uptrending OHLCV data."""
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="1min")
    close = np.linspace(100.0, 110.0, n_bars)
    return pd.DataFrame({
        "datetime": times,
        "open":  close - 0.1,
        "high":  close + 0.1,
        "low":   close - 0.2,
        "close": close,
        "volume": [1000] * n_bars,
    })

def test_execution_delay_baseline_equivalence():
    """Baseline equivalence: delay=0 behaves identically to default."""
    df = _make_test_df(10)
    strat = Strategy(
        name="test",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        long_exit=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator="<", right=100)]) # Never
    )
    
    baseline_res = run_backtest(strat, df)
    explicit_zero_res = run_backtest(strat, df, execution_delay_bars=0)
    
    assert len(baseline_res.trades) == len(explicit_zero_res.trades)
    if baseline_res.trades:
        assert baseline_res.trades[0].entry_price == explicit_zero_res.trades[0].entry_price
        assert baseline_res.trades[0].entry_time == explicit_zero_res.trades[0].entry_time
    assert baseline_res.assumptions.get("execution_delay_bars", 0) == 0

def test_execution_delay_one_bar_shift():
    """One-bar shift: execution is delayed exactly 1 bar."""
    df = _make_test_df(10)
    strat = Strategy(
        name="test",
        # Enter condition always triggers
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
    )
    
    baseline_res = run_backtest(strat, df)
    delayed_res = run_backtest(strat, df, execution_delay_bars=1)
    
    assert len(baseline_res.trades) == 1
    assert len(delayed_res.trades) == 1
    
    # Baseline: signal on index 0, entry on index 1
    # Delayed: signal on index 0, pending on index 1, entry on index 2
    assert delayed_res.trades[0].entry_time == df["datetime"].iloc[2]
    assert delayed_res.trades[0].entry_price == df["open"].iloc[2]
    assert baseline_res.trades[0].entry_time == df["datetime"].iloc[1]
    
def test_execution_delay_in_flight_blocking():
    """In-flight blocking: new signals are suppressed when pending is not None."""
    # If delay is 3, a signal on bar 0 shouldn't let bar 1, 2 generate new signals.
    df = _make_test_df(10)
    strat = Strategy(
        name="test",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
    )
    
    # Delay 3: signal on 0, wait 1, 2, 3, execute on 4.
    res = run_backtest(strat, df, execution_delay_bars=3)
    
    assert len(res.trades) == 1
    assert res.trades[0].entry_time == df["datetime"].iloc[4]

def test_execution_delay_end_of_data():
    """End-of-data handling: warning is generated if delay pushes past the end of data."""
    df = _make_test_df(3)
    strat = Strategy(
        name="test",
        # Triggers on all bars
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
    )
    
    # Signal on 0. Delay=5. Data ends at 2.
    res = run_backtest(strat, df, execution_delay_bars=5)
    
    # No trades executed because we ran out of data
    assert len(res.trades) == 0
    
    # Warning generated
    warnings = [w for w in res.warnings if "pending at end of data" in w]
    assert len(warnings) == 1


# ---------------------------------------------------------------------------
# Guardrail tests — invalid execution_delay_bars values
# ---------------------------------------------------------------------------

def test_execution_delay_bars_negative_raises():
    """Negative execution_delay_bars raises ValueError."""
    df = _make_test_df(10)
    strat = Strategy(
        name="test",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
    )
    with pytest.raises(ValueError, match="execution_delay_bars must be >= 0"):
        run_backtest(strat, df, execution_delay_bars=-1)


def test_execution_delay_bars_float_raises():
    """Float execution_delay_bars raises ValueError."""
    df = _make_test_df(10)
    strat = Strategy(
        name="test",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
    )
    with pytest.raises(ValueError, match="execution_delay_bars must be an int"):
        run_backtest(strat, df, execution_delay_bars=1.5)


def test_execution_delay_bars_bool_raises():
    """Bool execution_delay_bars raises ValueError (bool is a subclass of int)."""
    df = _make_test_df(10)
    strat = Strategy(
        name="test",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
    )
    with pytest.raises(ValueError, match="execution_delay_bars must be an int"):
        run_backtest(strat, df, execution_delay_bars=True)


def test_execution_delay_bars_str_raises():
    """String execution_delay_bars raises ValueError."""
    df = _make_test_df(10)
    strat = Strategy(
        name="test",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
    )
    with pytest.raises(ValueError, match="execution_delay_bars must be an int"):
        run_backtest(strat, df, execution_delay_bars="1")


def test_execution_delay_bars_none_raises():
    """None execution_delay_bars raises ValueError."""
    df = _make_test_df(10)
    strat = Strategy(
        name="test",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
    )
    with pytest.raises(ValueError, match="execution_delay_bars must be an int"):
        run_backtest(strat, df, execution_delay_bars=None)
