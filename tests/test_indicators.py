"""Tests for RSI, MACD, ATR indicators and evaluator — Task 021."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.models.strategy import Condition, StrategyBlock
from strategy_engine.indicators import atr, macd, rsi, sma
from strategy_engine.evaluator import evaluate_condition, evaluate_block


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_price_series(n: int = 50, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0, 1.0, n)
    return pd.Series(100.0 + np.cumsum(returns))


def _make_ohlcv_df(n: int = 50, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    times = pd.date_range("2024-01-02 08:30", periods=n, freq="1min")
    close = 100.0 + np.cumsum(rng.normal(0.0, 1.0, n))
    return pd.DataFrame({
        "datetime": times,
        "open":  close - 0.5,
        "high":  close + rng.uniform(0.5, 2.0, n),
        "low":   close - rng.uniform(0.5, 2.0, n),
        "close": close,
        "volume": rng.integers(500, 5000, n),
    })


# ---------------------------------------------------------------------------
# RSI
# ---------------------------------------------------------------------------


def test_rsi_warmup_is_nan():
    """First N bars of RSI(N) must be NaN."""
    series = _make_price_series(30)
    r = rsi(series, period=14)
    assert r.iloc[:14].isna().all()
    assert not r.iloc[14:].isna().all()


def test_rsi_range():
    """RSI values must be in [0, 100]."""
    series = _make_price_series(100)
    r = rsi(series, period=14)
    valid = r.dropna()
    assert (valid >= 0).all()
    assert (valid <= 100).all()


def test_rsi_constant_price_is_nan():
    """RSI on constant prices must produce NaN (no gains or losses)."""
    series = pd.Series([100.0] * 30)
    r = rsi(series, period=14)
    assert r.iloc[14:].isna().all()


# ---------------------------------------------------------------------------
# MACD
# ---------------------------------------------------------------------------


def test_macd_output_columns():
    """MACD must return macd_line, macd_signal, macd_histogram."""
    series = _make_price_series(100)
    result = macd(series)
    assert list(result.columns) == ["macd_line", "macd_signal", "macd_histogram"]
    assert len(result) == len(series)


def test_macd_no_future_leak():
    """MACD at bar i must only depend on bars ≤ i."""
    series = _make_price_series(100)
    full = macd(series)

    # Compute MACD up to bar 50 only.
    partial = macd(series.iloc[:51])
    # Values at index 50 must match.
    assert full["macd_line"].iloc[50] == pytest.approx(partial["macd_line"].iloc[50])
    assert full["macd_signal"].iloc[50] == pytest.approx(partial["macd_signal"].iloc[50])


# ---------------------------------------------------------------------------
# ATR
# ---------------------------------------------------------------------------


def test_atr_warmup_is_nan():
    """First period-1 bars of ATR(period) must be NaN."""
    df = _make_ohlcv_df(30)
    a = atr(df, period=14)
    assert a.iloc[:13].isna().all()   # bars 0-12 are NaN
    assert not pd.isna(a.iloc[13])    # bar 13 is first valid
    assert not a.iloc[14:].isna().all()


def test_atr_non_negative():
    """ATR must never be negative."""
    df = _make_ohlcv_df(100)
    a = atr(df, period=14)
    valid = a.dropna()
    assert (valid >= 0).all()


# ---------------------------------------------------------------------------
# Evaluator — RSI
# ---------------------------------------------------------------------------


def test_evaluate_rsi_above_threshold():
    """RSI(14) > 30 must be True when RSI exceeds 30."""
    df = _make_ohlcv_df(50)
    df["rsi_14"] = rsi(df["close"], 14)

    cond = Condition(indicator="RSI", params={"period": 14}, operator=">", right=30.0)
    # At bar 20, RSI should be computable and likely > 30 in random walk.
    assert evaluate_condition(cond, df, 20)


def test_evaluate_rsi_below_threshold_nan():
    """RSI NaN during warmup must return False."""
    df = _make_ohlcv_df(30)
    df["rsi_14"] = rsi(df["close"], 14)

    cond = Condition(indicator="RSI", params={"period": 14}, operator=">", right=30.0)
    assert not evaluate_condition(cond, df, 5)  # warmup


# ---------------------------------------------------------------------------
# Evaluator — MACD
# ---------------------------------------------------------------------------


def test_evaluate_macd_crossover():
    """MACD line > signal line condition must evaluate correctly."""
    df = _make_ohlcv_df(100)
    macd_df = macd(df["close"])
    df["macd_line_12_26_9"] = macd_df["macd_line"]
    df["macd_signal_12_26_9"] = macd_df["macd_signal"]

    cond = Condition(indicator="MACD", params={}, operator=">")
    # At bar 50, check manually.
    expected = bool(df.at[50, "macd_line_12_26_9"] > df.at[50, "macd_signal_12_26_9"])
    assert evaluate_condition(cond, df, 50) == expected


def test_evaluate_macd_mtf_crossover():
    """MACD MTF line > signal line condition uses suffixed columns."""
    df = _make_ohlcv_df(50)
    df["macd_line_12_26_9_tf_5"] = 1.0
    df["macd_signal_12_26_9_tf_5"] = 0.5
    
    cond_gt = Condition(indicator="MACD", params={"timeframe": 5}, operator=">")
    cond_lt = Condition(indicator="MACD", params={"timeframe": 5}, operator="<")
    
    assert bool(evaluate_condition(cond_gt, df, 10)) is True
    assert bool(evaluate_condition(cond_lt, df, 10)) is False


def test_evaluate_macd_mtf_missing_columns_false():
    """Missing MTF MACD columns return False without crashing."""
    df = _make_ohlcv_df(10)
    # df lacks macd_line_12_26_9_tf_5
    cond = Condition(indicator="MACD", params={"timeframe": 5}, operator=">")
    assert bool(evaluate_condition(cond, df, 5)) is False


def test_evaluate_macd_mtf_nan_values_false():
    """NaN MTF MACD values return False."""
    import numpy as np
    df = _make_ohlcv_df(10)
    df["macd_line_12_26_9_tf_5"] = np.nan
    df["macd_signal_12_26_9_tf_5"] = 0.5
    cond = Condition(indicator="MACD", params={"timeframe": 5}, operator=">")
    assert bool(evaluate_condition(cond, df, 5)) is False


# ---------------------------------------------------------------------------
# Evaluator — ATR
# ---------------------------------------------------------------------------


def test_evaluate_atr_above_threshold():
    """ATR(14) > 0.5 must evaluate correctly."""
    df = _make_ohlcv_df(50)
    df["atr_14"] = atr(df, 14)

    cond = Condition(indicator="ATR", params={"period": 14}, operator=">", right=0.5)
    atr_val = df.at[20, "atr_14"]
    expected = not pd.isna(atr_val) and atr_val > 0.5
    assert evaluate_condition(cond, df, 20) == expected


# ---------------------------------------------------------------------------
# Evaluator — SMA unchanged
# ---------------------------------------------------------------------------


def test_sma_evaluator_unchanged():
    """Existing SMA close > SMA(N) condition must still work."""
    df = _make_ohlcv_df(50)
    df["sma_10"] = sma(df["close"], 10)

    cond = Condition(indicator="SMA", params={"period": 10}, operator=">")
    close = df.at[20, "close"]
    sma_val = df.at[20, "sma_10"]
    expected = not pd.isna(sma_val) and close > sma_val
    assert evaluate_condition(cond, df, 20) == expected


# ---------------------------------------------------------------------------
# Block evaluation with new indicators
# ---------------------------------------------------------------------------


def test_block_with_rsi_and_sma():
    """AND block with close>SMA and RSI<70."""
    df = _make_ohlcv_df(100)
    df["sma_10"] = sma(df["close"], 10)
    df["rsi_14"] = rsi(df["close"], 14)

    block = StrategyBlock(
        conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator=">"),
            Condition(indicator="RSI", params={"period": 14}, operator="<", right=70.0),
        ],
        logic="AND",
    )
    result = evaluate_block(block, df, 30)
    assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# VOLUME SMA Indicator
# ---------------------------------------------------------------------------

from strategy_engine.indicators import volume_sma


def test_volume_sma_warmup_is_nan():
    series = pd.Series([100.0] * 30)
    v = volume_sma(series, period=10)
    assert v.iloc[:9].isna().all()
    assert not pd.isna(v.iloc[9])


def test_volume_sma_no_future_leak():
    series = pd.Series(np.random.rand(50) * 1000)
    full = volume_sma(series, period=10)
    partial = volume_sma(series.iloc[:25], period=10)
    assert full.iloc[24] == pytest.approx(partial.iloc[24])


# ---------------------------------------------------------------------------
# Evaluator — VOLUME
# ---------------------------------------------------------------------------


def test_evaluate_volume_threshold():
    df = _make_ohlcv_df(50)
    # Set known volume
    df.loc[20, "volume"] = 5000.0

    cond_gt = Condition(indicator="VOLUME", params={}, operator=">", right=4000.0)
    cond_lt = Condition(indicator="VOLUME", params={}, operator="<", right=6000.0)
    cond_false = Condition(indicator="VOLUME", params={}, operator=">", right=6000.0)

    assert evaluate_condition(cond_gt, df, 20)
    assert evaluate_condition(cond_lt, df, 20)
    assert not evaluate_condition(cond_false, df, 20)


def test_evaluate_volume_mtf():
    df = _make_ohlcv_df(50)
    df.loc[20, "volume"] = 1000.0  # base volume is low, would fail > 4000
    df.loc[20, "volume_tf_5"] = 5000.0 # mtf volume is high, passes > 4000

    cond_gt = Condition(indicator="VOLUME", params={"timeframe": 5}, operator=">", right=4000.0)
    assert bool(evaluate_condition(cond_gt, df, 20)) is True


def test_evaluate_volume_mtf_missing_columns_false():
    df = _make_ohlcv_df(10)
    # df lacks volume_tf_5
    cond = Condition(indicator="VOLUME", params={"timeframe": 5}, operator=">", right=100.0)
    assert bool(evaluate_condition(cond, df, 5)) is False


def test_col_volume_mtf():
    from strategy_engine.evaluator import _col
    assert _col("VOLUME", {"timeframe": 5}) == "volume_tf_5"


def test_evaluate_volume_sma():
    df = _make_ohlcv_df(50)
    df["volume_sma_10"] = volume_sma(df["volume"], 10)
    
    # Set known values at bar 20
    df.loc[20, "volume_sma_10"] = 2000.0
    df.loc[20, "volume"] = 3500.0

    # 3500 > 2000 * 1.5 (which is 3000) -> True
    cond_spike = Condition(indicator="VOLUME_SMA", params={"period": 10}, operator=">", right=1.5)
    assert evaluate_condition(cond_spike, df, 20)

    # 3500 > 2000 * 2.0 (which is 4000) -> False
    cond_too_high = Condition(indicator="VOLUME_SMA", params={"period": 10}, operator=">", right=2.0)
    assert not evaluate_condition(cond_too_high, df, 20)

    # Default multiplier (1.0)
    cond_default = Condition(indicator="VOLUME_SMA", params={"period": 10}, operator=">")
    assert evaluate_condition(cond_default, df, 20)


def test_evaluate_volume_sma_mtf():
    df = _make_ohlcv_df(50)
    
    # Base cols that would fail cond_spike:
    df.loc[20, "volume"] = 1000.0
    df.loc[20, "volume_sma_10"] = 1000.0 # ratio is 1.0 (fails > 1.5)
    
    # MTF cols that would pass cond_spike:
    df.loc[20, "volume_tf_5"] = 3500.0
    df.loc[20, "volume_sma_10_tf_5"] = 2000.0 # 3500 > 2000 * 1.5 -> True
    
    cond_spike = Condition(indicator="VOLUME_SMA", params={"period": 10, "timeframe": 5}, operator=">", right=1.5)
    assert bool(evaluate_condition(cond_spike, df, 20)) is True


def test_evaluate_volume_sma_mtf_missing_columns_false():
    df = _make_ohlcv_df(10)
    df.loc[5, "volume_tf_5"] = 3500.0
    # missing volume_sma_10_tf_5
    cond = Condition(indicator="VOLUME_SMA", params={"period": 10, "timeframe": 5}, operator=">", right=1.5)
    assert bool(evaluate_condition(cond, df, 5)) is False


def test_evaluate_volume_sma_mtf_missing_volume_tf_false():
    df = _make_ohlcv_df(10)
    df.loc[5, "volume_sma_10_tf_5"] = 2000.0
    # missing volume_tf_5
    cond = Condition(indicator="VOLUME_SMA", params={"period": 10, "timeframe": 5}, operator=">", right=1.5)
    assert bool(evaluate_condition(cond, df, 5)) is False


def test_volume_sma_invalid_period_safe_behavior():
    """If period is invalid (<0), pandas rolling raises ValueError."""
    series = pd.Series(np.random.rand(50))
    # Note: pandas allows window=0 (returns NaNs) but raises for window < 0
    with pytest.raises(ValueError):
        volume_sma(series, period=-1)


def test_volume_threshold_invalid_right_false():
    df = _make_ohlcv_df(50)
    cond = Condition(indicator="VOLUME", params={}, operator=">", right="not_a_number")
    assert not evaluate_condition(cond, df, 20)

    cond_nan = Condition(indicator="VOLUME", params={}, operator=">", right=float("nan"))
    assert not evaluate_condition(cond_nan, df, 20)

    cond_inf = Condition(indicator="VOLUME", params={}, operator=">", right=float("inf"))
    assert not evaluate_condition(cond_inf, df, 20)


def test_volume_sma_invalid_multiplier_false_or_default_documented():
    df = _make_ohlcv_df(50)
    df["volume_sma_10"] = volume_sma(df["volume"], 10)
    
    # string fallback defaults to multiplier=1.0
    cond_default = Condition(indicator="VOLUME_SMA", params={"period": 10}, operator=">")
    default_result = evaluate_condition(cond_default, df, 20)
    
    cond_str = Condition(indicator="VOLUME_SMA", params={"period": 10}, operator=">", right="not_a_number")
    assert evaluate_condition(cond_str, df, 20) == default_result

    # nan and inf are treated as invalid and evaluate to False
    cond_nan = Condition(indicator="VOLUME_SMA", params={"period": 10}, operator=">", right=float("nan"))
    assert not evaluate_condition(cond_nan, df, 20)

    cond_inf = Condition(indicator="VOLUME_SMA", params={"period": 10}, operator=">", right=float("inf"))
    assert not evaluate_condition(cond_inf, df, 20)


def test_volume_sma_missing_volume_column_safe_behavior():
    df = _make_ohlcv_df(50)
    # Intentionally remove "volume" to test KeyError safety
    df = df.drop(columns=["volume"])
    
    # Needs volume_sma column for _eval_volume_sma not to fail early on it
    df["volume_sma_10"] = 1000.0

    cond = Condition(indicator="VOLUME_SMA", params={"period": 10}, operator=">")
    assert not evaluate_condition(cond, df, 20)

    cond_thresh = Condition(indicator="VOLUME", params={}, operator=">", right=100)
    assert not evaluate_condition(cond_thresh, df, 20)


def test_volume_sma_warmup_false_in_evaluator():
    df = _make_ohlcv_df(50)
    df["volume_sma_10"] = volume_sma(df["volume"], 10)
    
    cond = Condition(indicator="VOLUME_SMA", params={"period": 10}, operator=">")
    # Bar 5 is in warmup (first 9 bars are NaN)
    assert pd.isna(df.at[5, "volume_sma_10"])
    assert not evaluate_condition(cond, df, 5)


def test_volume_sma_current_bar_only_no_future_leak():
    """Verify that evaluator only checks df.at[i, ...] and doesn't peek forward."""
    df = _make_ohlcv_df(50)
    df["volume_sma_10"] = volume_sma(df["volume"], 10)
    
    cond = Condition(indicator="VOLUME_SMA", params={"period": 10}, operator=">")
    
    # Change future bar 21 volume to something massive
    df.loc[21, "volume"] = 999999.0
    df.loc[21, "volume_sma_10"] = 999999.0
    
    # Make bar 20 NOT trigger
    df.loc[20, "volume"] = 1000.0
    df.loc[20, "volume_sma_10"] = 2000.0
    
    # If it leaked, it might see bar 21. But it shouldn't.
    assert not evaluate_condition(cond, df, 20)

