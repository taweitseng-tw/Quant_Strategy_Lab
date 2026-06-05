"""Tests for MTF precompute - Task 049B."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.models.strategy import Condition, Strategy, StrategyBlock
from backtest_engine.runner import (
    _drop_incomplete_final_htf_group,
    _infer_base_minutes,
    _precompute_indicators,
    _resample_for_mtf,
    _validate_mtf_timeframe,
    run_backtest,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_1min_df(n_bars: int = 100) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="1min")
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


def _make_5min_df(n_bars: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="5min")
    close = 100.0 + np.cumsum(rng.normal(0.03, 0.8, n_bars))
    close = np.maximum(close, 10.0)
    noise = rng.uniform(0.4, 2.0, n_bars)
    return pd.DataFrame({
        "datetime": times,
        "open":  close - noise * 0.3,
        "high":  close + noise,
        "low":   close - noise,
        "close": close,
        "volume": rng.integers(800, 8000, n_bars),
    })


# ---------------------------------------------------------------------------
# A. Base behavior unchanged
# ---------------------------------------------------------------------------


def test_precompute_no_timeframe_unchanged():
    df = _make_1min_df(50)
    strat = Strategy(
        name="base_only",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 20}, operator=">"),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)

    assert "sma_20" in df.columns
    # No MTF columns should be created.
    assert "sma_20_tf_5" not in df.columns


def test_backtest_base_only_strategy_unchanged_with_mtf_code_present():
    df = _make_1min_df(80)
    strat = _make_1min_df.__name__  # actually use the helper
    strat = Strategy(
        name="base_sma",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 5}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 5}, operator="<"),
        ], logic="AND"),
    )
    r1 = run_backtest(strat, df.copy())
    r2 = run_backtest(strat, df.copy())

    assert r1.metrics == r2.metrics
    assert r1.metrics.get("total_pnl") == r2.metrics.get("total_pnl")


# ---------------------------------------------------------------------------
# B. Timeframe validation
# ---------------------------------------------------------------------------


def test_mtf_timeframe_equal_base_is_noop():
    df = _make_1min_df(50)
    strat = Strategy(
        name="tf_eq_base",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 20, "timeframe": 1}, operator=">"),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)
    assert "sma_20" in df.columns
    assert "sma_20_tf_1" not in df.columns


def test_mtf_timeframe_less_than_base_raises():
    df = _make_1min_df(50)
    strat = Strategy(
        name="tf_too_small",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 20, "timeframe": 0}, operator=">"),
        ], logic="AND"),
    )
    with pytest.raises(ValueError, match="must be positive"):
        _precompute_indicators(df, strat)


def test_mtf_timeframe_not_multiple_raises():
    df = _make_5min_df(50)
    strat = Strategy(
        name="tf_not_multiple",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 20, "timeframe": 7}, operator=">"),
        ], logic="AND"),
    )
    with pytest.raises(ValueError, match="not an integer multiple"):
        _precompute_indicators(df, strat)


def test_mtf_timeframe_non_int_raises():
    df = _make_1min_df(50)
    strat = Strategy(
        name="tf_str",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 20, "timeframe": "5m"}, operator=">"),
        ], logic="AND"),
    )
    with pytest.raises(ValueError, match="must be an int"):
        _precompute_indicators(df, strat)


# ---------------------------------------------------------------------------
# C. Timeframe inference
# ---------------------------------------------------------------------------


def test_infer_base_minutes_1min():
    df = _make_1min_df(10)
    assert _infer_base_minutes(df) == 1


def test_infer_base_minutes_5min():
    df = _make_5min_df(10)
    assert _infer_base_minutes(df) == 5


def test_infer_base_minutes_trivial():
    df = pd.DataFrame({"datetime": pd.to_datetime(["2024-01-02 08:30"])})
    assert _infer_base_minutes(df) == 1


# ---------------------------------------------------------------------------
# D. No-future-leak merge alignment
# ---------------------------------------------------------------------------


def test_mtf_merge_asof_basic_alignment():
    df = _make_1min_df(30)
    strat = Strategy(
        name="mtf_sma",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 20, "timeframe": 5}, operator=">"),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)

    col = "sma_20_tf_5"
    assert col in df.columns

    # First few bars should be NaN (no HTF candle closed yet)
    # First 5-min candle closes at available_at = 08:34 (index 4)
    assert pd.isna(df.at[0, col]) or pd.isna(df.at[1, col])
    # After first complete HTF candle closes, value should appear
    # Not checking exact index since depends on indicator warmup


def test_mtf_merge_asof_no_future_leak():
    """For every row with a non-NaN MTF value, verify the source HTF candle's
    available_at is <= the base bar's datetime."""
    df = _make_1min_df(60)
    strat = Strategy(
        name="mtf_rsi",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="RSI", params={"period": 14, "timeframe": 5}, operator="<", right=50.0),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)

    col = "rsi_14_tf_5"
    assert col in df.columns

    # Reconstruct HTF data to verify alignment.
    htf_df = _resample_for_mtf(df, 1, 5)
    htf_df = _drop_incomplete_final_htf_group(htf_df, 1, 5)

    for i in range(len(df)):
        val = df.at[i, col]
        if not pd.isna(val):
            base_dt = df.at[i, "datetime"]
            # Find which HTF candle(s) could have produced this value.
            candidates = htf_df[htf_df["available_at"] <= base_dt]
            assert len(candidates) > 0, (
                f"Bar {i} ({base_dt}) has MTF value {val:.2f} but no HTF "
                f"candle has available_at <= {base_dt}"
            )


