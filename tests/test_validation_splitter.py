"""Tests for validation engine data splitter — Task 013."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from data_engine.normalizer import normalize
from validation_engine.splitter import SplitError, SplitResult, split_by_date, split_by_ratio

# TXF fixture for cross-format compatibility.
SAMPLE_TXF = Path(__file__).resolve().parent.parent / "sample_data" / "sample_txf.csv"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_test_df(n_bars: int = 100) -> pd.DataFrame:
    """Create a minimal normalized OHLCV DataFrame."""
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="1min")
    close = np.linspace(100.0, 150.0, n_bars)
    return pd.DataFrame({
        "datetime": times,
        "open":  close - 0.5,
        "high":  close + 1.0,
        "low":   close - 1.0,
        "close": close,
        "volume": np.full(n_bars, 1000),
    })


# ---------------------------------------------------------------------------
# split_by_ratio — happy path
# ---------------------------------------------------------------------------


def test_ratio_split_exact_sizes():
    """100 bars, 60/20/20 → train=60, val=20, oos=20."""
    df = _make_test_df(100)
    result = split_by_ratio(df, 0.6, 0.2, 0.2)

    assert len(result.train) == 60
    assert len(result.validation) == 20
    assert len(result.oos) == 20
    assert result.train_meta["row_count"] == 60
    assert result.validation_meta["row_count"] == 20
    assert result.oos_meta["row_count"] == 20


def test_ratio_split_metadata():
    """Metadata must include name, row_count, start, end for each segment."""
    df = _make_test_df(100)
    result = split_by_ratio(df, 0.6, 0.2, 0.2)

    for meta in (result.train_meta, result.validation_meta, result.oos_meta):
        assert meta["name"] in ("train", "validation", "oos")
        assert meta["row_count"] > 0
        assert meta["start"] is not None
        assert meta["end"] is not None


def test_ratio_split_no_overlap():
    """Train, validation, and OOS must share zero rows."""
    df = _make_test_df(100)
    result = split_by_ratio(df, 0.6, 0.2, 0.2)

    train_idx = set(result.train.index)
    val_idx = set(result.validation.index)
    oos_idx = set(result.oos.index)

    assert train_idx.isdisjoint(val_idx)
    assert train_idx.isdisjoint(oos_idx)
    assert val_idx.isdisjoint(oos_idx)


def test_ratio_split_chronological_order():
    """Each segment must be internally chronologically ordered and
    train < validation < oos in time."""
    df = _make_test_df(100)
    result = split_by_ratio(df, 0.6, 0.2, 0.2)

    assert result.train["datetime"].is_monotonic_increasing
    assert result.validation["datetime"].is_monotonic_increasing
    assert result.oos["datetime"].is_monotonic_increasing

    assert result.train["datetime"].max() < result.validation["datetime"].min()
    assert result.validation["datetime"].max() < result.oos["datetime"].min()


def test_ratio_split_zero_validation():
    """validation_ratio=0 must produce validation=None."""
    df = _make_test_df(100)
    result = split_by_ratio(df, 0.7, 0.0, 0.3)

    assert len(result.train) == 70
    assert result.validation is None
    assert len(result.oos) == 30
    assert result.validation_meta["row_count"] == 0


def test_ratio_split_rounding():
    """97 bars with 60/20/20 → train≈58, val≈19, oos=20 (rounding)."""
    df = _make_test_df(97)
    result = split_by_ratio(df, 0.6, 0.2, 0.2)

    assert len(result.train) + len(result.validation) + len(result.oos) == 97
    assert abs(len(result.train) - 58) <= 1
    assert abs(len(result.validation) - 19) <= 1


# ---------------------------------------------------------------------------
# split_by_date — happy path
# ---------------------------------------------------------------------------


def test_date_split_boundaries():
    """Split at explicit datetime boundaries."""
    df = _make_test_df(100)
    result = split_by_date(df, train_end="2024-01-02 09:00:00",
                           validation_end="2024-01-02 09:30:00")

    # Train: bars up to and including 09:00 (31 bars: 08:30-09:00).
    assert len(result.train) == 31
    # Validation: 09:01-09:30 (30 bars).
    assert len(result.validation) == 30
    # OOS: 09:31-10:09 (39 bars).
    assert len(result.oos) == 39

    assert result.train["datetime"].max() <= pd.Timestamp("2024-01-02 09:00")
    assert result.validation["datetime"].max() <= pd.Timestamp("2024-01-02 09:30")


def test_date_split_no_validation():
    """When validation_end is None, no validation segment."""
    df = _make_test_df(100)
    result = split_by_date(df, train_end="2024-01-02 09:00:00")

    assert result.train is not None
    assert result.validation is None
    assert result.oos is not None
    assert result.validation_meta["row_count"] == 0


def test_date_split_no_overlap():
    """Date-based splits must be non-overlapping."""
    df = _make_test_df(100)
    result = split_by_date(df, train_end="2024-01-02 09:00:00",
                           validation_end="2024-01-02 09:30:00")

    train_idx = set(result.train.index)
    val_idx = set(result.validation.index)
    oos_idx = set(result.oos.index)

    assert train_idx.isdisjoint(val_idx)
    assert train_idx.isdisjoint(oos_idx)
    assert val_idx.isdisjoint(oos_idx)


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_invalid_ratios_raise():
    """Ratios not summing to 1.0 must raise SplitError."""
    df = _make_test_df(100)
    with pytest.raises(SplitError, match="must sum to 1"):
        split_by_ratio(df, 0.5, 0.3, 0.3)  # = 1.1


def test_negative_ratio_raises():
    """Negative ratios must raise SplitError."""
    df = _make_test_df(100)
    with pytest.raises(SplitError, match="must be in"):
        split_by_ratio(df, -0.1, 0.5, 0.6)


def test_empty_dataframe_raises():
    """Empty DataFrame must raise SplitError."""
    df = pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])
    with pytest.raises(SplitError, match="empty"):
        split_by_ratio(df, 0.6, 0.2, 0.2)


def test_missing_datetime_column_raises():
    """DataFrame without datetime must raise SplitError."""
    df = pd.DataFrame({"open": [1.0], "high": [2.0], "low": [0.5], "close": [1.5], "volume": [100]})
    with pytest.raises(SplitError, match="datetime"):
        split_by_ratio(df, 0.6, 0.2, 0.2)


def test_date_split_validation_before_train_raises():
    """validation_end <= train_end must raise SplitError."""
    df = _make_test_df(100)
    with pytest.raises(SplitError, match="must be after"):
        split_by_date(df, train_end="2024-01-02 09:30:00",
                      validation_end="2024-01-02 09:00:00")


def test_non_datetime64_column_raises():
    """datetime column must be datetime64 dtype."""
    df = _make_test_df(10)
    df["datetime"] = df["datetime"].astype(str)
    with pytest.raises(SplitError, match="datetime64"):
        split_by_ratio(df, 0.6, 0.2, 0.2)


# ---------------------------------------------------------------------------
# TXF fixture compatibility
# ---------------------------------------------------------------------------


def test_txf_sample_can_be_split_by_ratio():
    """The TXF sample fixture must work with split_by_ratio."""
    df = pd.read_csv(SAMPLE_TXF)
    normalized = normalize(df)

    result = split_by_ratio(normalized, 0.4, 0.3, 0.3)
    assert len(result.train) > 0
    assert len(result.validation) > 0
    assert len(result.oos) > 0


def test_txf_sample_can_be_split_by_date():
    """The TXF sample fixture must work with split_by_date."""
    df = pd.read_csv(SAMPLE_TXF)
    normalized = normalize(df)

    mid = normalized["datetime"].iloc[7]
    result = split_by_date(normalized, train_end=str(mid))
    assert result.train is not None
    assert result.oos is not None
