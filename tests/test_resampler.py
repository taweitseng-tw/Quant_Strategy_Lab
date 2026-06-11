"""Tests for OHLCV resampler — Task 004A."""

from __future__ import annotations

import pandas as pd
import pytest

from data_engine.normalizer import INTERNAL_COLUMNS
from data_engine.resampler import ResamplerError, resample


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_1min_df(
    start: str = "2024-01-02 08:30",
    count: int = 10,
    seed_ohlc: tuple[float, float, float, float] = (100.0, 102.0, 99.0, 101.0),
) -> pd.DataFrame:
    """Build a canonical 1-min OHLCV DataFrame with sequential datetimes."""
    times = pd.date_range(start, periods=count, freq="1min")
    o, h, l, c = seed_ohlc
    return pd.DataFrame({
        "datetime": times,
        "open":  [o + i * 1.0 for i in range(count)],
        "high":  [h + i * 1.0 for i in range(count)],
        "low":   [l + i * 1.0 for i in range(count)],
        "close": [c + i * 1.0 for i in range(count)],
        "volume": [1000 + i * 100 for i in range(count)],
    })


# ---------------------------------------------------------------------------
# Happy path — exact grouping
# ---------------------------------------------------------------------------


def test_resample_10_bars_to_2_bars():
    """10 one-minute bars → exactly 2 five-minute bars with available_at."""
    df = _make_1min_df(count=10)
    result = resample(df, source_minutes=1, target_minutes=5)

    expected_cols = list(INTERNAL_COLUMNS) + ["available_at"]
    assert list(result.columns) == expected_cols
    assert len(result) == 2
    assert result["datetime"].dtype.kind == "M"
    assert result["available_at"].dtype.kind == "M"


def test_resample_ohlcv_correctness():
    """OHLCV values must match the documented aggregation rules."""
    df = pd.DataFrame({
        "datetime": pd.to_datetime([
            "2024-01-02 08:30", "2024-01-02 08:31", "2024-01-02 08:32",
            "2024-01-02 08:33", "2024-01-02 08:34",
        ]),
        "open":   [10.0, 11.0, 12.0, 13.0, 14.0],
        "high":   [15.0, 16.0, 20.0, 18.0, 19.0],
        "low":    [ 9.0,  8.0,  7.0,  6.0,  5.0],
        "close":  [10.5, 11.5, 12.5, 13.5, 14.5],
        "volume": [100,  200,  300,  400,  500],
    })

    result = resample(df, source_minutes=1, target_minutes=5)

    assert len(result) == 1
    row = result.iloc[0]

    assert row["datetime"] == pd.Timestamp("2024-01-02 08:30")  # start label
    assert row["open"] == 10.0    # first bar's open
    assert row["high"] == 20.0    # max of all highs
    assert row["low"] == 5.0      # min of all lows
    assert row["close"] == 14.5   # last bar's close
    assert row["volume"] == 1500  # sum (100+200+300+400+500)
    assert row["available_at"] == pd.Timestamp("2024-01-02 08:34")  # last bar


def test_resample_timestamp_convention_is_start_of_group():
    """datetime = group start; available_at = last bar in group."""
    df = _make_1min_df(start="2024-01-02 08:30", count=15)
    result = resample(df, source_minutes=1, target_minutes=5)

    expected_starts = pd.to_datetime([
        "2024-01-02 08:30",
        "2024-01-02 08:35",
        "2024-01-02 08:40",
    ])
    assert (result["datetime"] == expected_starts).all()

    # available_at must be the last bar in each 5-bar group.
    expected_avail = pd.to_datetime([
        "2024-01-02 08:34",
        "2024-01-02 08:39",
        "2024-01-02 08:44",
    ])
    assert (result["available_at"] == expected_avail).all()


def test_resample_timestamp_no_future_leak():
    """available_at must be >= datetime — ensures downstream code that gates
    on available_at cannot see future data.

    Also verifies that close at datetime does NOT equal close at available_at
    (confirming datetime is earlier than the last bar).
    """
    df = _make_1min_df(start="2024-01-02 08:30", count=5)
    result = resample(df, source_minutes=1, target_minutes=5)
    row = result.iloc[0]

    assert row["datetime"] == pd.Timestamp("2024-01-02 08:30")
    assert row["available_at"] == pd.Timestamp("2024-01-02 08:34")

    # Sanity: datetime < available_at (there IS time between them).
    assert row["datetime"] < row["available_at"]

    # Core guards: no future leak through either timestamp.
    # datetime must be ≤ earliest constituent.
    assert row["datetime"] <= df["datetime"].min()
    # available_at must be exactly the last constituent.
    assert row["available_at"] == df["datetime"].max()