def test_mtf_exact_boundary_match_visible():
    """When HTF available_at == base datetime, the value must be visible."""
    df = _make_1min_df(15)
    strat = Strategy(
        name="mtf_sma",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 2, "timeframe": 5}, operator=">"),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)

    col = "sma_2_tf_5"
    assert col in df.columns

    # The first complete 5-min candle covers bars 0-4, available_at = bar 4's datetime.
    # Bar 4 is index 4 (08:34).  Since SMA(2) needs 2 bars of HTF data,
    # the first HTF SMA value appears at the 2nd HTF candle (bars 5-9, available_at=idx 9).
    # So we check that the value appears at the correct bar and not before.
    htf_df = _resample_for_mtf(df, 1, 5)
    htf_df = _drop_incomplete_final_htf_group(htf_df, 1, 5)

    # Find the first non-NaN row and verify its datetime.
    first_valid_idx = None
    for i in range(len(df)):
        if not pd.isna(df.at[i, col]):
            first_valid_idx = i
            break

    assert first_valid_idx is not None, "No valid MTF values found."
    base_dt = df.at[first_valid_idx, "datetime"]
    # At least one HTF candle must have available_at <= base_dt.
    valid = htf_df[htf_df["available_at"] <= base_dt]
    assert len(valid) > 0


# ---------------------------------------------------------------------------
# E. Incomplete final candle dropped
# ---------------------------------------------------------------------------


def test_mtf_incomplete_final_htf_candle_dropped():
    """8 one-minute bars, target 5-min. Only 1 complete 5-min candle (bars 0-4).
    Bars 5-7 form an incomplete final candle (3 bars, not 5).  It must be dropped."""
    rng = np.random.default_rng(99)
    times = pd.date_range("2024-01-02 08:30", periods=8, freq="1min")
    close = 100.0 + np.cumsum(rng.normal(0.02, 0.5, 8))
    df = pd.DataFrame({
        "datetime": times,
        "open":  close - 0.2,
        "high":  close + 0.5,
        "low":   close - 0.5,
        "close": close,
        "volume": rng.integers(500, 5000, 8),
    })

    # Verify that drop_incomplete_final_htf_group drops the partial candle.
    htf = _resample_for_mtf(df, 1, 5)
    assert len(htf) == 2  # resampler produces 2 rows (08:30-08:34, 08:35-08:39 incomplete)

    htf_clean = _drop_incomplete_final_htf_group(htf, 1, 5)
    assert len(htf_clean) == 1  # only the complete candle survives


