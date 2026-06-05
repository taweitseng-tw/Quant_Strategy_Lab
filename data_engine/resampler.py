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

    # --- identity shortcut: same period → no-op -----------------------------
    if target_minutes == source_minutes:
        out = df[list(INTERNAL_COLUMNS)].copy()
        # When source == target each bar is immediately available.
        out["available_at"] = out["datetime"]
        return out

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
        dupes = work["datetime"].duplicated().sum()
        raise ResamplerError(
            f"Found {dupes} duplicate datetime rows. "
            "Resolve duplicates before resampling."
        )

    # --- numeric validation ---
    for col in ("open", "high", "low", "close", "volume"):
        if not pd.api.types.is_numeric_dtype(work[col]):
            raise ResamplerError(
                f"Column '{col}' must be numeric, got {work[col].dtype}."
            )

    # ------------------------------------------------------------------
    # 3. Sort by datetime (robustness — input may be unsorted)
    # ------------------------------------------------------------------
    work.sort_values("datetime", inplace=True)
    work.reset_index(drop=True, inplace=True)

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
        )
        .reset_index()
    )

    # Drop empty buckets that Grouper may create at the head (before data starts).
    result.dropna(subset=["open"], inplace=True)
    result.reset_index(drop=True, inplace=True)

    # Canonical output order — available_at is the non-leaking signal gate.
    _RESULT_COLUMNS = list(INTERNAL_COLUMNS) + ["available_at"]
    return result[_RESULT_COLUMNS]