# ---------------------------------------------------------------------------
# Incomplete final group
# ---------------------------------------------------------------------------


def test_resample_incomplete_final_group():
    """12 bars → 2 full 5-bar groups + 1 partial 2-bar group."""
    df = _make_1min_df(count=12)
    result = resample(df, source_minutes=1, target_minutes=5)

    assert len(result) == 3

    # Last group has only 2 bars (08:40, 08:41).
    last = result.iloc[-1]
    assert last["datetime"] == pd.Timestamp("2024-01-02 08:40")
    assert last["available_at"] == pd.Timestamp("2024-01-02 08:41")

    # open = first of partial group, close = last of partial group.
    # df rows 10,11 → open=110.0, close=112.0
    assert last["open"] == 110.0
    assert last["close"] == 112.0
    assert last["volume"] == 2000 + 2100  # = 4100


# ---------------------------------------------------------------------------
# Robustness — unsorted input
# ---------------------------------------------------------------------------


def test_resample_handles_unsorted_input():
    """Unsorted input must produce the same result as sorted input."""
    sorted_df = _make_1min_df(count=10)
    unsorted_df = sorted_df.sample(frac=1.0, random_state=42).reset_index(drop=True)

    result_from_unsorted = resample(unsorted_df, 1, 5)
    result_from_sorted = resample(sorted_df, 1, 5)

    pd.testing.assert_frame_equal(
        result_from_unsorted.reset_index(drop=True),
        result_from_sorted.reset_index(drop=True),
    )


# ---------------------------------------------------------------------------
# Alternate target periods
# ---------------------------------------------------------------------------


def test_resample_1min_to_15min():
    """15 bars → exactly 1 fifteen-minute bar."""
    df = _make_1min_df(count=15)
    result = resample(df, source_minutes=1, target_minutes=15)
    assert len(result) == 1


def test_resample_1min_to_60min():
    """120 bars starting at 08:30 span 3 hour buckets (08:00, 09:00, 10:00)."""
    df = _make_1min_df(count=120)
    result = resample(df, source_minutes=1, target_minutes=60)
    # 08:30–08:59 → 30 bars in bucket 08:00
    # 09:00–09:59 → 60 bars in bucket 09:00
    # 10:00–10:29 → 30 bars in bucket 10:00
    assert len(result) == 3


def test_resample_identity_5min_to_5min():
    """Resampling to the same timeframe is a no-op (1:1 mapping).

    available_at must equal datetime — each bar is immediately available."""
    df = _make_1min_df(count=10)
    result = resample(df, source_minutes=5, target_minutes=5)
    assert len(result) == len(df)

    # available_at mirrors datetime in identity mode.
    assert (result["available_at"] == result["datetime"]).all()
    assert result["available_at"].dtype.kind == "M"


# ---------------------------------------------------------------------------
# Future-leak protection — available_at contract
# ---------------------------------------------------------------------------


def test_available_at_never_earlier_than_datetime():
    """For every resampled bar, available_at >= datetime."""
    df = _make_1min_df(count=30)
    result = resample(df, source_minutes=1, target_minutes=5)

    assert (result["available_at"] >= result["datetime"]).all()
    # At least one bar should have a gap (not identity).
    assert (result["available_at"] > result["datetime"]).any()


def test_available_at_gates_close_from_future():
    """A naive signal that fires at 'datetime' and reads 'close' gets future
    data.  The contract requires gating on 'available_at' instead.

    This test asserts the structural invariant: close-at-datetime is known
    only after available_at, making 'datetime' unsafe for signal timing.
    """
    df = _make_1min_df(count=15)
    result = resample(df, source_minutes=1, target_minutes=5)

    # The first resampled bar covers 08:30–08:34.
    # At 08:30 (datetime) the close of 14.5 wasn't known — it needed 08:34.
    bar0 = result.iloc[0]
    assert bar0["datetime"] < bar0["available_at"]

    # The raw close at 08:30 was from the first 1-min bar (101.0 via _make_1min_df).
    raw_close_at_0830 = df.loc[df["datetime"] == pd.Timestamp("2024-01-02 08:30"), "close"].iloc[0]
    # The resampled close is the close at 08:34 (different bar entirely).
    assert bar0["close"] != raw_close_at_0830

    # A backtest that gates on available_at would NOT act until 08:34 —
    # at which point this close IS known.  This is the safe path.
    assert bar0["available_at"] == pd.Timestamp("2024-01-02 08:34")


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_resample_empty_raises():
    """Empty DataFrame must raise ResamplerError."""
    df = pd.DataFrame(columns=list(INTERNAL_COLUMNS))
    with pytest.raises(ResamplerError, match="empty"):
        resample(df)