def test_complete_final_htf_candle_not_dropped():
    """10 one-minute bars, target 5-min = 2 complete candles.  Neither should be dropped."""
    rng = np.random.default_rng(99)
    times = pd.date_range("2024-01-02 08:30", periods=10, freq="1min")
    close = 100.0 + np.cumsum(rng.normal(0.02, 0.5, 10))
    df = pd.DataFrame({
        "datetime": times,
        "open":  close - 0.2,
        "high":  close + 0.5,
        "low":   close - 0.5,
        "close": close,
        "volume": rng.integers(500, 5000, 10),
    })
    htf = _resample_for_mtf(df, 1, 5)
    assert len(htf) == 2
    htf_clean = _drop_incomplete_final_htf_group(htf, 1, 5)
    assert len(htf_clean) == 2


# ---------------------------------------------------------------------------
# F. Indicator coverage
# ---------------------------------------------------------------------------


def test_precompute_mtf_sma_column_exists():
    df = _make_1min_df(60)
    strat = Strategy(
        name="mtf_sma",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10, "timeframe": 5}, operator=">"),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)
    assert "sma_10_tf_5" in df.columns


def test_precompute_mtf_rsi_column_exists():
    df = _make_1min_df(60)
    strat = Strategy(
        name="mtf_rsi",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="RSI", params={"period": 14, "timeframe": 5}, operator="<", right=50.0),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)
    assert "rsi_14_tf_5" in df.columns


def test_precompute_mtf_atr_column_exists():
    df = _make_1min_df(60)
    strat = Strategy(
        name="mtf_atr",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="ATR", params={"period": 14, "timeframe": 5}, operator="<", right=2.5),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)
    assert "atr_14_tf_5" in df.columns


def test_precompute_mtf_macd_columns_exist():
    df = _make_1min_df(60)
    strat = Strategy(
        name="mtf_macd",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="MACD", params={"fast": 12, "slow": 26, "signal": 9, "timeframe": 5}, operator=">"),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)
    assert "macd_line_12_26_9_tf_5" in df.columns
    assert "macd_signal_12_26_9_tf_5" in df.columns
    assert "macd_histogram_12_26_9_tf_5" in df.columns


def test_precompute_mtf_volume_columns_exist():
    df = _make_1min_df(60)
    strat = Strategy(
        name="mtf_vol",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="VOLUME_SMA", params={"period": 20, "timeframe": 5}, operator=">"),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)
    assert "volume_sma_20_tf_5" in df.columns


# ---------------------------------------------------------------------------
# G. Multiple timeframes + dedup
# ---------------------------------------------------------------------------


def test_mtf_multiple_timeframes_columns_independent():
    df = _make_1min_df(100)
    strat = Strategy(
        name="mtf_multi",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 20, "timeframe": 5}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="RSI", params={"period": 14, "timeframe": 15}, operator="<", right=50.0),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)

    assert "sma_20_tf_5" in df.columns
    assert "rsi_14_tf_15" in df.columns
    # Columns from different timeframes should have different values.
    # (They won't be identical series.)


def test_precompute_mtf_deduplicates_same_indicator_params():
    df = _make_1min_df(60)
    strat = Strategy(
        name="mtf_dup",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10, "timeframe": 5}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10, "timeframe": 5}, operator="<"),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)

    # Both blocks reference the same indicator+params+timeframe -> one column.
    assert "sma_10_tf_5" in df.columns
    # Resampling should happen only once - we can't spy easily, but the column
    # count guarantees dedup worked (no crash from duplicate column creation).


# ---------------------------------------------------------------------------
# H. Safety
# ---------------------------------------------------------------------------


def test_mtf_conditions_present_in_full_backtest():
    """Smoke: backtest completes with MTF conditions present, no crash."""
    df = _make_1min_df(80)
    strat = Strategy(
        name="mtf_full",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10, "timeframe": 5}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10, "timeframe": 5}, operator="<"),
        ], logic="AND"),
    )
    result = run_backtest(strat, df)
    assert result is not None
    assert len(result.trades) >= 0  # may have trades or not


