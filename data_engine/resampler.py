"""OHLCV resampler — converts higher-frequency bars to lower-frequency bars.

Two-timestamp contract
----------------------
Every output bar carries **two** timestamps to prevent future leak:

    ``datetime``
        The **start** of the candle window — intended for chart display.

    ``available_at``
        The timestamp of the **last** constituent bar.  Downstream backtest
        and signal code MUST gate on ``available_at``, not ``datetime``,
        when consuming OHLCV values from a resampled bar.  A signal that
        fires at ``datetime`` should not read the bar's ``close`` (which
        isn't known until ``available_at``).

Example — 1‑min → 5‑min
------------------------
Bars at :30, :31, :32, :33, :34 produce a single output row:

    datetime     = :30  (chart label — candle start)
    available_at = :34  (when close/high/low/volume became fully known)

OHLCV rules (per PRD §8.1.4)
-----------------------------
- open   = open of the first bar in the group
- high   = max of all highs in the group
- low    = min of all lows in the group
- close  = close of the last bar in the group
- volume = sum of all volumes in the group
"""

from __future__ import annotations

import pandas as pd

from data_engine.normalizer import INTERNAL_COLUMNS, NormalizerError


class ResamplerError(ValueError):
    """Raised when input data cannot be resampled."""


def resample(
    df: pd.DataFrame,
    source_minutes: int = 1,
    target_minutes: int = 5,
) -> pd.DataFrame:
    """Resample OHLCV bars from *source_minutes* to *target_minutes*.

    Parameters
    ----------
    df : DataFrame
        Must have the canonical columns: ``datetime, open, high, low, close, volume``.
    source_minutes : int
        Bar period of the input data in minutes (default 1).
    target_minutes : int
        Desired bar period in minutes (default 5).  Must be >= *source_minutes*
        and a multiple of it.

    Returns
    -------
    DataFrame
        Resampled bars with columns ``datetime, open, high, low, close, volume,
        available_at``.  ``datetime`` is the candle start; ``available_at`` is
        the last constituent bar timestamp — the non-leaking signal gate.

    Raises
    ------
    ResamplerError
        If columns are missing, datetimes are duplicated, *target_minutes*
        is not an integer multiple of *source_minutes*, or the input is empty.
    """
    # ------------------------------------------------------------------
    # 1. Validate parameters
    # ------------------------------------------------------------------
    if target_minutes < source_minutes:
        raise ResamplerError(
            f"target_minutes ({target_minutes}) must be >= source_minutes ({source_minutes})."
        )
    if target_minutes % source_minutes != 0:
        raise ResamplerError(
            f"target_minutes ({target_minutes}) must be a multiple of "
            f"source_minutes ({source_minutes})."
        )

    # ------------------------------------------------------------------
    # 2. Validate input DataFrame
    # ------------------------------------------------------------------
    if df.empty:
        raise ResamplerError("Input DataFrame is empty — nothing to resample.")

    missing = [c for c in INTERNAL_COLUMNS if c not in df.columns]
    if missing:
        raise ResamplerError(
            f"Required columns missing: {missing}. "
            f"Expected canonical columns: {list(INTERNAL_COLUMNS)}."
        )

    # Work on a copy.
    work = df[list(INTERNAL_COLUMNS)].copy()

    # --- datetime validation ---
    if not pd.api.types.is_datetime64_any_dtype(work["datetime"]):
        raise ResamplerError(
            "The 'datetime' column must be datetime64 — run the normalizer first."
        )

    if work["datetime"].isna().any():
        raise ResamplerError("Datetime column contains NaT values.")

    if work["datetime"].duplicated().any():
        dupe_series = work["datetime"][work["datetime"].duplicated()]
        dupe_count = len(dupe_series)
        unique_dupes = dupe_series.unique()
        sample_dupes = [str(ts) for ts in unique_dupes[:5]]
        raise ResamplerError(
            f"Found {dupe_count} duplicate datetime rows. "
            f"Duplicate timestamps include: {', '.join(sample_dupes)}"
            f"{'...' if len(unique_dupes) > 5 else ''}. "
            "Resolve duplicates before resampling."
        )

    # --- numeric validation ---
    for col in ("open", "high", "low", "close", "volume"):
        if not pd.api.types.is_numeric_dtype(work[col]):
            raise ResamplerError(
                f"Column '{col}' must be numeric, got {work[col].dtype}."
            )
        invalid_mask = (
            work[col].isna()
            | (work[col] == float("inf"))
            | (work[col] == float("-inf"))
        )
        if invalid_mask.any():
            bad_count = invalid_mask.sum()
            raise ResamplerError(
                f"{bad_count} row(s) contain NaN or infinite values in column '{col}'."
            )

    for col in ("open", "high", "low", "close"):
        invalid_mask = work[col] <= 0
        if invalid_mask.any():
            bad_count = invalid_mask.sum()
            raise ResamplerError(
                f"{bad_count} row(s) contain non-positive prices (<= 0) in column '{col}'."
            )

    invalid_mask = work["volume"] < 0
    if invalid_mask.any():
        bad_count = invalid_mask.sum()
        raise ResamplerError(
            f"{bad_count} row(s) contain negative volume in column 'volume'."
        )

    invalid_high_open = work["high"] < work["open"]
    invalid_high_close = work["high"] < work["close"]
    invalid_high_low = work["high"] < work["low"]
    invalid_low_open = work["low"] > work["open"]
    invalid_low_close = work["low"] > work["close"]

    any_invalid = (
        invalid_high_open | invalid_high_close | invalid_high_low |
        invalid_low_open | invalid_low_close
    )
    if any_invalid.any():
        bad_count = any_invalid.sum()
        raise ResamplerError(
            f"{bad_count} row(s) contain invalid OHLC relationships."
        )

    # ------------------------------------------------------------------
    # 3. Sort by datetime (robustness — input may be unsorted)
    # ------------------------------------------------------------------
    work.sort_values("datetime", inplace=True)
    work.reset_index(drop=True, inplace=True)

    # --- identity shortcut: same period no-op after validation --------------
    if target_minutes == source_minutes:
        out = work[list(INTERNAL_COLUMNS)].copy()
        # When source == target each bar is immediately available.
        out["available_at"] = out["datetime"]
        return out

    # Preserve a copy of datetime as a column so we can aggregate .last()
    # after set_index consumes the original column.
    work["_dt"] = work["datetime"]

    # ------------------------------------------------------------------
    # 4. Group into target_minutes buckets via pd.Grouper
    # ------------------------------------------------------------------
    # closed="left"  → bucket covers [t, t + target_minutes)
    # label="left"   → output bar labelled with the start of the window
    # This convention means e.g. 08:30–08:34 bars produce a bar at 08:30.
    result = (
        work.set_index("datetime")
        .groupby(
            pd.Grouper(
                freq=f"{target_minutes}min",
                closed="left",
                label="left",
            )
        )
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
            available_at=("_dt", "last"),  # _dt is the preserved datetime copy
            constituent_count=("_dt", "count"),
        )
        .reset_index()
    )

    # Drop empty buckets that Grouper may create at the head (before data starts).
    result.dropna(subset=["open"], inplace=True)
    result.reset_index(drop=True, inplace=True)

    expected_count = target_minutes // source_minutes
    if len(result) >= 3:
        non_boundary = result.iloc[1:-1]
        incomplete_mask = non_boundary["constituent_count"] < expected_count
        if incomplete_mask.any():
            incomplete_bars = non_boundary[incomplete_mask]
            incomplete_details = [
                f"{row['datetime'].strftime('%Y-%m-%d %H:%M')} "
                f"(has {int(row['constituent_count'])}/{expected_count} bars)"
                for _, row in incomplete_bars.head(5).iterrows()
            ]
            import warnings
            warnings.warn(
                f"Found {len(incomplete_bars)} non-boundary resampled bars "
                "with incomplete constituent counts. "
                f"Expected {expected_count} bars. Incomplete bars include: "
                f"{', '.join(incomplete_details)}"
                f"{'...' if len(incomplete_bars) > 5 else ''}.",
                UserWarning,
                stacklevel=2,
            )

    # Canonical output order — available_at is the non-leaking signal gate.
    _RESULT_COLUMNS = list(INTERNAL_COLUMNS) + ["available_at"]
    return result[_RESULT_COLUMNS]
