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


def test_structured_issues_populated():
    """Quality check must produce structured DataQualityIssue entries."""
    df = _clean_df(20)
    report = check_quality(df, expected_freq_minutes=1, outlier_pct_threshold=5.0)
    # Clean data: no errors or warnings.
    assert len(report.issues) == 0


def test_structured_issues_on_bad_ohlc():
    """Bad OHLC data must produce structured issues with type and severity."""
    df = _clean_df(20)
    # Force a high < low violation.
    df.loc[5, "high"] = df.loc[5, "low"] - 1
    report = check_quality(df, expected_freq_minutes=1)
    issues_by_type = {i.type: i for i in report.issues}
    assert "high_less_than_low" in issues_by_type
    issue = issues_by_type["high_less_than_low"]
    assert issue.severity == "error"
    assert issue.count >= 1


def test_structural_error_populates_issue_counts():
    """Early structural failures must keep issue_counts consistent with issues."""
    report = check_quality("not a dataframe")
    assert not report.passed
    assert report.issue_counts == {"not_dataframe": 1}
    assert report.issues[0].type == "not_dataframe"


def test_structured_issues_on_time_gaps():
    """Time gap warnings must produce structured issues with sample_values."""
    df = _clean_df(20)
    # Insert a gap.
    times = list(df["datetime"])
    times[10] = times[9] + pd.Timedelta(minutes=10)
    df["datetime"] = times
    report = check_quality(df, expected_freq_minutes=1, outlier_pct_threshold=5.0)
    issues_by_type = {i.type: i for i in report.issues}
    assert "time_gaps" in issues_by_type
    issue = issues_by_type["time_gaps"]
    assert issue.severity == "warning"
    assert issue.sample_values.get("max_gap_minutes", 0) >= 8
    assert issue.sample_values.get("gap_limit_minutes", 0) == 2
    assert issue.sample_timestamps


def test_structured_issues_backward_compatible_strings():
    """Structured issues must keep errors/warnings lists consistent."""
    df = _clean_df(20)
    df.loc[5, "high"] = df.loc[5, "low"] - 1
    report = check_quality(df, expected_freq_minutes=1)
    for issue in report.issues:
        if issue.severity == "error":
            assert issue.message in report.errors
        else:
            assert issue.message in report.warnings


def test_session_aware_import_with_data_service(tmp_path):
    """DataService.import_file must pass session parameters through to
    quality check and suppress session-break gaps."""
    from app.services.data_service import DataService

    # Create a CSV with an overnight gap.
    import pandas as pd
    csv_path = tmp_path / "session_test.csv"
    times = [
        pd.Timestamp("2024-01-02 13:29"),
        pd.Timestamp("2024-01-02 13:30"),
        pd.Timestamp("2024-01-03 08:30"),
        pd.Timestamp("2024-01-03 08:31"),
    ]
    pd.DataFrame({
        "Date": [t.strftime("%Y/%m/%d") for t in times],
        "Time": [t.strftime("%H:%M:%S") for t in times],
        "Open": 100.0, "High": 101.0, "Low": 99.0,
        "Close": 100.5, "TotalVolume": 1000,
    }).to_csv(csv_path, index=False)

    service = DataService(project_path=tmp_path)

    # Without session params — overnight gap is warned.
    _, _, report_no_session = service.import_file(csv_path, symbol="TEST", timeframe="1min")
    no_session_issues = {i.type for i in report_no_session.issues}
    assert "time_gaps" in no_session_issues or report_no_session.warnings, (
        "Expected time_gap warning without session params"
    )

    # With session params — overnight gap is suppressed.
    _, _, report_with_session = service.import_file(
        csv_path, symbol="TEST", timeframe="1min",
        session_start="08:30", session_end="13:30",
    )
    with_session_issues = {i.type for i in report_with_session.issues}
    assert "session_break_gaps" in with_session_issues or "time_gaps" not in with_session_issues, (
        f"Expected session_break_gaps or suppressed time_gaps, got {with_session_issues}"
    )