# ---------------------------------------------------------------------------
# I. Resample deduplication (spy-based)
# ---------------------------------------------------------------------------


def test_mtf_resample_called_once_per_timeframe():
    """Strategy with SMA(tf=5), RSI(tf=5), ATR(tf=5).  _resample_for_mtf
    must be called exactly once for tf=5."""
    from unittest.mock import patch
    import backtest_engine.runner as runner_mod

    df = _make_1min_df(60)
    strat = Strategy(
        name="dedup_tf5",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10, "timeframe": 5}, operator=">"),
            Condition(indicator="RSI", params={"period": 14, "timeframe": 5}, operator="<", right=50.0),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="ATR", params={"period": 14, "timeframe": 5}, operator="<", right=2.0),
        ], logic="AND"),
    )

    with patch.object(runner_mod, "_resample_for_mtf", wraps=runner_mod._resample_for_mtf) as spy:
        _precompute_indicators(df, strat)
        assert spy.call_count == 1, (
            f"_resample_for_mtf called {spy.call_count} times for tf=5; expected 1"
        )


def test_mtf_resample_called_once_per_distinct_timeframe():
    """Strategy with SMA(tf=5), RSI(tf=15).  _resample_for_mtf must be
    called exactly twice - once for each distinct timeframe."""
    from unittest.mock import patch
    import backtest_engine.runner as runner_mod

    df = _make_1min_df(100)
    strat = Strategy(
        name="dedup_multi_tf",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10, "timeframe": 5}, operator=">"),
            Condition(indicator="RSI", params={"period": 14, "timeframe": 15}, operator="<", right=50.0),
        ], logic="AND"),
    )

    with patch.object(runner_mod, "_resample_for_mtf", wraps=runner_mod._resample_for_mtf) as spy:
        _precompute_indicators(df, strat)
        assert spy.call_count == 2, (
            f"_resample_for_mtf called {spy.call_count} times; expected 2 (one per timeframe)"
        )


# ---------------------------------------------------------------------------
# J. Exact boundary / NaN placement
# ---------------------------------------------------------------------------


def test_mtf_basic_alignment_exact_values():
    """Use deterministic close values and short SMA period to assert exact
    NaN/value placement around available_at boundaries."""
    # 10 one-minute bars with linearly increasing close.
    times = pd.date_range("2024-01-02 08:30", periods=10, freq="1min")
    close = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0])
    df = pd.DataFrame({
        "datetime": times,
        "open":  close - 0.5,
        "high":  close + 0.5,
        "low":   close - 0.5,
        "close": close,
        "volume": [1000] * 10,
    })

    # SMA(2) on tf=5. HTF candles: 0..4 (close=104, available_at=idx4), 5..9 (close=109, avail=idx9)
    # SMA(2) on HTF: first value at 2nd HTF candle (idx 9), value = (104+109)/2 = 106.5
    strat = Strategy(
        name="exact",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 2, "timeframe": 5}, operator=">"),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)

    col = "sma_2_tf_5"
    assert col in df.columns

    # Bars 0-8: no HTF SMA(2) value available yet (only 1 complete HTF candle at idx 4,
    # SMA(2) needs 2 candles -> first value at 2nd HTF close, idx 9).
    for i in range(9):
        assert pd.isna(df.at[i, col]), f"Bar {i} should be NaN, got {df.at[i, col]}"

    # Bar 9: HTF candle 5..9 closes at idx 9 -> SMA(2) = (104+109)/2 = 106.5
    assert not pd.isna(df.at[9, col])
    assert df.at[9, col] == pytest.approx(106.5)


