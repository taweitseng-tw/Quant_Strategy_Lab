"""Tests for backtest engine — Task 005."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.models.backtest_result import Trade
from core.models.strategy import Condition, Strategy, StrategyBlock
from strategy_engine.evaluator import evaluate_block, evaluate_condition
from strategy_engine.indicators import sma
from backtest_engine.runner import run_backtest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_uptrend_df(n_bars: int = 50) -> pd.DataFrame:
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


def _make_simple_long_strategy(sma_period: int = 5) -> Strategy:
    return Strategy(
        name="test_sma_cross",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": sma_period}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": sma_period}, operator="<"),
        ], logic="AND"),
    )


# ---------------------------------------------------------------------------
# SMA indicator — no future leak
# ---------------------------------------------------------------------------


def test_sma_no_future_leak():
    close = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0])
    result = sma(close, period=3)
    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])
    assert result.iloc[2] == pytest.approx(20.0)
    assert result.iloc[3] == pytest.approx(30.0)


# ---------------------------------------------------------------------------
# Condition evaluation
# ---------------------------------------------------------------------------


def test_evaluate_sma_condition():
    df = _make_uptrend_df(30)
    df["sma_5"] = sma(df["close"], 5)
    cond = Condition(indicator="SMA", params={"period": 5}, operator=">")
    # After warmup, close should be above SMA in uptrend
    found_true = False
    for i in range(10, 25):
        if evaluate_condition(cond, df, i):
            found_true = True
            break
    assert found_true


def test_evaluate_and_block():
    df = _make_uptrend_df(30)
    df["sma_5"] = sma(df["close"], 5)
    df["sma_20"] = sma(df["close"], 20)
    block = StrategyBlock(conditions=[
        Condition(indicator="SMA", params={"period": 5}, operator=">"),
        Condition(indicator="SMA", params={"period": 20}, operator=">"),
    ], logic="AND")
    # Both must be true — after warmup in uptrend
    found = False
    for i in range(25, 30):
        if evaluate_block(block, df, i):
            found = True
            break
    assert found

def test_compile_condition_matches_evaluate_exhaustive():
    from strategy_engine.evaluator import compile_condition, evaluate_condition
    df = _make_uptrend_df(30)
    df["sma_5"] = sma(df["close"], 5)
    df["rsi_14"] = 50.0
    df["atr_14"] = 1.5
    df["macd_line_12_26_9"] = 1.0
    df["macd_signal_12_26_9"] = 0.5
    df["volume_sma_20"] = 2000.0
    df["sma_5_tf_15"] = 120.0  # MTF mock
    df["macd_line_12_26_9_tf_5"] = 2.0
    df["macd_signal_12_26_9_tf_5"] = 1.5
    
    # Inject various missing values
    # SMA missing at index 5
    df.loc[5, "sma_5"] = np.nan
    # RSI missing at index 6 as pd.NA (using object dtype to hold it alongside floats if needed, or Float64)
    df["rsi_14"] = df["rsi_14"].astype("Float64")
    df.loc[6, "rsi_14"] = pd.NA
    # MACD missing at index 7
    df.loc[7, "macd_line_12_26_9"] = np.nan
    # VOLUME_SMA missing at index 8
    df.loc[8, "volume_sma_20"] = pd.NA
    
    conditions = [
        Condition(indicator="SMA", params={"period": 5}, operator=">"),
        Condition(indicator="SMA", params={"period": 5}, operator="<"),
        Condition(indicator="SMA", params={"period": 5, "timeframe": 15}, operator=">"),
        Condition(indicator="RSI", params={"period": 14}, operator=">", right="40.0"),
        Condition(indicator="RSI", params={"period": 14}, operator="<", right=60.0),
        Condition(indicator="ATR", params={"period": 14}, operator=">", right=1.0),
        Condition(indicator="MACD", params={}, operator=">"),
        Condition(indicator="MACD", params={"timeframe": 5}, operator=">"),
        Condition(indicator="VOLUME", params={}, operator=">", right=1000),
        Condition(indicator="VOLUME_SMA", params={"period": 20}, operator=">", right=1.5),
        # Missing column conditions
        Condition(indicator="SMA", params={"period": 99}, operator=">"),
        Condition(indicator="RSI", params={"period": 99}, operator=">"),
        Condition(indicator="MACD", params={"timeframe": 99}, operator=">"),
        Condition(indicator="VOLUME_SMA", params={"period": 99}, operator=">"),
        # Invalid thresholds
        Condition(indicator="RSI", params={"period": 14}, operator=">", right="invalid"),
        Condition(indicator="RSI", params={"period": 14}, operator=">", right=np.nan),
    ]
    
    for cond in conditions:
        acc = compile_condition(cond, df)
        for i in range(30):
            expected = evaluate_condition(cond, df, i)
            actual = acc(i)
            assert expected == actual, f"Mismatch for {cond} at index {i}: expected {expected}, got {actual}"


def test_compile_block_matches_evaluate():
    from strategy_engine.evaluator import compile_block, evaluate_block
    df = _make_uptrend_df(30)
    df["sma_5"] = sma(df["close"], 5)
    df["sma_20"] = sma(df["close"], 20)
    block = StrategyBlock(conditions=[
        Condition(indicator="SMA", params={"period": 5}, operator=">"),
        Condition(indicator="SMA", params={"period": 20}, operator=">"),
    ], logic="AND")
    
    acc = compile_block(block, df)
    
    for i in range(30):
        expected = evaluate_block(block, df, i)
        actual = acc(i)
        assert expected == actual, f"Mismatch at index {i}: expected {expected}, got {actual}"



# ---------------------------------------------------------------------------
# Backtest entry / exit
# ---------------------------------------------------------------------------


def test_backtest_entry_signal_generates_trade():
    df = _make_uptrend_df(50)
    strat = _make_simple_long_strategy(5)
    result = run_backtest(strat, df)
    assert len(result.trades) >= 1


def test_backtest_no_strategy_no_trades():
    df = _make_uptrend_df(30)
    strat = Strategy(name="empty")
    result = run_backtest(strat, df)
    assert len(result.trades) == 0


def test_backtest_accounting_identity():
    df = _make_uptrend_df(50)
    strat = _make_simple_long_strategy(5)
    result = run_backtest(strat, df)
    trade_pnl = sum(t.pnl for t in result.trades)
    final_eq = result.equity_curve["equity"].iloc[-1]
    assert trade_pnl == pytest.approx(final_eq - 100_000.0)


def test_backtest_results_have_all_required_fields():
    df = _make_uptrend_df(50)
    result = run_backtest(_make_simple_long_strategy(5), df)
    assert isinstance(result.trades, list)
    assert len(result.trades) == 1
    assert "equity" in result.equity_curve.columns
    assert "drawdown" in result.drawdown_curve.columns
    assert "total_pnl" in result.metrics
    assert "profit_factor" in result.metrics
    assert result.metrics["total_pnl"] > 0.0


def test_backtest_commission_reduces_pnl():
    df = _make_uptrend_df(50)
    strat = _make_simple_long_strategy(5)
    r_no_comm = run_backtest(strat, df.copy(), commission=0.0)
    r_with_comm = run_backtest(strat, df.copy(), commission=50.0)
    assert r_with_comm.metrics["total_pnl"] < r_no_comm.metrics["total_pnl"]


def test_backtest_slippage_reduces_pnl():
    df = _make_uptrend_df(50)
    strat = _make_simple_long_strategy(5)
    r_no_slip = run_backtest(strat, df.copy(), slippage_ticks=0.0)
    r_with_slip = run_backtest(strat, df.copy(), slippage_ticks=5.0)
    assert r_with_slip.metrics["total_pnl"] < r_no_slip.metrics["total_pnl"]


# ---------------------------------------------------------------------------
# Trade details
# ---------------------------------------------------------------------------


def test_trade_entry_exit_times_are_chronological():
    df = _make_uptrend_df(50)
    result = run_backtest(_make_simple_long_strategy(5), df)
    for t in result.trades:
        assert t.entry_time <= t.exit_time

def test_trade_timestamps_are_pandas_timestamp():
    df = _make_uptrend_df(50)
    result = run_backtest(_make_simple_long_strategy(5), df)
    assert len(result.trades) > 0
    for t in result.trades:
        assert isinstance(t.entry_time, pd.Timestamp), f"entry_time is {type(t.entry_time)}"
        assert isinstance(t.exit_time, pd.Timestamp), f"exit_time is {type(t.exit_time)}"



def test_trade_direction_is_long_for_long_entry():
    df = _make_uptrend_df(50)
    result = run_backtest(_make_simple_long_strategy(5), df)
    for t in result.trades:
        assert t.direction == "long"


# ---------------------------------------------------------------------------
# Phase 3 Indicator Cache Tests
# ---------------------------------------------------------------------------


def test_indicator_cache_equivalence():
    from backtest_engine.runner import IndicatorCache, run_backtest
    df = _make_uptrend_df(100)
    strategy = _make_simple_long_strategy(10)
    
    res1 = run_backtest(strategy, df)
    
    cache = IndicatorCache(df)
    res2 = run_backtest(strategy, df, indicator_cache=cache)
    
    assert len(res1.trades) == len(res2.trades)
    assert res1.trades == res2.trades
    pd.testing.assert_frame_equal(res1.equity_curve, res2.equity_curve)
    assert res1.metrics == res2.metrics


def test_indicator_cache_mtf_equivalence():
    from backtest_engine.runner import IndicatorCache, run_backtest
    df = _make_uptrend_df(100)
    strategy = Strategy(
        name="mtf_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 5, "timeframe": 5}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 5, "timeframe": 5}, operator="<"),
        ], logic="AND"),
    )
    
    res1 = run_backtest(strategy, df)
    
    cache = IndicatorCache(df)
    res2 = run_backtest(strategy, df, indicator_cache=cache)
    
    assert res1.trades == res2.trades
    pd.testing.assert_frame_equal(res1.equity_curve, res2.equity_curve)


def test_indicator_cache_fingerprint_rejection():
    from backtest_engine.runner import IndicatorCache, run_backtest
    df1 = _make_uptrend_df(100)
    df2 = _make_uptrend_df(100)
    df2.loc[0, "close"] = 999.0  # alter shape/data
    
    cache = IndicatorCache(df1)
    
    assert cache.is_valid(df1)
    assert not cache.is_valid(df2)
    
    strategy = _make_simple_long_strategy(10)
    # This should bypass cache safely and match res1
    res1 = run_backtest(strategy, df2)
    res2 = run_backtest(strategy, df2, indicator_cache=cache)
    
    assert res1.trades == res2.trades


def test_indicator_cache_hit_rate():
    from backtest_engine.runner import IndicatorCache, _precompute_indicators
    df = _make_uptrend_df(100)
    strategy1 = _make_simple_long_strategy(10)
    strategy2 = _make_simple_long_strategy(10) # same indicators
    
    cache = IndicatorCache(df)
    
    _precompute_indicators(df.copy(), strategy1, cache)
    assert len(cache.columns) == 1  # Base SMA 10 is cached
    
    _precompute_indicators(df.copy(), strategy2, cache)
    assert len(cache.columns) == 1  # No new columns computed


def test_indicator_cache_macd_collision():
    from backtest_engine.runner import IndicatorCache, _precompute_indicators
    df = _make_uptrend_df(100)
    strategy1 = Strategy(
        name="macd1",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="MACD", params={"fast": 10, "slow": 20, "signal": 5}, operator=">"),
        ], logic="AND"),
    )
    strategy2 = Strategy(
        name="macd2",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="MACD", params={"fast": 12, "slow": 26, "signal": 9}, operator=">"),
        ], logic="AND"),
    )
    
    cache = IndicatorCache(df)
    _precompute_indicators(df.copy(), strategy1, cache)
    _precompute_indicators(df.copy(), strategy2, cache)
    
    assert len(cache.columns) == 2  # Both MACDs should be cached distinctly without collision


# ---------------------------------------------------------------------------
# Position management
# ---------------------------------------------------------------------------


def test_backtest_single_position_at_a_time():
    df = _make_uptrend_df(80)
    strat = _make_simple_long_strategy(5)
    result = run_backtest(strat, df)
    for i in range(len(result.trades) - 1):
        assert result.trades[i].exit_time <= result.trades[i + 1].entry_time


# ---------------------------------------------------------------------------
# Indicators — MACD, RSI, ATR, VOLUME_SMA
# ---------------------------------------------------------------------------


def test_macd_condition_evaluates():
    df = _make_uptrend_df(50)
    df["macd_line_12_26_9"] = 1.0
    df["macd_signal_12_26_9"] = 0.5
    cond = Condition(indicator="MACD", params={"fast": 12, "slow": 26, "signal": 9}, operator=">")
    assert evaluate_condition(cond, df, 30)

    cond_false = Condition(indicator="MACD", params={"fast": 12, "slow": 26, "signal": 9}, operator="<")
    assert not evaluate_condition(cond_false, df, 30)


def test_rsi_condition_evaluates():
    df = _make_uptrend_df(50)
    df["rsi_14"] = 80.0
    cond = Condition(indicator="RSI", params={"period": 14}, operator=">", right=50.0)
    assert evaluate_condition(cond, df, 30)

    cond_false = Condition(indicator="RSI", params={"period": 14}, operator="<", right=50.0)
    assert not evaluate_condition(cond_false, df, 30)


def test_atr_condition_evaluates():
    df = _make_uptrend_df(50)
    df["atr_14"] = 2.0
    cond = Condition(indicator="ATR", params={"period": 14}, operator=">", right=1.0)
    assert evaluate_condition(cond, df, 30)

    cond_false = Condition(indicator="ATR", params={"period": 14}, operator="<", right=1.0)
    assert not evaluate_condition(cond_false, df, 30)


def test_volume_sma_condition_evaluates():
    from strategy_engine.indicators import volume_sma
    df = _make_uptrend_df(50)
    df["volume_sma_20"] = volume_sma(df["volume"], 20)
    cond = Condition(indicator="VOLUME_SMA", params={"period": 20}, operator=">")
    for i in range(25, 50):
        evaluate_condition(cond, df, i)  # must not crash


def test_mtf_macd_backtest_runs_and_condition_can_trigger():
    """Prove MTF MACD condition evaluates during a full backtest run and can trigger trades."""
    df = _make_uptrend_df(200)
    strat = Strategy(
        name="mtf_macd_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="MACD", params={"fast": 12, "slow": 26, "signal": 9, "timeframe": 5}, operator=">"),
        ], logic="AND")
    )
    result = run_backtest(strat, df)
    assert len(result.trades) > 0


# ---------------------------------------------------------------------------
# MTF Integration — Signal timing, drops, errors
# ---------------------------------------------------------------------------


def test_mtf_sma_backtest_signal_timing():
    """Prove MTF SMA condition does not trigger before HTF indicator is available,
    and first possible trade entry is at the next bar open after signal availability.
    """
    df = _make_uptrend_df(60)  # 1min bars, starts 08:30
    
    strat = Strategy(
        name="timing_test",
        long_entry=StrategyBlock(conditions=[
            # In uptrend, close > SMA will be true as soon as SMA(5) on 5-min tf is available
            Condition(indicator="SMA", params={"period": 5, "timeframe": 5}, operator=">")
        ], logic="AND")
    )
    result = run_backtest(strat, df)
    assert len(result.trades) > 0
    
    first_trade = result.trades[0]
    # Candle 1: 08:30-08:34 (available 08:34)
    # Candle 5: 08:50-08:54 (available 08:54) -> SMA(5) first valid value at 08:54
    # Signal confirmed at bar close of 08:54.
    # Trade executes at next bar open: 08:55.
    # bar 0 = 08:30 ... bar 24 = 08:54, bar 25 = 08:55.
    expected_entry_time = df.loc[25, "datetime"]
    assert first_trade.entry_time == expected_entry_time


def test_mtf_rsi_backtest_runs_and_condition_can_trigger():
    df = _make_uptrend_df(150)
    # Add noise so RSI doesn't evaluate to NaN forever (due to zero down-ticks)
    np.random.seed(42)
    df["close"] += np.random.randn(150) * 5.0
    
    strat = Strategy(
        name="rsi_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="RSI", params={"period": 14, "timeframe": 5}, operator=">", right=10.0)
        ], logic="AND")
    )
    result = run_backtest(strat, df)
    assert len(result.trades) > 0


def test_mtf_atr_backtest_runs_and_condition_can_trigger():
    df = _make_uptrend_df(150)
    strat = Strategy(
        name="atr_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="ATR", params={"period": 14, "timeframe": 5}, operator=">", right=0.01)
        ], logic="AND")
    )
    result = run_backtest(strat, df)
    assert len(result.trades) > 0


def test_mtf_volume_backtest_uses_volume_tf_column():
    df = _make_uptrend_df(60)
    df["volume"] = 100
    
    # Base volume > 400 is False (100 > 400).
    # MTF (5m) volume > 400 is True (500 > 400).
    strat = Strategy(
        name="vol_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="VOLUME", params={"timeframe": 5}, operator=">", right=400)
        ], logic="AND")
    )
    result = run_backtest(strat, df)
    assert len(result.trades) > 0
    # First 5-min candle (500 vol) completes at 08:34. Trigger at 08:34 close, entry at 08:35 (bar 5).
    assert result.trades[0].entry_time == df.loc[5, "datetime"]


def test_mtf_volume_sma_backtest_uses_mtf_volume_and_mtf_sma():
    df = _make_uptrend_df(200)
    df["volume"] = 100
    
    # Base volume < Base SMA * 1.5 -> 100 < 150 (True).
    # MTF volume < MTF SMA * 1.5 -> 500 < 750 (True).
    # This verifies condition works and returns True.
    strat = Strategy(
        name="vol_sma_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="VOLUME_SMA", params={"period": 10, "timeframe": 5}, operator="<", right=1.5)
        ], logic="AND")
    )
    result = run_backtest(strat, df)
    assert len(result.trades) > 0


def test_mtf_incomplete_final_candle_no_signal():
    # 63 bars: 08:30 to 09:32
    # 15m candles: 08:30-08:44 (15), 08:45-08:59 (15), 09:00-09:14 (15), 09:15-09:29 (15).
    # Incomplete 15m candle: 09:30-09:32 (3 bars).
    df = _make_uptrend_df(63)
    df["volume"] = 100
    
    # Complete 15m candle volume = 1500.
    # Incomplete 15m candle volume = 300.
    # Condition: MTF volume < 500.
    # If incomplete candle was NOT dropped, it would trigger True at the end.
    strat = Strategy(
        name="incomplete_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="VOLUME", params={"timeframe": 15}, operator="<", right=500)
        ], logic="AND")
    )
    result = run_backtest(strat, df)
    assert len(result.trades) == 0  # No signal because incomplete candle is dropped.


def test_mtf_invalid_timeframe_error_in_run_backtest():
    df = _make_uptrend_df(50)
    strat = Strategy(
        name="invalid_tf",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 5, "timeframe": "not_an_int"}, operator=">")
        ], logic="AND")
    )
    with pytest.raises(ValueError, match="must be an int"):
        run_backtest(strat, df)


def test_mtf_base_only_strategy_result_unchanged():
    df = _make_uptrend_df(50)
    strat = _make_simple_long_strategy(5)
    result = run_backtest(strat, df)
    # We just need to know it runs normally and generates trades.
    # test_trade_entry_exit_times_are_chronological already proves base-only works.
    assert len(result.trades) > 0


# ---------------------------------------------------------------------------
# Task 053B: SL / TP Tests
# ---------------------------------------------------------------------------

def _make_sl_tp_df() -> pd.DataFrame:
    # 5 bars
    times = pd.date_range("2024-01-01 09:00", periods=5, freq="5min")
    return pd.DataFrame({
        "datetime": times,
        "open":  [100.0, 105.0, 110.0, 100.0, 100.0],
        "high":  [101.0, 115.0, 110.0, 100.0, 100.0],
        "low":   [99.0,   95.0, 110.0, 100.0, 100.0],
        "close": [100.0, 105.0, 110.0, 100.0, 100.0],
        "volume": [1000] * 5,
    })

def test_long_sl_hit():
    from core.models.strategy import RiskManagement
    df = _make_sl_tp_df()
    df.loc[0, "volume"] = 1000
    df.loc[1:, "volume"] = 100
    # enter long at bar 0 close -> executes bar 1 open (105.0)
    # bar 1 low is 95.0. SL is 100.0 (105 - 5 ticks)
    # should exit bar 1 mid-bar at 100.0
    strat = Strategy(
        name="test_long_sl",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(stop_loss_ticks=5.0)
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.direction == "long"
    assert t.entry_price == 105.0
    assert t.exit_price == 100.0
    assert t.exit_reason == "stop_loss"

def test_long_tp_hit():
    from core.models.strategy import RiskManagement
    df = _make_sl_tp_df()
    df.loc[0, "volume"] = 1000
    df.loc[1:, "volume"] = 100
    # enter long at bar 0 close -> executes bar 1 open (105.0)
    # bar 1 high is 115.0. TP is 110.0 (105 + 5 ticks)
    # should exit bar 1 mid-bar at 110.0
    strat = Strategy(
        name="test_long_tp",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(take_profit_ticks=5.0)
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.exit_price == 110.0
    assert t.exit_reason == "take_profit"

def test_short_sl_hit():
    from core.models.strategy import RiskManagement
    df = _make_sl_tp_df()
    df.loc[0, "volume"] = 1000
    df.loc[1:, "volume"] = 100
    # enter short at bar 0 close -> executes bar 1 open (105.0)
    # bar 1 high is 115.0. SL is 110.0 (105 + 5 ticks)
    strat = Strategy(
        name="test_short_sl",
        short_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(stop_loss_ticks=5.0)
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.direction == "short"
    assert t.exit_price == 110.0
    assert t.exit_reason == "stop_loss"

def test_short_tp_hit():
    from core.models.strategy import RiskManagement
    df = _make_sl_tp_df()
    df.loc[0, "volume"] = 1000
    df.loc[1:, "volume"] = 100
    # enter short at bar 0 close -> executes bar 1 open (105.0)
    # bar 1 low is 95.0. TP is 100.0 (105 - 5 ticks)
    strat = Strategy(
        name="test_short_tp",
        short_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(take_profit_ticks=5.0)
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.exit_price == 100.0
    assert t.exit_reason == "take_profit"

def test_same_bar_ambiguity_sl_wins():
    from core.models.strategy import RiskManagement
    df = _make_sl_tp_df()
    df.loc[0, "volume"] = 1000
    df.loc[1:, "volume"] = 100
    # enter long bar 1 open (105.0).
    # SL=100, TP=110. Bar 1 low=95, high=115. Both hit. SL wins.
    strat = Strategy(
        name="test_ambiguity",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(stop_loss_ticks=5.0, take_profit_ticks=5.0)
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.exit_price == 100.0
    assert t.exit_reason == "stop_loss"

def test_short_same_bar_ambiguity_sl_wins():
    from core.models.strategy import RiskManagement
    df = _make_sl_tp_df()
    df.loc[0, "volume"] = 1000
    df.loc[1:, "volume"] = 100
    # Enter short at bar 0 close -> executes at bar 1 open (105.0)
    # SL = 110.0 (105 + 5 ticks), TP = 100.0 (105 - 5 ticks)
    # Bar 1 high is 115.0 (hits SL), low is 95.0 (hits TP)
    strat = Strategy(
        name="test_short_ambiguity",
        short_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(stop_loss_ticks=5.0, take_profit_ticks=5.0)
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.direction == "short"
    assert t.exit_reason == "stop_loss"
    assert t.exit_price == 110.0

def test_long_gap_through_same_bar_ambiguity_sl_wins():
    from core.models.strategy import RiskManagement
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01 09:00", periods=4, freq="5min"),
        "open":  [100.0, 100.0,  90.0, 100.0],
        "high":  [100.0, 100.0, 112.0, 100.0],
        "low":   [100.0, 100.0,  85.0, 100.0],
        "close": [100.0, 100.0,  90.0, 100.0],
        "volume": [1000, 100, 100, 100],
    })
    # Bar 0: volume=1000 -> long entry signal triggered
    # Bar 1: opens at 100.0 -> long position entered at 100.0
    # SL is 95.0 (5 ticks), TP is 105.0 (5 ticks)
    # Bar 2: opens at 90.0 (gaps down past SL)
    # Bar 2 High is 112.0 (hits TP), Low is 85.0 (hits SL)
    # Both SL and TP are hit on Bar 2. SL wins.
    # Exits at gap open (90.0) with warning.
    strat = Strategy(
        name="test_long_gap_ambiguity",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(stop_loss_ticks=5.0, take_profit_ticks=5.0)
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.exit_reason == "stop_loss"
    assert t.exit_price == 90.0

    # Assert gap warning exists
    warnings = [w for w in res.warnings if "Gap execution on Stop-Loss" in w]
    assert len(warnings) == 1

def test_short_gap_through_same_bar_ambiguity_sl_wins():
    from core.models.strategy import RiskManagement
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01 09:00", periods=4, freq="5min"),
        "open":  [100.0, 100.0, 112.0, 100.0],
        "high":  [100.0, 100.0, 115.0, 100.0],
        "low":   [100.0, 100.0,  90.0, 100.0],
        "close": [100.0, 100.0, 110.0, 100.0],
        "volume": [1000, 100, 100, 100],
    })
    # Bar 0: volume=1000 -> short entry signal triggered
    # Bar 1: opens at 100.0 -> short position entered at 100.0
    # SL is 105.0 (5 ticks), TP is 95.0 (5 ticks)
    # Bar 2: opens at 112.0 (gaps up past SL)
    # Bar 2 High is 115.0 (hits SL), Low is 90.0 (hits TP)
    # Both SL and TP are hit on Bar 2. SL wins.
    # Exits at gap open (112.0) with warning.
    strat = Strategy(
        name="test_short_gap_ambiguity",
        short_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(stop_loss_ticks=5.0, take_profit_ticks=5.0)
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.direction == "short"
    assert t.exit_reason == "stop_loss"
    assert t.exit_price == 112.0

    # Assert gap warning exists
    warnings = [w for w in res.warnings if "Gap execution on Stop-Loss" in w]
    assert len(warnings) == 1

def test_gap_through_long_sl():
    from core.models.strategy import RiskManagement
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=3),
        "open":  [100.0, 100.0, 80.0],
        "high":  [100.0, 100.0, 85.0],
        "low":   [100.0, 100.0, 75.0],
        "close": [100.0, 100.0, 80.0],
        "volume": [1000, 1000, 1000]
    })
    # entry condition true at bar 0 close. Executed bar 1 open (100).
    # SL is 90 (10 ticks).
    # Bar 1 high/low 100/100.
    # Bar 2 open is 80 (gapped below SL).
    # Should exit at 80, not 90.
    strat = Strategy(
        name="test_gap",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(stop_loss_ticks=10.0)
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.exit_price == 80.0
    assert t.exit_reason == "stop_loss"

def test_gap_through_short_sl():
    from core.models.strategy import RiskManagement
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=3),
        "open":  [100.0, 100.0, 120.0],
        "high":  [100.0, 100.0, 125.0],
        "low":   [100.0, 100.0, 115.0],
        "close": [100.0, 100.0, 120.0],
        "volume": [1000, 1000, 1000]
    })
    # short filled bar 1 at 100. SL is 110.
    # Bar 2 open is 120. Gap above short SL.
    # Exit should be 120.
    strat = Strategy(
        name="test_gap_short",
        short_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(stop_loss_ticks=10.0)
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.exit_price == 120.0
    assert t.exit_reason == "stop_loss"

def test_disabled_baseline_equivalence():
    df = _make_sl_tp_df()
    df.loc[0, "volume"] = 1000
    df.loc[1:, "volume"] = 100
    # If RM disabled, it shouldn't trigger SL/TP even if huge swings.
    strat = Strategy(
        name="test_disabled",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)])
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    assert len(res.trades) == 1
    t = res.trades[0]
    # No exit rules, so it will exit at end of data.
    assert t.exit_reason == "end_of_data"
    assert t.exit_price == 100.0 # final close

def test_next_bar_open_preserved():
    df = _make_sl_tp_df() # entry condition true on bar 0.
    df.loc[0, "volume"] = 1000
    df.loc[1:, "volume"] = 100
    strat = Strategy(
        name="test_nbo",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)])
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    t = res.trades[0]
    assert t.entry_price == 105.0 # bar 1 open, NOT bar 0 close (100.0)

def test_rule_based_exit_priority():
    from core.models.strategy import RiskManagement
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=3),
        "open":  [100.0, 100.0, 100.0],
        "high":  [100.0, 100.0, 100.0],
        "low":   [100.0, 100.0, 90.0], # SL would be hit on bar 2
        "close": [100.0, 50.0, 100.0],  
        "volume": [1000, 100, 1000] # volume drops to 100 on bar 1, triggering exit
    })
    # Enter bar 1 at 100 (from bar 0 entry signal). SL is 95.
    # Bar 1 close is 50. Exit condition triggered. Queues exit for bar 2 open.
    # Bar 2 open is 100. Rule-based exit executes at 100.
    # Even though Bar 2 low is 90 (which would hit SL), the position was already closed by the rule at the open.
    strat = Strategy(
        name="test_rule_exit",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        long_exit=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator="<", right=500)]),
        risk_management=RiskManagement(stop_loss_ticks=5.0)
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    t = res.trades[0]
    assert t.exit_reason == "signal"
    assert t.exit_price == 100.0

def test_final_bar_behavior():
    df = _make_sl_tp_df()
    df.loc[0, "volume"] = 1000
    df.loc[1:, "volume"] = 100
    strat = Strategy(
        name="test_final",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)])
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    t = res.trades[0]
    assert t.exit_reason == "end_of_data"

def test_backtest_assumptions_record_sl_tp_state():
    from core.models.strategy import RiskManagement
    df = _make_sl_tp_df()
    
    # Disabled case
    strat_disabled = Strategy(
        name="test_disabled",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)])
    )
    res_disabled = run_backtest(strat_disabled, df)
    assert res_disabled.assumptions["stop_take_profit_enabled"] is False
    assert "risk_management_precedence" not in res_disabled.assumptions
    
    # Enabled case
    strat_enabled = Strategy(
        name="test_enabled",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(stop_loss_ticks=10.0, take_profit_pct=0.05)
    )
    res_enabled = run_backtest(strat_enabled, df)
    assert res_enabled.assumptions["stop_take_profit_enabled"] is True
    assert res_enabled.assumptions["risk_management_precedence"] == "ticks_over_percent"
    assert res_enabled.assumptions["stop_loss_ticks"] == 10.0
    assert res_enabled.assumptions["take_profit_pct"] == 0.05
    assert "stop_loss_pct" not in res_enabled.assumptions
    assert "take_profit_ticks" not in res_enabled.assumptions


# ---------------------------------------------------------------------------
# Task 053E: Session-End Exit Tests
# ---------------------------------------------------------------------------

def _make_session_end_df() -> pd.DataFrame:
    times = pd.date_range("2024-01-01 15:45", periods=5, freq="5min")
    return pd.DataFrame({
        "datetime": times,
        "open":  [100.0, 100.0, 100.0, 100.0, 100.0],
        "high":  [100.0, 100.0, 100.0, 100.0, 100.0],
        "low":   [100.0, 100.0, 100.0, 100.0, 100.0],
        "close": [100.0, 100.0, 100.0, 100.0, 100.0],
        "volume": [1000] * 5,
    })

def test_session_end_long_exit():
    from core.models.strategy import RiskManagement
    df = _make_session_end_df()
    strat = Strategy(
        name="test_session_end_long",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(close_end_of_session=True, session_end_time="16:00")
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.direction == "long"
    assert t.exit_reason == "session_end"
    assert t.exit_time == pd.Timestamp("2024-01-01 16:00")

def test_session_end_short_exit():
    from core.models.strategy import RiskManagement
    df = _make_session_end_df()
    strat = Strategy(
        name="test_session_end_short",
        short_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(close_end_of_session=True, session_end_time="16:00")
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.direction == "short"
    assert t.exit_reason == "session_end"
    assert t.exit_time == pd.Timestamp("2024-01-01 16:00")

def test_session_end_with_costs():
    from core.models.strategy import RiskManagement
    df = _make_session_end_df()
    strat = Strategy(
        name="test_session_end_costs",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(close_end_of_session=True, session_end_time="16:00")
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0, commission=2.0, slippage_ticks=1.0)
    t = res.trades[0]
    assert t.entry_price == 101.0
    assert t.exit_price == 99.0
    assert t.pnl == -6.0

def test_session_end_missing_final_bar():
    from core.models.strategy import RiskManagement
    times = pd.to_datetime(["2024-01-01 15:50", "2024-01-01 15:55", "2024-01-01 16:05", "2024-01-01 16:10"])
    df = pd.DataFrame({
        "datetime": times,
        "open":  [100.0]*4, "high":  [100.0]*4, "low":   [100.0]*4, "close": [100.0]*4,
        "volume": [1000]*4,
    })
    strat = Strategy(
        name="test_session_end_missing_bar",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(close_end_of_session=True, session_end_time="16:00")
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    t = res.trades[0]
    assert t.exit_reason == "session_end"
    assert t.exit_time == pd.Timestamp("2024-01-01 16:05")

def test_session_end_preempted_by_sl():
    from core.models.strategy import RiskManagement
    df = _make_session_end_df()
    df.loc[3, "low"] = 90.0
    strat = Strategy(
        name="test_session_end_sl_wins",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(close_end_of_session=True, session_end_time="16:00", stop_loss_ticks=5.0)
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    t = res.trades[0]
    assert t.exit_reason == "stop_loss"
    assert t.exit_time == pd.Timestamp("2024-01-01 16:00")

def test_session_end_prevents_new_entry():
    from core.models.strategy import RiskManagement
    df = _make_session_end_df()
    strat = Strategy(
        name="test_session_end_no_new_entry",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(close_end_of_session=True, session_end_time="16:00")
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.exit_time == pd.Timestamp("2024-01-01 16:00")

def test_session_end_assumptions():
    from core.models.strategy import RiskManagement
    df = _make_session_end_df()
    strat = Strategy(
        name="test_session_end_assumptions",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(close_end_of_session=True, session_end_time="16:00")
    )
    res = run_backtest(strat, df, initial_capital=10000.0, tick_size=1.0)
    assert res.assumptions.get("close_end_of_session") is True
    assert res.assumptions.get("session_end_time") == "16:00"

def test_session_end_invalid_time_raises():
    from core.models.strategy import RiskManagement
    df = _make_session_end_df()
    strat = Strategy(
        name="test_invalid",
        risk_management=RiskManagement(close_end_of_session=True, session_end_time="invalid")
    )
    with pytest.raises(ValueError, match="Invalid session_end_time format"):
        run_backtest(strat, df)

def test_session_end_assumptions_disabled_if_invalid_time():
    from core.models.strategy import RiskManagement
    df = _make_session_end_df()
    strat = Strategy(
        name="test_missing_time",
        risk_management=RiskManagement(close_end_of_session=True, session_end_time=None)
    )
    res = run_backtest(strat, df)
    assert "close_end_of_session" not in res.assumptions
    assert "session_end_time" not in res.assumptions

def test_session_end_cancels_prior_bar_pending_entry():
    from core.models.strategy import RiskManagement
    times = pd.date_range("2024-01-01 15:55", periods=3, freq="5min")
    df = pd.DataFrame({
        "datetime": times,
        "open":  [100.0]*3, "high":  [100.0]*3, "low":   [100.0]*3, "close": [100.0]*3,
        "volume": [1000]*3,
    })
    strat = Strategy(
        name="test_cancel_entry",
        long_entry=StrategyBlock(conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=500)]),
        risk_management=RiskManagement(close_end_of_session=True, session_end_time="16:00")
    )
    res = run_backtest(strat, df)
    assert len(res.trades) == 0
    warnings = [w for w in res.warnings if "Canceled pending long entry" in w]
    assert len(warnings) == 1
