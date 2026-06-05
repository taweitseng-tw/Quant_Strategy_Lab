"""Indicator calculations for strategy conditions.

All indicators use rolling, backward-looking windows — no future leak.
"""

from __future__ import annotations

import pandas as pd


# ---------------------------------------------------------------------------
# SMA
# ---------------------------------------------------------------------------


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average over *period* bars.

    Uses ``rolling(window=period).mean()`` which at index *i* only consumes
    bars ``i - period + 1`` through ``i`` — no future data is used.

    The first ``period - 1`` values are NaN (insufficient history).
    """
    return series.rolling(window=period, min_periods=period).mean()


# ---------------------------------------------------------------------------
# RSI — Relative Strength Index
# ---------------------------------------------------------------------------


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's RSI over *period* bars.

    Uses a simple moving average of gains and losses (not Wilder's smoothing).
    At bar *i*, only bars ≤ *i* are used — no future leak.

    Returns a Series in [0, 100]; the first *period* values are NaN.
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))
    return 100.0 - (100.0 / (1.0 + rs))


# ---------------------------------------------------------------------------
# MACD — Moving Average Convergence Divergence
# ---------------------------------------------------------------------------


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """Compute MACD line, signal line, and histogram.

    - **macd_line** = EMA(fast) − EMA(slow)
    - **macd_signal** = EMA(macd_line, signal)
    - **macd_histogram** = macd_line − macd_signal

    All EMAs use ``span`` (not ``halflife``) and are backward-looking.

    Returns a DataFrame with columns ``macd_line``, ``macd_signal``,
    ``macd_histogram``.
    """
    ema_fast = series.ewm(span=fast, min_periods=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, min_periods=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    macd_signal_line = macd_line.ewm(span=signal, min_periods=signal, adjust=False).mean()
    macd_histogram = macd_line - macd_signal_line

    return pd.DataFrame({
        "macd_line": macd_line,
        "macd_signal": macd_signal_line,
        "macd_histogram": macd_histogram,
    })


# ---------------------------------------------------------------------------
# ATR — Average True Range
# ---------------------------------------------------------------------------


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range over *period* bars.

    True Range = max(high−low, |high−prev_close|, |low−prev_close|).
    Uses rolling mean — backward-looking only.

    The first *period* values are NaN.
    """
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    return true_range.rolling(window=period, min_periods=period).mean()


# ---------------------------------------------------------------------------
# VOLUME SMA
# ---------------------------------------------------------------------------


def volume_sma(series: pd.Series, period: int = 20) -> pd.Series:
    """Simple Moving Average of Volume over *period* bars.

    Uses ``rolling(window=period).mean()`` — backward-looking only.
    """
    return series.rolling(window=period, min_periods=period).mean()
