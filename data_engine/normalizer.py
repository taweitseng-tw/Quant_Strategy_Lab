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

    # --- 6. Sort and check duplicates ------------------------------------------------------
    df.sort_values("datetime", inplace=True)
    df.reset_index(drop=True, inplace=True)

    if df["datetime"].duplicated().any():
        dupes = df["datetime"].duplicated().sum()
        raise NormalizerError(
            f"Found {dupes} duplicate datetime rows. "
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
