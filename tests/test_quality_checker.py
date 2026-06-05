"""Tests for data quality checker — Task 018."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from data_engine.quality_checker import DataQualityReport, check_quality


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clean_df(n_bars: int = 20) -> pd.DataFrame:
    """Create a clean normalized OHLCV DataFrame."""
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="1min")
    close = np.linspace(100.0, 120.0, n_bars)
    return pd.DataFrame({
        "datetime": times,
        "open":  close - 0.5,
        "high":  close + 1.0,
        "low":   close - 1.0,
        "close": close,
        "volume": np.full(n_bars, 1000),
    })


SAMPLE_TXF = Path(__file__).resolve().parent.parent / "sample_data" / "sample_txf.csv"


# ---------------------------------------------------------------------------
# Clean data passes
# ---------------------------------------------------------------------------


def test_clean_data_passes():
    """A valid normalized DataFrame must pass all checks."""
    df = _clean_df()
    report = check_quality(df)
    assert report.passed
    assert report.errors == []
    assert report.row_count == 20


def test_txf_sample_passes_basic_checks():
    """The TXF sample fixture must pass basic OHLCV checks."""
    df = pd.read_csv(SAMPLE_TXF)
    from data_engine.normalizer import normalize
    normalized = normalize(df)
    report = check_quality(normalized)
    assert report.passed
    assert report.errors == []


# ---------------------------------------------------------------------------
# Structural errors
# ---------------------------------------------------------------------------


def test_not_a_dataframe():
    report = check_quality([1, 2, 3])  # type: ignore[arg-type]
    assert not report.passed
    assert any("not a pandas" in e.lower() for e in report.errors)


def test_empty_dataframe():
    df = pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])
    report = check_quality(df)
    assert not report.passed
    assert any("empty" in e.lower() for e in report.errors)


def test_missing_columns():
    df = pd.DataFrame({"datetime": pd.date_range("2024-01-02", periods=3, freq="1min")})
    report = check_quality(df)
    assert not report.passed
    assert any("missing" in e.lower() for e in report.errors)


# ---------------------------------------------------------------------------
# Datetime errors
# ---------------------------------------------------------------------------


def test_non_datetime64_column():
    df = _clean_df()
    df["datetime"] = df["datetime"].astype(str)
    report = check_quality(df)
    assert not report.passed
    assert any("datetime64" in e for e in report.errors)


def test_nat_datetime():
    df = _clean_df()
    df.loc[5, "datetime"] = pd.NaT
    report = check_quality(df)
    assert not report.passed
    assert any("NaT" in e for e in report.errors)


def test_duplicate_datetime():
    df = _clean_df()
    df.loc[3, "datetime"] = df.loc[2, "datetime"]
    report = check_quality(df)
    assert not report.passed
    assert any("duplicate" in e.lower() for e in report.errors)


def test_unsorted_datetime():
    df = _clean_df()
    # Swap two rows to break sort order.
    df.iloc[2], df.iloc[8] = df.iloc[8].copy(), df.iloc[2].copy()
    report = check_quality(df)
    assert not report.passed
    assert any("sorted" in e.lower() for e in report.errors)


# ---------------------------------------------------------------------------
# Null / non-numeric
# ---------------------------------------------------------------------------


def test_null_close():
    df = _clean_df()
    df.loc[5, "close"] = np.nan
    report = check_quality(df)
    assert not report.passed
    assert any("close" in e and "null" in e for e in report.errors)


def test_non_numeric_volume():
    df = _clean_df()
    df["volume"] = df["volume"].astype(str)
    report = check_quality(df)
    assert not report.passed
    assert any("volume" in e and "numeric" in e.lower() for e in report.errors)


# ---------------------------------------------------------------------------
# OHLC relationship errors
# ---------------------------------------------------------------------------


def test_high_less_than_low():
    df = _clean_df()
    df.loc[3, "high"] = 50.0  # below low
    report = check_quality(df)
    assert not report.passed
    assert any("high < low" in e for e in report.errors)


def test_open_above_high():
    df = _clean_df()
    df.loc[3, "open"] = df.loc[3, "high"] + 10.0
    report = check_quality(df)
    assert not report.passed
    assert any("open > high" in e for e in report.errors)


def test_close_above_high():
    df = _clean_df()
    df.loc[3, "close"] = df.loc[3, "high"] + 10.0
    report = check_quality(df)
    assert not report.passed
    assert any("close > high" in e for e in report.errors)


def test_negative_volume():
    df = _clean_df()
    df.loc[3, "volume"] = -500
    report = check_quality(df)
    assert not report.passed
    assert any("negative volume" in e.lower() for e in report.errors)


def test_multiple_errors_reported():
    """A DataFrame with multiple problems must report all of them."""
    df = _clean_df()
    df.loc[0, "high"] = df.loc[0, "low"] - 1  # high < low
    df.loc[1, "volume"] = -100  # negative volume
    df.loc[3, "close"] = np.nan  # null close
    report = check_quality(df)
    assert not report.passed
    assert len(report.errors) >= 3


# ---------------------------------------------------------------------------
# Warnings (gaps, outliers)
# ---------------------------------------------------------------------------


def test_time_gap_warning():
    """A gap > 2× expected frequency must produce a warning."""
    df = _clean_df(20)
    # Insert a 10-minute gap in the middle.
    df.loc[10:, "datetime"] += pd.Timedelta(minutes=10)
    report = check_quality(df, expected_freq_minutes=1)
    assert report.passed  # gaps are warnings, not errors
    assert any("time gap" in w.lower() for w in report.warnings)


def test_outlier_jump_warning():
    """A close change > threshold % must produce a warning."""
    df = _clean_df(20)
    # Create a 10% jump — also adjust high so OHLC relationship is valid.
    df.loc[10, "close"] = df.loc[9, "close"] * 1.15
    df.loc[10, "high"] = df.loc[10, "close"] + 2.0  # keep high >= close
    report = check_quality(df, outlier_pct_threshold=5.0)
    assert report.passed  # outliers are warnings, not errors
    assert any("large_jumps" in str(report.issue_counts) or
               "close change" in w.lower() for w in report.warnings)


def test_no_warnings_when_clean():
    """Clean data with gap/outlier thresholds must produce no warnings."""
    df = _clean_df(20)
    report = check_quality(df, expected_freq_minutes=1, outlier_pct_threshold=5.0)
    assert report.warnings == []


# ---------------------------------------------------------------------------
# No mutation
# ---------------------------------------------------------------------------


def test_quality_check_does_not_mutate_input():
    """Input DataFrame must be unchanged after check."""
    df = _clean_df()
    df_copy = df.copy()
    check_quality(df, expected_freq_minutes=1, outlier_pct_threshold=5.0)
    pd.testing.assert_frame_equal(df, df_copy)


# ---------------------------------------------------------------------------
# Structured output
# ---------------------------------------------------------------------------


def test_report_structure():
    """DataQualityReport must have all required fields."""
    df = _clean_df()
    report = check_quality(df)

    assert isinstance(report, DataQualityReport)
    assert isinstance(report.passed, bool)
    assert isinstance(report.errors, list)
    assert isinstance(report.warnings, list)
    assert report.row_count == 20
    assert isinstance(report.issue_counts, dict)
