"""Strategy condition evaluator - bar-by-bar signal generation.

Evaluates conditions against pre-computed indicator columns on a normalized
DataFrame.  All lookups are at the current bar index - no future leak.

Supported patterns
------------------
- ``close > SMA(N)`` / ``close < SMA(N)``
- ``RSI(N) > threshold`` / ``RSI(N) < threshold``
- ``MACD line > signal line`` / ``MACD line < signal line``
- ``ATR(N) > threshold`` / ``ATR(N) < threshold``
"""

from __future__ import annotations

import pandas as pd

from core.models.strategy import Condition, StrategyBlock
from typing import Callable

ConditionAccessor = Callable[[int], bool]
BlockAccessor = Callable[[int], bool]


def _col(name: str, params: dict) -> str:
    """Build a canonical indicator column name from indicator + params.

    Appends ``_tf_{N}`` suffix when *params* includes a ``"timeframe"`` key
    (multi-timeframe conditions, Task 049B).
    """
    ind = name.upper()
    tf = params.get("timeframe")

    if ind == "SMA":
        base = f"sma_{params.get('period', '')}"
    elif ind == "RSI":
        base = f"rsi_{params.get('period', 14)}"
    elif ind == "MACD":
        base = "macd_line"  # both macd_line and macd_signal are used
    elif ind == "ATR":
        base = f"atr_{params.get('period', 14)}"
    elif ind == "VOLUME":
        base = "volume"
    elif ind == "VOLUME_SMA":
        base = f"volume_sma_{params.get('period', 20)}"
    else:
        base = f"{name.lower()}_{params.get('period', '')}"

    if tf is not None:
        return f"{base}_tf_{tf}"
    return base


def evaluate_condition(cond: Condition, df: pd.DataFrame, i: int) -> bool:
    """Evaluate a single condition at bar index *i*.

    Returns ``False`` when any referenced indicator value is NaN
    (insufficient warm-up history).
    """
    ind = cond.indicator.upper()
    op = cond.operator

    if ind == "SMA":
        return _eval_sma(cond, df, i, op)
    elif ind == "RSI":
        return _eval_threshold(_col("RSI", cond.params), df, i, op, cond.right)
    elif ind == "MACD":
        return _eval_macd(df, i, op, cond.params)
    elif ind == "ATR":
        return _eval_threshold(_col("ATR", cond.params), df, i, op, cond.right)
    elif ind == "VOLUME":
        return _eval_threshold(_col("VOLUME", cond.params), df, i, op, cond.right)
    elif ind == "VOLUME_SMA":
        return _eval_volume_sma(cond, df, i, op)
    return False


def evaluate_block(block: StrategyBlock, df: pd.DataFrame, i: int) -> bool:
    """Evaluate whether *block* fires at bar index *i*."""
    if not block.conditions:
        return False

    results = [evaluate_condition(c, df, i) for c in block.conditions]
    if block.logic.upper() == "AND":
        return all(results)
    return any(results)  # OR


# ---------------------------------------------------------------------------
# internal evaluators
# ---------------------------------------------------------------------------


def _eval_sma(cond: Condition, df: pd.DataFrame, i: int, op: str) -> bool:
    col = _col("SMA", cond.params)
    try:
        sma_val = df.at[i, col]
        close = float(df.at[i, "close"])
    except KeyError:
        return False
    if pd.isna(sma_val):
        return False
    if op == ">":
        return close > sma_val
    elif op == "<":
        return close < sma_val
    return False


def _eval_threshold(col: str, df: pd.DataFrame, i: int, op: str, threshold: float | str) -> bool:
    try:
        val = df.at[i, col]
    except KeyError:
        return False
    if pd.isna(val):
        return False
    try:
        thresh = float(threshold)
        import math
        if math.isnan(thresh) or math.isinf(thresh):
            return False
    except (TypeError, ValueError):
        return False
    if op == ">":
        return val > thresh
    elif op == "<":
        return val < thresh
    return False


def _eval_macd(df: pd.DataFrame, i: int, op: str, params: dict) -> bool:
    tf = params.get("timeframe")
    fast = int(params.get("fast", 12))
    slow = int(params.get("slow", 26))
    sig = int(params.get("signal", 9))
    base_name = f"macd_line_{fast}_{slow}_{sig}"
    base_sig = f"macd_signal_{fast}_{slow}_{sig}"
    line_col = f"{base_name}_tf_{tf}" if tf is not None else base_name
    signal_col = f"{base_sig}_tf_{tf}" if tf is not None else base_sig

    try:
        line = df.at[i, line_col]
        signal = df.at[i, signal_col]
    except KeyError:
        return False
    if pd.isna(line) or pd.isna(signal):
        return False
    if op == ">":
        return line > signal
    elif op == "<":
        return line < signal
    return False