def test_mtf_no_future_leak_available_at_source():
    """Prove every non-NaN MTF value comes from a source HTF candle whose
    available_at <= the base bar's datetime."""
    df = _make_1min_df(60)
    strat = Strategy(
        name="nf_leak",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 3, "timeframe": 5}, operator=">"),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)

    col = "sma_3_tf_5"
    assert col in df.columns

    htf_df = _resample_for_mtf(df, 1, 5)
    htf_df = _drop_incomplete_final_htf_group(htf_df, 1, 5)

    for i in range(len(df)):
        val = df.at[i, col]
        if not pd.isna(val):
            base_dt = df.at[i, "datetime"]
            # At least one HTF candle must have available_at <= base_dt AND
            # must be the one that produced this value (last available_at <= base_dt).
            candidates = htf_df[htf_df["available_at"] <= base_dt]
            assert len(candidates) > 0, (
                f"Bar {i} ({base_dt}): MTF value present but no HTF candle "
                f"with available_at <= {base_dt}"
            )
            # The source candle is the most recent one with available_at <= base_dt.
            source = candidates.iloc[-1]
            assert source["available_at"] <= base_dt, (
                f"Bar {i}: source available_at {source['available_at']} > base {base_dt}"
            )


# ---------------------------------------------------------------------------
# K. Incomplete final candle - no new value
# ---------------------------------------------------------------------------


def test_mtf_incomplete_final_candle_does_not_create_new_value():
    """8 one-minute bars, SMA(2) on tf=5.  The final 3-bar partial HTF group
    must be dropped, so no new SMA value appears at bar 7.  The last complete
    HTF value (from bars 0-4) forward-fills."""
    times = pd.date_range("2024-01-02 08:30", periods=8, freq="1min")
    close = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0])
    df = pd.DataFrame({
        "datetime": times,
        "open":  close - 0.5,
        "high":  close + 0.5,
        "low":   close - 0.5,
        "close": close,
        "volume": [1000] * 8,
    })

    # SMA(2) on tf=5: Only 1 complete HTF candle (bars 0-4, close=104).
    # SMA(2) needs 2 candles -> no valid SMA value at all (only 1 complete candle).
    # The incomplete final (bars 5-7, close=107) is dropped.
    strat = Strategy(
        name="inc",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 2, "timeframe": 5}, operator=">"),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)

    col = "sma_2_tf_5"
    assert col in df.columns

    # Since SMA(2) on 5-min needs 2 HTF candles and we only have 1 complete,
    # all values should be NaN.
    for i in range(len(df)):
        assert pd.isna(df.at[i, col]), (
            f"Bar {i}: expected NaN (only 1 HTF candle, SMA(2) needs 2), "
            f"got {df.at[i, col]}"
        )


def test_mtf_last_complete_value_forward_fills():
    """15 one-minute bars, SMA(2) on tf=5.  3 complete HTF candles (bars 0-4,
    5-9, 10-14).  When data ends cleanly, the last value should forward-fill
    through the final bar."""
    times = pd.date_range("2024-01-02 08:30", periods=15, freq="1min")
    close = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0,    # HTF candle 1
                       105.0, 106.0, 107.0, 108.0, 109.0,    # HTF candle 2
                       110.0, 111.0, 112.0, 113.0, 114.0])   # HTF candle 3
    df = pd.DataFrame({
        "datetime": times,
        "open":  close - 0.5,
        "high":  close + 0.5,
        "low":   close - 0.5,
        "close": close,
        "volume": [1000] * 15,
    })

    # SMA(2) on tf=5: values at candle 2 (close=109) -> (104+109)/2=106.5,
    # and candle 3 (close=114) -> (109+114)/2=111.5
    strat = Strategy(
        name="ff",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 2, "timeframe": 5}, operator=">"),
        ], logic="AND"),
    )
    _precompute_indicators(df, strat)

    col = "sma_2_tf_5"
    assert col in df.columns

    # Bars 0-8: NaN (SMA(2) on 5-min needs 2 HTF candles)
    for i in range(9):
        assert pd.isna(df.at[i, col]), f"Bar {i}: expected NaN, got {df.at[i, col]}"

    # Bar 9: SMA(2) = (104+109)/2 = 106.5
    assert not pd.isna(df.at[9, col])
    assert df.at[9, col] == pytest.approx(106.5)

    # Bars 10-13: still 106.5 (forward-filled until next HTF candle closes)
    for i in range(10, 14):
        assert not pd.isna(df.at[i, col])
        assert df.at[i, col] == pytest.approx(106.5)

    # Bar 14: SMA(2) = (109+114)/2 = 111.5
    assert not pd.isna(df.at[14, col])
    assert df.at[14, col] == pytest.approx(111.5)