# ---------------------------------------------------------------------------
# Session-aware gap detection
# ---------------------------------------------------------------------------


def test_session_aware_gap_suppresses_intraday_gap():
    """A gap during a known intraday session (within 08:30-13:30) is still warned."""
    times = pd.date_range("2024-01-02 08:30", periods=5, freq="1min")
    times = times.insert(3, times[2] + pd.Timedelta(minutes=5))  # 5-min intraday gap
    df = pd.DataFrame({
        "datetime": times[:6],
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000,
    })
    report = check_quality(
        df, expected_freq_minutes=1, gap_max_minutes=2,
        session_start="08:30", session_end="13:30",
    )
    # The 5-min gap is within the session and should be warned.
    assert report.warnings, "Expected a gap warning for intraday gap"
    assert "time gap" in report.warnings[0].lower()


def test_session_aware_session_break_suppressed():
    """A gap that crosses the session boundary (overnight) should not be warned."""
    times = [
        pd.Timestamp("2024-01-02 13:29"),
        pd.Timestamp("2024-01-02 13:30"),
        pd.Timestamp("2024-01-03 08:30"),  # overnight gap to next session start
        pd.Timestamp("2024-01-03 08:31"),
    ]
    df = pd.DataFrame({
        "datetime": times,
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000,
    })
    report = check_quality(
        df, expected_freq_minutes=1, gap_max_minutes=2,
        session_start="08:30", session_end="13:30",
    )
    # The overnight gap bridges session end → next session start and should
    # be suppressed.  There may still be warnings about the jump itself.
    assert "session_break_gaps" in report.issue_counts, (
        f"Expected session_break_gaps in issue_counts, got {report.issue_counts}"
    )
    # There should be no time_gap warning remaining.
    assert "time_gaps" not in report.issue_counts or report.issue_counts["time_gaps"] == 0, (
        f"Expected no time_gaps with session-aware, got {report.issue_counts}"
    )


def test_session_aware_weekend_gap_suppressed():
    """A weekend gap should not be warned when session boundaries are provided."""
    times = [
        pd.Timestamp("2024-01-05 13:30"),  # Friday close
        pd.Timestamp("2024-01-08 08:30"),  # Monday open
        pd.Timestamp("2024-01-08 08:31"),
    ]
    df = pd.DataFrame({
        "datetime": times,
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000,
    })
    report = check_quality(
        df, expected_freq_minutes=1, gap_max_minutes=2,
        session_start="08:30", session_end="13:30",
    )
    assert "session_break_gaps" in report.issue_counts, (
        f"Expected session_break_gaps, got {report.issue_counts}"
    )
    assert "time_gaps" not in report.issue_counts or report.issue_counts["time_gaps"] == 0, (
        f"Expected no time_gaps, got {report.issue_counts}"
    )


def test_session_aware_no_session_no_change():
    """Without session_start/session_end, behavior is unchanged (backward compat)."""
    times = [
        pd.Timestamp("2024-01-02 13:29"),
        pd.Timestamp("2024-01-02 13:30"),
        pd.Timestamp("2024-01-03 08:30"),
    ]
    df = pd.DataFrame({
        "datetime": times,
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000,
    })
    report_no_session = check_quality(df, expected_freq_minutes=1, gap_max_minutes=2)
    # Without session-aware, the overnight gap should be warned.
    assert "time_gaps" in report_no_session.issue_counts, (
        f"Expected time_gaps without session-aware, got {report_no_session.issue_counts}"
    )


def test_session_aware_blank_session_values_are_ignored():
    """Blank session strings should behave like no session filter, not raise."""
    times = [
        pd.Timestamp("2024-01-02 13:29"),
        pd.Timestamp("2024-01-02 13:30"),
        pd.Timestamp("2024-01-03 08:30"),
    ]
    df = pd.DataFrame({
        "datetime": times,
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000,
    })
    report = check_quality(
        df,
        expected_freq_minutes=1,
        gap_max_minutes=2,
        session_start="",
        session_end="",
    )
    assert "time_gaps" in report.issue_counts
