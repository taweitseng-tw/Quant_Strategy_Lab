"""Data quality checker — validates normalized OHLCV DataFrames.

Catches broken or suspicious rows before they enter backtest/validation.
Returns a structured DataQualityReport — never mutates the input.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from data_engine.normalizer import INTERNAL_COLUMNS


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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_quality(
    df: pd.DataFrame,
    *,
    expected_freq_minutes: int | None = None,
    outlier_pct_threshold: float | None = None,
    gap_max_minutes: int | None = None,
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

    # ── 1. structural checks ────────────────────────────────────────────────
    if not isinstance(df, pd.DataFrame):
        errors.append("Input is not a pandas DataFrame.")
        return DataQualityReport(passed=False, errors=errors, warnings=warnings)

    if df.empty:
        errors.append("DataFrame is empty.")
        return DataQualityReport(passed=False, errors=errors, warnings=warnings, row_count=0)

    missing_cols = [c for c in INTERNAL_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}.")
        return DataQualityReport(passed=False, errors=errors, warnings=warnings, row_count=len(df))

    n = len(df)

    # ── 2. datetime checks ──────────────────────────────────────────────────
    if not pd.api.types.is_datetime64_any_dtype(df["datetime"]):
        errors.append("Column 'datetime' is not datetime64 dtype.")
        return DataQualityReport(passed=False, errors=errors, warnings=warnings, row_count=n)

    nat_count = int(df["datetime"].isna().sum())
    if nat_count > 0:
        errors.append(f"Found {nat_count} NaT value(s) in 'datetime' column.")
        counts["nat_datetime"] = nat_count
        # Continue checking — NaT rows don't prevent OHLCV checks.

    dup_count = int(df["datetime"].duplicated().sum())
    if dup_count > 0:
        errors.append(f"Found {dup_count} duplicate datetime(s).")
        counts["duplicate_datetime"] = dup_count

    if not df["datetime"].is_monotonic_increasing:
        errors.append("Datetime column is not sorted in ascending order.")
        counts["unsorted_datetime"] = 1

    # ── 3. null / non-numeric checks ────────────────────────────────────────
    numeric_ok = True
    for col in ("open", "high", "low", "close", "volume"):
        nulls = int(df[col].isna().sum())
        if nulls > 0:
            errors.append(f"Column '{col}' has {nulls} null value(s).")
            counts[f"null_{col}"] = nulls
        if not pd.api.types.is_numeric_dtype(df[col]):
            errors.append(f"Column '{col}' is not numeric (dtype={df[col].dtype}).")
            counts[f"non_numeric_{col}"] = 1
            numeric_ok = False

    # ── 4. OHLC relationship checks (only when all columns are numeric) ─────
    if numeric_ok:
        hl_violations = int((df["high"] < df["low"]).sum())
        if hl_violations > 0:
            errors.append(f"Found {hl_violations} row(s) where high < low.")
            counts["high_less_than_low"] = hl_violations

        open_above_high = int((df["open"] > df["high"]).sum())
        if open_above_high > 0:
            errors.append(f"Found {open_above_high} row(s) where open > high.")
            counts["open_above_high"] = open_above_high

        open_below_low = int((df["open"] < df["low"]).sum())
        if open_below_low > 0:
            errors.append(f"Found {open_below_low} row(s) where open < low.")
            counts["open_below_low"] = open_below_low

        close_above_high = int((df["close"] > df["high"]).sum())
        if close_above_high > 0:
            errors.append(f"Found {close_above_high} row(s) where close > high.")
            counts["close_above_high"] = close_above_high

        close_below_low = int((df["close"] < df["low"]).sum())
        if close_below_low > 0:
            errors.append(f"Found {close_below_low} row(s) where close < low.")
            counts["close_below_low"] = close_below_low

        # ── 5. negative volume ──────────────────────────────────────────────
        neg_vol = int((df["volume"] < 0).sum())
        if neg_vol > 0:
            errors.append(f"Found {neg_vol} row(s) with negative volume.")
            counts["negative_volume"] = neg_vol

    # ── 6. time gap detection (warning only) ────────────────────────────────
    if expected_freq_minutes is not None and len(df) > 1:
        gap_limit = gap_max_minutes or (expected_freq_minutes * 2)
        deltas = df["datetime"].diff().dropna()
        gap_mask = deltas > pd.Timedelta(minutes=gap_limit)
        gap_count = int(gap_mask.sum())
        if gap_count > 0:
            max_gap = deltas[gap_mask].max()
            warnings.append(
                f"Found {gap_count} time gap(s) > {gap_limit} min "
                f"(expected freq={expected_freq_minutes} min, max gap={max_gap})."
            )
            counts["time_gaps"] = gap_count

    # ── 7. outlier / large-jump detection (warning only) ────────────────────
    if outlier_pct_threshold is not None and len(df) > 1:
        pct_chg = df["close"].pct_change().abs() * 100
        outlier_mask = pct_chg > outlier_pct_threshold
        outlier_count = int(outlier_mask.sum())
        if outlier_count > 0:
            max_pct = float(pct_chg[outlier_mask].max())
            warnings.append(
                f"Found {outlier_count} bar(s) with close change > "
                f"{outlier_pct_threshold}% (max={max_pct:.2f}%)."
            )
            counts["large_jumps"] = outlier_count

    passed = len(errors) == 0
    return DataQualityReport(
        passed=passed,
        errors=errors,
        warnings=warnings,
        row_count=n,
        issue_counts=counts,
    )