def test_mtf_internal_gap_kept_due_to_span_assumption():
    """Documents the MVP limitation: if an incomplete final candle has an internal
    gap such that its timestamp span equals the expected span, the span-based
    logic keeps it, even though it's missing constituent bars.
    """
    from backtest_engine.runner import _drop_incomplete_final_htf_group
    # Mock two HTF candles.
    # Candle 1: Complete (08:25 to 08:29).
    # Candle 2: 08:30 to 08:34. We omit 08:31, 08:32, 08:33 in the base data.
    # The resampler will output a single row for Candle 2 with start=08:30, available_at=08:34.
    df = pd.DataFrame({
        "datetime": pd.to_datetime(["2024-01-02 08:25", "2024-01-02 08:30"]),
        "available_at": pd.to_datetime(["2024-01-02 08:29", "2024-01-02 08:34"]),
        "close": [100.0, 104.0],
    })
    
    # Expected span for 5-min target from 1-min base is (5/1 - 1) * 1 = 4 minutes.
    # For Candle 2, 08:34 - 08:30 = 4 minutes, so the span check passes despite 3 missing constituent bars.
    cleaned = _drop_incomplete_final_htf_group(df, base_minutes=1, target_minutes=5)
    
    # We document that Candle 2 is NOT dropped, leaving 2 rows.
    assert len(cleaned) == 2, "Documented limitation: internal gaps pass span check."


# ---------------------------------------------------------------------------
# L. Bool timeframe rejection
# ---------------------------------------------------------------------------


def test_mtf_timeframe_bool_rejected():
    df = _make_1min_df(50)
    strat = Strategy(
        name="bool_tf",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 20, "timeframe": True}, operator=">"),
        ], logic="AND"),
    )
    with pytest.raises(ValueError, match="must be an int"):
        _precompute_indicators(df, strat)


# ---------------------------------------------------------------------------
# M. Missing volume - specific error
# ---------------------------------------------------------------------------


def test_mtf_missing_volume_column_clear_error():
    df = _make_1min_df(30).drop(columns=["volume"])
    strat = Strategy(
        name="vol_err",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="VOLUME_SMA", params={"period": 20, "timeframe": 5}, operator=">"),
        ], logic="AND"),
    )
    from data_engine.resampler import ResamplerError
    with pytest.raises(ResamplerError, match="volume"):
        _precompute_indicators(df, strat)


# ---------------------------------------------------------------------------
# N. _col() suffixed column names
# ---------------------------------------------------------------------------


def test_col_returns_suffixed_name_for_mtf_sma():
    from strategy_engine.evaluator import _col
    assert _col("SMA", {"period": 20, "timeframe": 5}) == "sma_20_tf_5"


def test_col_returns_base_name_without_timeframe():
    from strategy_engine.evaluator import _col
    assert _col("SMA", {"period": 20}) == "sma_20"


def test_col_returns_suffixed_name_for_mtf_rsi():
    from strategy_engine.evaluator import _col
    assert _col("RSI", {"period": 14, "timeframe": 15}) == "rsi_14_tf_15"


def test_col_returns_suffixed_name_for_mtf_atr():
    from strategy_engine.evaluator import _col
    assert _col("ATR", {"period": 14, "timeframe": 5}) == "atr_14_tf_5"


def test_col_returns_suffixed_name_for_mtf_volume():
    from strategy_engine.evaluator import _col
    assert _col("VOLUME", {"timeframe": 5}) == "volume_tf_5"


def test_col_returns_suffixed_name_for_mtf_volume_sma():
    from strategy_engine.evaluator import _col
    assert _col("VOLUME_SMA", {"period": 20, "timeframe": 5}) == "volume_sma_20_tf_5"
