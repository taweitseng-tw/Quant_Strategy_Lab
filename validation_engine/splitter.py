"""Chronological dataset splitter — IS / Validation / OOS.

Splits are **non-overlapping** and preserve chronological order.
OOS data must never be used for training or parameter optimisation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from data_engine.normalizer import INTERNAL_COLUMNS


class SplitError(ValueError):
    """Raised when split parameters are invalid."""


@dataclass
class SplitResult:
    """Structured result of a chronological data split.

    Each segment is ``None`` when its ratio is zero (or the segment
    contains no bars).
    """

    train: pd.DataFrame | None = None
    validation: pd.DataFrame | None = None
    oos: pd.DataFrame | None = None

    # Per-segment metadata for reporting.
    train_meta: dict = field(default_factory=dict)
    validation_meta: dict = field(default_factory=dict)
    oos_meta: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def split_by_ratio(
    df: pd.DataFrame,
    train_ratio: float = 0.6,
    validation_ratio: float = 0.2,
    oos_ratio: float = 0.2,
) -> SplitResult:
    """Split *df* into train / validation / OOS by row-count ratios.

    Ratios must sum to 1.0 within floating-point tolerance.
    Segments are contiguous and chronologically ordered (first *train_ratio*
    rows → train, next *validation_ratio* rows → validation, remainder → OOS).

    Parameters
    ----------
    df : DataFrame
        Normalized OHLCV data (must have ``datetime`` column).
    train_ratio : float
    validation_ratio : float
    oos_ratio : float

    Returns
    -------
    SplitResult
    """
    _validate_ratios(train_ratio, validation_ratio, oos_ratio)
    _validate_dataframe(df)

    n = len(df)
    train_n = int(round(n * train_ratio))
    val_n = int(round(n * validation_ratio))
    oos_n = n - train_n - val_n

    train = df.iloc[:train_n].copy() if train_n > 0 else None
    val = df.iloc[train_n:train_n + val_n].copy() if val_n > 0 else None
    oos = df.iloc[train_n + val_n:].copy() if oos_n > 0 else None

    return SplitResult(
        train=train,
        validation=val,
        oos=oos,
        train_meta=_segment_meta(train, "train"),
        validation_meta=_segment_meta(val, "validation"),
        oos_meta=_segment_meta(oos, "oos"),
    )


def split_by_date(
    df: pd.DataFrame,
    train_end: str | pd.Timestamp,
    validation_end: str | pd.Timestamp | None = None,
) -> SplitResult:
    """Split *df* by explicit datetime boundaries.

    - **train**:  ``datetime <= train_end``
    - **validation**: ``train_end < datetime <= validation_end``
    - **oos**:  ``datetime > validation_end`` (or ``datetime > train_end``
      when *validation_end* is ``None``)

    Parameters
    ----------
    df : DataFrame
        Normalized OHLCV data.
    train_end : str or Timestamp
        End of training window (inclusive).
    validation_end : str or Timestamp or None
        End of validation window (inclusive).  When ``None``, no validation
        segment is produced — the remaining data becomes OOS.

    Returns
    -------
    SplitResult
    """
    _validate_dataframe(df)

    te = pd.Timestamp(train_end)
    ve = pd.Timestamp(validation_end) if validation_end is not None else None

    if ve is not None and ve <= te:
        raise SplitError(
            f"validation_end ({validation_end}) must be after "
            f"train_end ({train_end})."
        )

    mask_train = df["datetime"] <= te
    train = df.loc[mask_train].copy() if mask_train.any() else None

    if ve is not None:
        mask_val = (df["datetime"] > te) & (df["datetime"] <= ve)
        val = df.loc[mask_val].copy() if mask_val.any() else None
        mask_oos = df["datetime"] > ve
    else:
        val = None
        mask_oos = df["datetime"] > te

    oos = df.loc[mask_oos].copy() if mask_oos.any() else None

    return SplitResult(
        train=train,
        validation=val,
        oos=oos,
        train_meta=_segment_meta(train, "train"),
        validation_meta=_segment_meta(val, "validation"),
        oos_meta=_segment_meta(oos, "oos"),
    )


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


def _validate_ratios(train: float, val: float, oos: float) -> None:
    total = train + val + oos
    if abs(total - 1.0) > 1e-9:
        raise SplitError(
            f"Ratios must sum to 1.0.  Got train={train}, "
            f"validation={val}, oos={oos} → sum={total}."
        )
    for name, r in (("train", train), ("validation", val), ("oos", oos)):
        if r < 0.0 or r > 1.0:
            raise SplitError(
                f"{name}_ratio must be in [0, 1], got {r}."
            )


def _validate_dataframe(df: pd.DataFrame) -> None:
    if df.empty:
        raise SplitError("Cannot split an empty DataFrame.")
    if "datetime" not in df.columns:
        raise SplitError(
            f"DataFrame must have a 'datetime' column. "
            f"Found columns: {list(df.columns)}."
        )
    if not pd.api.types.is_datetime64_any_dtype(df["datetime"]):
        raise SplitError("The 'datetime' column must be datetime64 — run the normalizer first.")


def _segment_meta(seg: pd.DataFrame | None, name: str) -> dict:
    if seg is None or len(seg) == 0:
        return {"name": name, "row_count": 0, "start": None, "end": None}
    return {
        "name": name,
        "row_count": len(seg),
        "start": str(seg["datetime"].iloc[0]),
        "end": str(seg["datetime"].iloc[-1]),
    }