def _eval_volume_sma(cond: Condition, df: pd.DataFrame, i: int, op: str) -> bool:
    sma_col = _col("VOLUME_SMA", cond.params)
    vol_col = _col("VOLUME", cond.params)
    try:
        sma_val = df.at[i, sma_col]
        vol_val = df.at[i, vol_col]
    except KeyError:
        return False

    if pd.isna(sma_val) or pd.isna(vol_val):
        return False
    
    multiplier = 1.0
    try:
        if cond.right is not None and cond.right != "":
            val = float(cond.right)
            # Treat NaN or inf multiplier as invalid -> safe fallback to False
            import math
            if math.isnan(val) or math.isinf(val):
                return False
            if val != 0.0:
                multiplier = val
    except (TypeError, ValueError):
        pass

    target_val = sma_val * multiplier
    
    if op == ">":
        return vol_val > target_val
    elif op == "<":
        return vol_val < target_val
    return False


# ---------------------------------------------------------------------------
# Phase 2 Optimization: Fast Accessor Compilation
# ---------------------------------------------------------------------------


def compile_condition(cond: Condition, df: pd.DataFrame) -> ConditionAccessor:
    """Compile a condition into a fast array-backed closure.
    Takes `df` to extract NumPy arrays once. The returned closure takes `i` (bar index)
    and returns a boolean.
    """
    ind = cond.indicator.upper()
    op = cond.operator
    import math

    if ind == "SMA":
        col = _col("SMA", cond.params)
        try:
            arr = df[col].values
            close_arr = df["close"].values
        except KeyError:
            return lambda i: False
        
        if op == ">":
            return lambda i, arr=arr, close_arr=close_arr, isna=pd.isna: False if isna(arr[i]) else close_arr[i] > arr[i]
        elif op == "<":
            return lambda i, arr=arr, close_arr=close_arr, isna=pd.isna: False if isna(arr[i]) else close_arr[i] < arr[i]

    elif ind in ("RSI", "ATR", "VOLUME"):
        col = _col(ind, cond.params)
        try:
            arr = df[col].values
            thresh = float(cond.right)
            if math.isnan(thresh) or math.isinf(thresh):
                return lambda i: False
        except (KeyError, TypeError, ValueError):
            return lambda i: False
            
        if op == ">":
            return lambda i, arr=arr, thresh=thresh, isna=pd.isna: False if isna(arr[i]) else arr[i] > thresh
        elif op == "<":
            return lambda i, arr=arr, thresh=thresh, isna=pd.isna: False if isna(arr[i]) else arr[i] < thresh

    elif ind == "MACD":
        tf = cond.params.get("timeframe")
        fast = int(cond.params.get("fast", 12))
        slow = int(cond.params.get("slow", 26))
        sig = int(cond.params.get("signal", 9))
        base_name = f"macd_line_{fast}_{slow}_{sig}"
        base_sig = f"macd_signal_{fast}_{slow}_{sig}"
        line_col = f"{base_name}_tf_{tf}" if tf is not None else base_name
        signal_col = f"{base_sig}_tf_{tf}" if tf is not None else base_sig
        try:
            line_arr = df[line_col].values
            sig_arr = df[signal_col].values
        except KeyError:
            return lambda i: False
            
        if op == ">":
            return lambda i, l=line_arr, s=sig_arr, isna=pd.isna: False if (isna(l[i]) or isna(s[i])) else l[i] > s[i]
        elif op == "<":
            return lambda i, l=line_arr, s=sig_arr, isna=pd.isna: False if (isna(l[i]) or isna(s[i])) else l[i] < s[i]

    elif ind == "VOLUME_SMA":
        sma_col = _col("VOLUME_SMA", cond.params)
        vol_col = _col("VOLUME", cond.params)
        try:
            sma_arr = df[sma_col].values
            vol_arr = df[vol_col].values
        except KeyError:
            return lambda i: False
            
        multiplier = 1.0
        try:
            if cond.right is not None and cond.right != "":
                val = float(cond.right)
                if math.isnan(val) or math.isinf(val):
                    return lambda i: False
                if val != 0.0:
                    multiplier = val
        except (TypeError, ValueError):
            pass
            
        if op == ">":
            return lambda i, s=sma_arr, v=vol_arr, m=multiplier, isna=pd.isna: False if (isna(s[i]) or isna(v[i])) else v[i] > (s[i] * m)
        elif op == "<":
            return lambda i, s=sma_arr, v=vol_arr, m=multiplier, isna=pd.isna: False if (isna(s[i]) or isna(v[i])) else v[i] < (s[i] * m)

    return lambda i: False


def compile_block(block: StrategyBlock, df: pd.DataFrame) -> BlockAccessor:
    """Compile a strategy block into a fast closure evaluating all conditions."""
    if not block.conditions:
        return lambda i: False
        
    accessors = [compile_condition(c, df) for c in block.conditions]
    
    if block.logic.upper() == "AND":
        def _and(i: int, accs=accessors) -> bool:
            for acc in accs:
                if not acc(i):
                    return False
            return True
        return _and
    else:
        def _or(i: int, accs=accessors) -> bool:
            for acc in accs:
                if acc(i):
                    return True
            return False
        return _or