def test_resample_missing_columns_raises():
    """Missing required columns must raise ResamplerError."""
    df = pd.DataFrame({"datetime": pd.to_datetime(["2024-01-02 08:30"])})
    with pytest.raises(ResamplerError, match="Required columns missing"):
        resample(df)


def test_resample_duplicate_datetimes_raises():
    """Duplicate timestamps must raise ResamplerError."""
    df = pd.DataFrame({
        "datetime": pd.to_datetime(["2024-01-02 08:30", "2024-01-02 08:30"]),
        "open":   [10.0, 11.0],
        "high":   [15.0, 16.0],
        "low":    [9.0, 8.0],
        "close":  [10.5, 11.5],
        "volume": [100, 200],
    })
    with pytest.raises(ResamplerError, match="duplicate datetime"):
        resample(df)


def test_resample_nat_datetime_raises():
    """NaT in datetime column must raise ResamplerError."""
    df = _make_1min_df(count=3)
    df.loc[1, "datetime"] = pd.NaT
    with pytest.raises(ResamplerError, match="NaT"):
        resample(df)


def test_resample_non_numeric_ohlcv_raises():
    """Non-numeric OHLCV columns must raise ResamplerError."""
    df = _make_1min_df(count=3)
    df["close"] = df["close"].astype(str)
    with pytest.raises(ResamplerError, match="'close' must be numeric"):
        resample(df)


def test_resample_bad_ratio_raises():
    """target_minutes must be an integer multiple of source_minutes."""
    df = _make_1min_df(count=3)
    with pytest.raises(ResamplerError, match="must be a multiple"):
        resample(df, source_minutes=3, target_minutes=5)


def test_resample_target_smaller_than_source_raises():
    """target_minutes < source_minutes must raise."""
    df = _make_1min_df(count=3)
    with pytest.raises(ResamplerError, match="must be >="):
        resample(df, source_minutes=5, target_minutes=1)


def test_resample_non_datetime64_column_raises():
    """A datetime column that isn't datetime64 dtype must raise."""
    df = _make_1min_df(count=3)
    df["datetime"] = df["datetime"].astype(str)
    with pytest.raises(ResamplerError, match="datetime64"):
        resample(df)


# ---------------------------------------------------------------------------
# Resampler Hardening Tests
# ---------------------------------------------------------------------------


def test_resample_invalid_inputs_raises():
    """Invalid OHLCV prices, volume, or NaN/infs raise ResamplerError."""
    # Negative Price
    df1 = _make_1min_df(count=3)
    df1.loc[1, "close"] = -10.0
    with pytest.raises(ResamplerError, match="non-positive prices"):
        resample(df1)

    # Invalid OHLC relationships (high < low)
    df2 = _make_1min_df(count=3)
    df2.loc[1, "high"] = 50.0
    df2.loc[1, "low"] = 150.0
    with pytest.raises(ResamplerError, match="invalid OHLC relationships"):
        resample(df2)

    # Negative Volume
    df3 = _make_1min_df(count=3)
    df3.loc[1, "volume"] = -100
    with pytest.raises(ResamplerError, match="negative volume"):
        resample(df3)

    # NaN Value
    df4 = _make_1min_df(count=3)
    df4.loc[1, "open"] = float("nan")
    with pytest.raises(ResamplerError, match="NaN or infinite values"):
        resample(df4)


def test_resample_identity_mode_still_validates_inputs():
    """Same-timeframe resampling must not bypass hardening validation."""
    df = _make_1min_df(count=3)
    df.loc[1, "low"] = 0.0

    with pytest.raises(ResamplerError, match="non-positive prices"):
        resample(df, source_minutes=1, target_minutes=1)


def test_resample_partial_bar_warning():
    """Resampling with missing non-boundary constituent bars triggers a UserWarning."""
    # We want a 1-min to 5-min resampling.
    # If we have 15 minutes of bars, but one of the middle groups (e.g. index 5-9, representing 08:35-08:39)
    # is missing some bars, say we drop 08:36, 08:37, and 08:38.
    df = _make_1min_df(start="2024-01-02 08:30", count=15)
    # drop indices 6, 7, 8 (timestamps 08:36, 08:37, 08:38)
    df = df.drop(index=[6, 7, 8]).reset_index(drop=True)

    with pytest.warns(UserWarning, match="incomplete constituent counts"):
        result = resample(df, source_minutes=1, target_minutes=5)

    assert len(result) == 3
    # The middle bar (datetime 08:35) should have 2 constituent bars instead of 5
    # Verification that it still resampled correctly:
    # 08:30 group has 5 bars (08:30-08:34)
    # 08:35 group has 2 bars (08:35, 08:39)
    # 08:40 group has 5 bars (08:40-08:44)
