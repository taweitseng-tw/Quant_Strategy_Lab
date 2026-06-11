"""Schema normalizer — maps source columns to the internal OHLCV schema.

Internal canonical columns: datetime, open, high, low, close, volume
"""

from __future__ import annotations

import pandas as pd


# Canonical output column order.
INTERNAL_COLUMNS = ("datetime", "open", "high", "low", "close", "volume")

# Column-name aliases (lowercase → canonical).  Sources like MultiCharts and
# TradeStation often use PascalCase or different spellings.
_COLUMN_ALIASES: dict[str, str] = {
    # datetime — single-column
    "datetime": "datetime",
    "date": "datetime",
    "timestamp": "datetime",
    "time": "datetime",
    # price
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "last": "close",      # TradeStation sometimes uses "Last" for close
    "settle": "close",    # futures settlement price
    # volume
    "volume": "volume",
    "vol": "volume",
    "totalvolume": "volume",
    "upvol": "volume",    # best-effort: take any volume column
    "downvol": "volume",
}


# Columns that indicate a two-column datetime source (Date + Time).
_DATE_COLUMN_ALIASES = frozenset({"date", "timestamp"})
_TIME_COLUMN_ALIASES = frozenset({"time", "timestamp"})


class NormalizerError(ValueError):
    """Raised when source data cannot be normalized to the internal schema."""


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize *df* to the internal OHLCV schema.

    1. Map source column names to canonical names via aliases.
    2. Combine separate Date and Time columns into a single datetime column.
    3. Validate that all required columns are present.
    4. Reject rows with unparseable datetimes (no silent drop).
    5. Sort by datetime and check for duplicates.

    Returns a new DataFrame with columns ``datetime, open, high, low, close, volume``.

    Raises :class:`NormalizerError` on missing columns, unparseable datetimes,
    or duplicate timestamps.
    """
    df = df.copy()
    original_cols = [c.lower().strip() for c in df.columns]

    # --- 1. Detect and combine Date + Time -------------------------------------------------
    if _has_two_column_datetime(original_cols):
        date_col, time_col = _find_date_time_pair(original_cols, list(df.columns))
        df["datetime"] = pd.to_datetime(
            df[date_col].astype(str) + " " + df[time_col].astype(str),
            errors="coerce",
        )
        df.drop(columns=[date_col, time_col], inplace=True, errors="ignore")
    else:
        # Single datetime column — find and parse it.
        dt_col = _find_single_datetime_col(original_cols, list(df.columns))
        if dt_col is None:
            raise NormalizerError(
                "No datetime column found. "
                "Expected one of: datetime, date, time, timestamp."
            )
        df["datetime"] = pd.to_datetime(df[dt_col], errors="coerce")
        if original_cols[list(df.columns).index(dt_col)] not in _COLUMN_ALIASES:
            # Mapped a non-alias column — keep the original as well.
            pass
        # Drop the original datetime column if its name differs from "datetime".
        if dt_col.lower() != "datetime":
            df.drop(columns=[dt_col], inplace=True)

    # --- 2. Map remaining columns ----------------------------------------------------------
    rename_map: dict[str, str] = {}
    for col in list(df.columns):
        key = col.lower().strip()
        if key in _COLUMN_ALIASES:
            canonical = _COLUMN_ALIASES[key]
            if col != canonical:
                rename_map[col] = canonical

    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    # --- 3. Validate required columns ------------------------------------------------------
    missing = [c for c in INTERNAL_COLUMNS if c not in df.columns]
    if missing:
        raise NormalizerError(
            f"Required columns missing after normalization: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    # --- 4. Keep only canonical columns in order -------------------------------------------
    df = df[list(INTERNAL_COLUMNS)]

    # --- 5. Reject rows with unparseable datetimes -----------------------------------------
    nat_mask = df["datetime"].isna()
    if nat_mask.any():
        bad_count = nat_mask.sum()
        bad_indices = df.index[nat_mask].tolist()
        raise NormalizerError(
            f"{bad_count} row(s) contain unparseable datetimes "
            f"at indices {bad_indices}.  All datetime values must be valid."
        )

    # --- 5A. Validate OHLCV numeric/finite/bounds ------------------------------------------
    for col in ("open", "high", "low", "close", "volume"):
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise NormalizerError(f"Column '{col}' must be numeric.")

        # Check for NaN or infinite values
        invalid_mask = df[col].isna() | (df[col] == float("inf")) | (df[col] == float("-inf"))
        if invalid_mask.any():
            bad_count = invalid_mask.sum()
            bad_indices = df.index[invalid_mask].tolist()
            raise NormalizerError(
                f"{bad_count} row(s) contain NaN or infinite values in column '{col}' "
                f"at indices {bad_indices}."
            )

    # Check price bounds (positive)
    for col in ("open", "high", "low", "close"):
        invalid_mask = df[col] <= 0
        if invalid_mask.any():
            bad_count = invalid_mask.sum()
            bad_indices = df.index[invalid_mask].tolist()
            raise NormalizerError(
                f"{bad_count} row(s) contain non-positive prices (<= 0) in column '{col}' "
                f"at indices {bad_indices}."
            )

    # Check volume bounds (non-negative)
    invalid_mask = df["volume"] < 0
    if invalid_mask.any():
        bad_count = invalid_mask.sum()
        bad_indices = df.index[invalid_mask].tolist()
        raise NormalizerError(
            f"{bad_count} row(s) contain negative volume in column 'volume' "
            f"at indices {bad_indices}."
        )

    # Check OHLC consistency: high >= open, high >= close, high >= low, low <= open, low <= close
    invalid_high_open = df["high"] < df["open"]
    invalid_high_close = df["high"] < df["close"]
    invalid_high_low = df["high"] < df["low"]
    invalid_low_open = df["low"] > df["open"]
    invalid_low_close = df["low"] > df["close"]

    any_invalid = (
        invalid_high_open | invalid_high_close | invalid_high_low |
        invalid_low_open | invalid_low_close
    )
    if any_invalid.any():
        bad_count = any_invalid.sum()
        bad_indices = df.index[any_invalid].tolist()
        first_bad = bad_indices[0]
        row_vals = df.loc[first_bad]
        raise NormalizerError(
            f"{bad_count} row(s) contain invalid OHLC relationships "
            f"at indices {bad_indices}. First violation values at index {first_bad}: "
            f"O={row_vals['open']}, H={row_vals['high']}, L={row_vals['low']}, C={row_vals['close']}."
        )

    # --- 6. Sort and check duplicates ------------------------------------------------------
    import warnings
    if not df["datetime"].is_monotonic_increasing:
        warnings.warn(
            "Source datetime series is not monotonic increasing (out-of-order). "
            "Data will be automatically sorted by datetime.",
            UserWarning,
            stacklevel=2
        )

    df.sort_values("datetime", inplace=True)
    df.reset_index(drop=True, inplace=True)

    if df["datetime"].duplicated().any():
        dupe_series = df["datetime"][df["datetime"].duplicated()]
        dupe_count = len(dupe_series)
        unique_dupes = dupe_series.unique()
        sample_dupes = [str(ts) for ts in unique_dupes[:5]]
        raise NormalizerError(
            f"Found {dupe_count} duplicate datetime rows. "
            f"Duplicate timestamps include: {', '.join(sample_dupes)}"
            f"{'...' if len(unique_dupes) > 5 else ''}. "
            "Source data must have unique timestamps per bar."
        )

    return df


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


def _has_two_column_datetime(cols_lower: list[str]) -> bool:
    """Return True if the source appears to use separate Date + Time columns."""
    has_date = any(c in _DATE_COLUMN_ALIASES for c in cols_lower)
    has_time = any(c in _TIME_COLUMN_ALIASES and c != "datetime" for c in cols_lower)
    return has_date and has_time


def _find_date_time_pair(
    cols_lower: list[str], cols_original: list[str],
) -> tuple[str, str]:
    """Return the (date_col, time_col) pair from original column names."""
    date_col = None
    time_col = None
    for lower, orig in zip(cols_lower, cols_original):
        if lower in _DATE_COLUMN_ALIASES and date_col is None:
            date_col = orig
        elif lower in _TIME_COLUMN_ALIASES and time_col is None and lower != "datetime":
            time_col = orig
    if date_col is None or time_col is None:
        raise NormalizerError("Could not determine Date / Time column pair.")
    return date_col, time_col


def _find_single_datetime_col(
    cols_lower: list[str], cols_original: list[str],
) -> str | None:
    """Return the best single datetime column, or None."""
    for lower, orig in zip(cols_lower, cols_original):
        if lower in ("datetime", "date", "timestamp"):
            return orig
    return None
