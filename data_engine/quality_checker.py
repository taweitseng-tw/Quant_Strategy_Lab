"""Data quality checker — validates normalized OHLCV DataFrames.

Catches broken or suspicious rows before they enter backtest/validation.
Returns a structured DataQualityReport — never mutates the input.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

from data_engine.normalizer import INTERNAL_COLUMNS

# ---------------------------------------------------------------------------
# Structured issue model
# ---------------------------------------------------------------------------

IssueSeverity = Literal["error", "warning"]


@dataclass
class DataQualityIssue:
    """A single structured quality issue — error or warning.

    Keeps backward compatibility: the traditional ``errors`` / ``warnings``
    string lists are still populated.  Consumers that want structured data
    can iterate ``issues`` instead.
    """

    type: str
    """Machine-readable identifier such as ``high_less_than_low``."""

    severity: IssueSeverity
    """``"error"`` blocks pipeline execution; ``"warning"`` does not."""

    message: str
    """Human-readable description (also appended to ``errors`` / ``warnings``)."""

    count: int = 1
    """Number of occurrences (e.g. 15 rows where high < low)."""

    sample_timestamps: list[str] = field(default_factory=list)
    """Up to 3 sample timestamps where the issue was found."""

    sample_values: dict[str, float] = field(default_factory=dict)
    """Optional key values such as ``{"max_gap_minutes": 1440}``."""


# ---------------------------------------------------------------------------
# Report model
# ---------------------------------------------------------------------------


@dataclass
class DataQualityReport:
    """Structured output of a data quality check."""

    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    row_count: int = 0
    issue_counts: dict = field(default_factory=dict)
    issues: list[DataQualityIssue] = field(default_factory=list)


def _add_issue(
    issues: list[DataQualityIssue],
    errors: list[str],
    warnings: list[str],
    counts: dict,
    *,
    issue_type: str,
    severity: IssueSeverity,
    message: str,
    count: int = 1,
    sample_timestamps: list[str] | None = None,
    sample_values: dict[str, float] | None = None,
) -> None:
    """Append a structured *DataQualityIssue* and keep the legacy string lists
    in sync for callers that have not yet migrated to the structured API."""
    issues.append(DataQualityIssue(
        type=issue_type,
        severity=severity,
        message=message,
        count=count,
        sample_timestamps=sample_timestamps or [],
        sample_values=sample_values or {},
    ))
    (errors if severity == "error" else warnings).append(message)
    counts[issue_type] = counts.get(issue_type, 0) + count


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_quality(
    df: pd.DataFrame,
    *,
    expected_freq_minutes: int | None = None,
    outlier_pct_threshold: float | None = None,
    gap_max_minutes: int | None = None,
    session_start: str | None = None,
    session_end: str | None = None,
) -> DataQualityReport:
    """Validate a normalized OHLCV DataFrame.

    Parameters
    ----------
    df : DataFrame
        Must have canonical columns: datetime, open, high, low, close, volume.
    expected_freq_minutes : int or None
        If set, warns when consecutive bar gaps exceed *gap_max_minutes*
        (defaults to 2 × *expected_freq_minutes* when not specified).
    outlier_pct_threshold : float or None
        If set (e.g. 5.0), warns when any bar's OHLC change from the previous
        close exceeds *outlier_pct_threshold* percent.  ``None`` disables.
    gap_max_minutes : int or None
        Max allowed gap in minutes before warning.  Defaults to
        2 × *expected_freq_minutes* when *expected_freq_minutes* is set.

    Returns
    -------
    DataQualityReport
    """
    errors: list[str] = []
    warnings: list[str] = []
    counts: dict[str, int] = {}
    issues: list[DataQualityIssue] = []

    # ── 1. structural checks ────────────────────────────────────────────────
    if not isinstance(df, pd.DataFrame):
        _add_issue(issues, errors, warnings, counts, issue_type="not_dataframe", severity="error", message="Input is not a pandas DataFrame.")
        return DataQualityReport(passed=False, errors=errors, warnings=warnings, issue_counts=counts, issues=issues)

    if df.empty:
        _add_issue(issues, errors, warnings, counts, issue_type="empty_dataframe", severity="error", message="DataFrame is empty.", count=0)
        return DataQualityReport(passed=False, errors=errors, warnings=warnings, row_count=0, issue_counts=counts, issues=issues)

    missing_cols = [c for c in INTERNAL_COLUMNS if c not in df.columns]
    if missing_cols:
        _add_issue(issues, errors, warnings, counts, issue_type="missing_columns", severity="error", message=f"Missing required columns: {missing_cols}.", count=len(df))
        return DataQualityReport(passed=False, errors=errors, warnings=warnings, row_count=len(df), issue_counts=counts, issues=issues)

    n = len(df)

    # ── 2. datetime checks ──────────────────────────────────────────────────
    if not pd.api.types.is_datetime64_any_dtype(df["datetime"]):
        _add_issue(issues, errors, warnings, counts, issue_type="datetime_not_datetime64", severity="error", message="Column 'datetime' is not datetime64 dtype.")
        return DataQualityReport(passed=False, errors=errors, warnings=warnings, row_count=n, issue_counts=counts, issues=issues)

    nat_count = int(df["datetime"].isna().sum())
    if nat_count > 0:
        _add_issue(issues, errors, warnings, counts, issue_type="nat_datetime", severity="error", message=f"Found {nat_count} NaT value(s) in 'datetime' column.", count=nat_count)

    dup_count = int(df["datetime"].duplicated().sum())
    if dup_count > 0:
        _add_issue(issues, errors, warnings, counts, issue_type="duplicate_datetime", severity="error", message=f"Found {dup_count} duplicate datetime(s).", count=dup_count)

    if not df["datetime"].is_monotonic_increasing:
        _add_issue(issues, errors, warnings, counts, issue_type="unsorted_datetime", severity="error", message="Datetime column is not sorted in ascending order.")

    # ── 3. null / non-numeric checks ────────────────────────────────────────
    numeric_ok = True
    for col in ("open", "high", "low", "close", "volume"):
        nulls = int(df[col].isna().sum())
        if nulls > 0:
            _add_issue(issues, errors, warnings, counts, issue_type=f"null_{col}", severity="error", message=f"Column '{col}' has {nulls} null value(s).", count=nulls)
        if not pd.api.types.is_numeric_dtype(df[col]):
            _add_issue(issues, errors, warnings, counts, issue_type=f"non_numeric_{col}", severity="error", message=f"Column '{col}' is not numeric (dtype={df[col].dtype}).")
            numeric_ok = False

    # ── 4. OHLC relationship checks (only when all columns are numeric) ─────
    if numeric_ok:
        hl_violations = int((df["high"] < df["low"]).sum())
        if hl_violations > 0:
            _add_issue(issues, errors, warnings, counts, issue_type="high_less_than_low", severity="error", message=f"Found {hl_violations} row(s) where high < low.", count=hl_violations)

        open_above_high = int((df["open"] > df["high"]).sum())
        if open_above_high > 0:
            _add_issue(issues, errors, warnings, counts, issue_type="open_above_high", severity="error", message=f"Found {open_above_high} row(s) where open > high.", count=open_above_high)

        open_below_low = int((df["open"] < df["low"]).sum())
        if open_below_low > 0:
            _add_issue(issues, errors, warnings, counts, issue_type="open_below_low", severity="error", message=f"Found {open_below_low} row(s) where open < low.", count=open_below_low)

        close_above_high = int((df["close"] > df["high"]).sum())
        if close_above_high > 0:
            _add_issue(issues, errors, warnings, counts, issue_type="close_above_high", severity="error", message=f"Found {close_above_high} row(s) where close > high.", count=close_above_high)

        close_below_low = int((df["close"] < df["low"]).sum())
        if close_below_low > 0:
            _add_issue(issues, errors, warnings, counts, issue_type="close_below_low", severity="error", message=f"Found {close_below_low} row(s) where close < low.", count=close_below_low)

        # ── 5. negative volume ──────────────────────────────────────────────
        neg_vol = int((df["volume"] < 0).sum())
        if neg_vol > 0:
            _add_issue(issues, errors, warnings, counts, issue_type="negative_volume", severity="error", message=f"Found {neg_vol} row(s) with negative volume.", count=neg_vol)

    # ── 6. time gap detection (warning only) ────────────────────────────────
    if expected_freq_minutes is not None and len(df) > 1:
        gap_limit = gap_max_minutes or (expected_freq_minutes * 2)
        deltas = df["datetime"].diff().dropna()
        gap_mask = deltas > pd.Timedelta(minutes=gap_limit)

        # ── 6a. session-aware gap filtering ─────────────────────────────────
        session_break_count = 0
        if session_start and session_end and gap_mask.any():
            session_end_t = pd.Timestamp(session_end).time()
            session_start_t = pd.Timestamp(session_start).time()
            for pos in range(len(gap_mask)):
                if not gap_mask.iloc[pos]:
                    continue
                prev_time = df["datetime"].iloc[pos].time()
                next_time = df["datetime"].iloc[pos + 1].time()
                if prev_time >= session_end_t or next_time <= session_start_t:
                    gap_mask.iloc[pos] = False
                    session_break_count += 1

        gap_count = int(gap_mask.sum())
        if gap_count > 0:
            max_gap = deltas[gap_mask].max()
            max_gap_min = max_gap.total_seconds() / 60
            warning = (
                f"Found {gap_count} time gap(s) > {gap_limit} min "
                f"(expected freq={expected_freq_minutes} min, max gap={max_gap})."
            )
            gap_samples: list[str] = []
            for idx in deltas[gap_mask].nlargest(3).index:
                current_pos = deltas.index.get_loc(idx) + 1
                previous_dt = df["datetime"].iloc[current_pos - 1]
                current_dt = df["datetime"].iloc[current_pos]
                gap_samples.append(
                    f"{previous_dt:%Y-%m-%d %H:%M} -> {current_dt:%Y-%m-%d %H:%M}"
                )
            _add_issue(issues, errors, warnings, counts, issue_type="time_gaps", severity="warning", message=warning, count=gap_count, sample_timestamps=gap_samples, sample_values={"max_gap_minutes": max_gap_min, "gap_limit_minutes": float(gap_limit)})
        if session_break_count > 0:
            _add_issue(issues, errors, warnings, counts, issue_type="session_break_gaps", severity="warning", message=f"{session_break_count} expected session break(s) not counted as gaps.", count=session_break_count)

    # ── 7. outlier / large-jump detection (warning only) ────────────────────
    if outlier_pct_threshold is not None and len(df) > 1:
        pct_chg = df["close"].pct_change().abs() * 100
        outlier_mask = pct_chg > outlier_pct_threshold
        outlier_count = int(outlier_mask.sum())
        if outlier_count > 0:
            max_pct = float(pct_chg[outlier_mask].max())
            jump_samples: list[str] = []
            for idx in pct_chg[outlier_mask].nlargest(3).index:
                current_pos = pct_chg.index.get_loc(idx)
                dt_val = df["datetime"].iloc[current_pos]
                pct_val = float(pct_chg.iloc[current_pos])
                jump_samples.append(f"{dt_val:%Y-%m-%d %H:%M} ({pct_val:.1f}%)")
            _add_issue(issues, errors, warnings, counts, issue_type="large_jumps", severity="warning", message=f"Found {outlier_count} bar(s) with close change > {outlier_pct_threshold}% (max={max_pct:.2f}%).", count=outlier_count, sample_timestamps=jump_samples, sample_values={"max_pct": max_pct, "threshold_pct": outlier_pct_threshold})

    passed = len(errors) == 0
    return DataQualityReport(
        passed=passed,
        errors=errors,
        warnings=warnings,
        row_count=n,
        issue_counts=counts,
        issues=issues,
    )
