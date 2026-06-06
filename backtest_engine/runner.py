"""Event-driven backtest engine - bar-by-bar, single-instrument, single-position.

Conservative execution defaults (AGENTS.md Section 6.1):
  - Signal confirmed at bar close
  - Execute at **next** bar open
  - No same-bar optimistic assumptions
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.models.backtest_result import BacktestResult, Trade
from core.models.instrument import InstrumentProfile
from core.models.strategy import Strategy
from strategy_engine.evaluator import evaluate_block
from strategy_engine.indicators import sma


import hashlib

class IndicatorCache:
    """Population-level cache for indicator columns and resampled MTF DataFrames.
    
    This cache strictly prevents data leaks across datasets by tying itself to a
    specific DataFrame fingerprint (derived from its shape and OHLCV boundary samples).
    If a dataset with a different fingerprint is presented, the cache is bypassed.
    """
    def __init__(self, df: pd.DataFrame):
        self.df_fingerprint = self._compute_fingerprint(df)
        self.columns: dict[tuple, pd.Series | dict[str, pd.Series]] = {}
        self.resampled: dict[int, pd.DataFrame] = {}

    def _compute_fingerprint(self, df: pd.DataFrame) -> str:
        if len(df) == 0:
            return "empty"
        
        # We hash the core OHLCV + datetime columns across all rows to guarantee
        # any middle-row mutation is caught. pd.util.hash_pandas_object is fast in C.
        cols_to_hash = [c for c in ('datetime', 'open', 'high', 'low', 'close', 'volume') if c in df.columns]
        sub_df = df[cols_to_hash]
        
        row_hashes = pd.util.hash_pandas_object(sub_df, index=True)
        h = hashlib.sha256(row_hashes.values.tobytes())
        h.update(str(cols_to_hash).encode('utf-8'))
        h.update(str(len(df)).encode('utf-8'))
                    
        return h.hexdigest()

    def is_valid(self, df: pd.DataFrame) -> bool:
        return self._compute_fingerprint(df) == self.df_fingerprint


def run_backtest(
    strategy: Strategy,
    df: pd.DataFrame,
    *,
    initial_capital: float = 100_000.0,
    commission: float | None = None,
    slippage_ticks: float | None = None,
    tick_size: float | None = None,
    point_value: float | None = None,
    instrument: InstrumentProfile | None = None,
    indicator_cache: IndicatorCache | None = None,
    execution_delay_bars: int = 0,
) -> BacktestResult:
    """Run an event-driven backtest of *strategy* on *df*.

    Parameters
    ----------
    strategy : Strategy
        Four-block strategy definition.
    df : DataFrame
        Normalized OHLCV data (datetime, open, high, low, close, volume).
    initial_capital : float
        Starting cash (default 100 000).  Equity = cash + position mark-to-market.
    commission : float or None
        Per-**side** fixed commission in dollars.  ``None`` (default) means
        use ``instrument.commission_value`` if *instrument* is provided,
        otherwise 0.0.  An explicit ``0.0`` **overrides** the instrument.
    slippage_ticks : float or None
        Per-side slippage in ticks.  ``None`` -> instrument default or 0.0.
    tick_size : float or None
        Value of one tick (price units).  ``None`` -> instrument default or 1.0.
    point_value : float or None
        Dollar value of one price-unit move.  ``None`` -> instrument default or 1.0.
    instrument : InstrumentProfile or None
        Convenience object that supplies *point_value*, *tick_size*,
        *commission_value*, and *slippage_ticks*.  Individual keyword
        arguments **always** take precedence, including zero values.

    Returns
    -------
    BacktestResult
        Structured output with trades, equity curve, drawdown, metrics,
        assumptions, and warnings.
    """
    # -- guard execution_delay_bars ------------------------------------------
    if not isinstance(execution_delay_bars, int) or isinstance(execution_delay_bars, bool):
        raise ValueError(
            f"execution_delay_bars must be an int, got {type(execution_delay_bars).__name__} "
            f"({execution_delay_bars!r})."
        )
    if execution_delay_bars < 0:
        raise ValueError(
            f"execution_delay_bars must be >= 0, got {execution_delay_bars}."
        )

    # -- resolve parameters: explicit args > instrument > hard defaults -------
    _pv = point_value
    _ts = tick_size
    _comm = commission
    _slip = slippage_ticks

    if instrument is not None:
        if _pv is None:
            _pv = instrument.point_value
        if _ts is None:
            _ts = instrument.tick_size
        if _comm is None:
            _comm = instrument.commission_value
        if _slip is None:
            _slip = instrument.slippage_ticks

    # Apply hard defaults when nothing was provided.
    if _pv is None:
        _pv = 1.0
    if _ts is None:
        _ts = 1.0
    if _comm is None:
        _comm = 0.0
    if _slip is None:
        _slip = 0.0

    point_value = _pv
    tick_size = _ts
    commission = _comm
    slippage_ticks = _slip
    # -- prepare data --------------------------------------------------------
    data = df.copy().reset_index(drop=True)
    n = len(data)

    # Pre-compute indicators on the full dataset.  Each indicator uses a
    # backward-looking rolling window - no future leak.
    _precompute_indicators(data, strategy, indicator_cache)

    # -- state ----------------------------------------------------------------
    equity = np.full(n, np.nan, dtype=float)
    drawdown = np.full(n, np.nan, dtype=float)

    # Phase 1 Optimization: Local array extraction to avoid pd.DataFrame.iloc
    open_arr = data["open"].values
    high_arr = data["high"].values
    low_arr = data["low"].values
    close_arr = data["close"].values
    datetime_arr = data["datetime"].tolist()

    cash = float(initial_capital)
    position: str | None = None       # "long", "short", or None
    entry_price: float = 0.0
    entry_bar: int = -1
    sl_price: float | None = None
    tp_price: float | None = None

    # Phase 2: Pre-compile blocks
    from strategy_engine.evaluator import compile_block
    long_entry_acc = compile_block(strategy.long_entry, data)
    short_entry_acc = compile_block(strategy.short_entry, data)
    long_exit_acc = compile_block(strategy.long_exit, data)
    short_exit_acc = compile_block(strategy.short_exit, data)

    from core.models.strategy import RiskManagement
    rm = strategy.risk_management or RiskManagement()
    has_session_end = rm.close_end_of_session and rm.session_end_time is not None
    parsed_session_time = None
    if has_session_end:
        from datetime import datetime
        try:
            parsed_session_time = datetime.strptime(rm.session_end_time[:5], "%H:%M").time()
        except Exception as e:
            raise ValueError(f"Invalid session_end_time format: {rm.session_end_time}. Expected 'HH:MM' or 'HH:MM:SS'.") from e

    # Queued action for the NEXT bar open.  ("enter", direction, delay_rem) or ("exit", position, 0).
    pending: tuple[str, str, int] | None = None

    trades: list[Trade] = []
    warnings: list[str] = []
    peak_equity = initial_capital

    # -- main loop ------------------------------------------------------------
    for i in range(n):
        bar_open = float(open_arr[i])
        bar_close = float(close_arr[i])
        bar_datetime = datetime_arr[i]

        # --- 1. Execute queued actions at bar open ---
        execute_now = False
        if pending is not None:
            action, direction, delay_rem = pending
            if action == "enter" and has_session_end and bar_datetime.time() >= parsed_session_time:
                warnings.append(f"Canceled pending {direction} entry at index {i} due to session end ({rm.session_end_time}).")
                pending = None
            elif delay_rem > 0:
                pending = (action, direction, delay_rem - 1)
            else:
                execute_now = True

        if execute_now:
            action, direction, _ = pending
            if action == "enter":
                # Apply slippage: for longs, we pay slightly more; for shorts, slightly less.
                slip = slippage_ticks * tick_size
                fill_price = bar_open + slip if direction == "long" else bar_open - slip
                position = direction
                entry_price = fill_price
                entry_bar = i
                # Calculate SL/TP
                sl_price = None
                tp_price = None
                if position == "long":
                    if rm.stop_loss_ticks is not None:
                        sl_price = entry_price - rm.stop_loss_ticks * tick_size
                    elif rm.stop_loss_pct is not None:
                        sl_price = entry_price * (1 - rm.stop_loss_pct)
                    if rm.take_profit_ticks is not None:
                        tp_price = entry_price + rm.take_profit_ticks * tick_size
                    elif rm.take_profit_pct is not None:
                        tp_price = entry_price * (1 + rm.take_profit_pct)
                else:  # short
                    if rm.stop_loss_ticks is not None:
                        sl_price = entry_price + rm.stop_loss_ticks * tick_size
                    elif rm.stop_loss_pct is not None:
                        sl_price = entry_price * (1 + rm.stop_loss_pct)
                    if rm.take_profit_ticks is not None:
                        tp_price = entry_price - rm.take_profit_ticks * tick_size
                    elif rm.take_profit_pct is not None:
                        tp_price = entry_price * (1 - rm.take_profit_pct)
                # Deduct entry-side commission immediately.
                cash -= commission
            elif action == "exit":
                slip = slippage_ticks * tick_size
                # Reverse the entry slippage: exit longs lower, shorts higher.
                fill_price = bar_open - slip if position == "long" else bar_open + slip

                gross_pnl = _compute_pnl(position, entry_price, fill_price)
                # Convert price movement to dollars via point_value.
                gross_dollars = gross_pnl * point_value
                # round-trip PnL: gross dollars minus both entry and exit commission.
                round_trip_pnl = gross_dollars - 2 * commission
                # Cash inflow at exit: gross dollars minus the exit commission.
                cash += gross_dollars - commission

                trades.append(Trade(
                    entry_time=datetime_arr[entry_bar],
                    exit_time=bar_datetime,
                    direction=position or "",
                    entry_price=entry_price,
                    exit_price=fill_price,
                    quantity=1,
                    pnl=round_trip_pnl,
                    exit_reason="signal",
                ))

                # Reset position; we may open a new one this same bar close.
                position = None
                entry_price = 0.0

            pending = None

        # --- 1.5 Active Risk Management (Intra-Bar) ---
        if position is not None and (sl_price is not None or tp_price is not None):
            bar_high = float(high_arr[i])
            bar_low = float(low_arr[i])
            
            hit_sl = False
            hit_tp = False
            
            if position == "long":
                if sl_price is not None and bar_low <= sl_price:
                    hit_sl = True
                if tp_price is not None and bar_high >= tp_price:
                    hit_tp = True
            else:  # short
                if sl_price is not None and bar_high >= sl_price:
                    hit_sl = True
                if tp_price is not None and bar_low <= tp_price:
                    hit_tp = True

            if hit_sl or hit_tp:
                # Same-bar ambiguity: Stop-Loss wins
                reason = "stop_loss" if hit_sl else "take_profit"
                
                # Determine exit price based on direction and gap-through logic
                slip = slippage_ticks * tick_size
                if position == "long":
                    if reason == "stop_loss":
                        # If gap down below SL, execute at open. Otherwise at SL.
                        trigger_price = bar_open if bar_open <= sl_price else sl_price
                        fill_price = trigger_price - slip
                    else:
                        # If gap up above TP, execute at open. Otherwise at TP.
                        trigger_price = bar_open if bar_open >= tp_price else tp_price
                        # TP acts like a limit order, but applying slippage against trader for conservatism.
                        fill_price = trigger_price - slip
                else:  # short
                    if reason == "stop_loss":
                        # Gap up above SL
                        trigger_price = bar_open if bar_open >= sl_price else sl_price
                        fill_price = trigger_price + slip
                    else:
                        # Gap down below TP
                        trigger_price = bar_open if bar_open <= tp_price else tp_price
                        fill_price = trigger_price + slip

                # Check if gap execution occurred and warn
                if reason == "stop_loss" and trigger_price == bar_open:
                    warnings.append(f"Gap execution on Stop-Loss at index {i}: requested {sl_price}, filled {bar_open}")
                elif reason == "take_profit" and trigger_price == bar_open:
                    warnings.append(f"Gap execution on Take-Profit at index {i}: requested {tp_price}, filled {bar_open}")

                # Process the exit
                gross_pnl = _compute_pnl(position, entry_price, fill_price)
                gross_dollars = gross_pnl * point_value
                round_trip_pnl = gross_dollars - 2 * commission
                cash += gross_dollars - commission

                trades.append(Trade(
                    entry_time=datetime_arr[entry_bar],
                    exit_time=bar_datetime,
                    direction=position or "",
                    entry_price=entry_price,
                    exit_price=fill_price,
                    quantity=1,
                    pnl=round_trip_pnl,
                    exit_reason=reason,
                ))

                # Reset position
                position = None
                entry_price = 0.0

        # --- 1.8 Session-End Exit ---
        session_ended = False
        if has_session_end and bar_datetime.time() >= parsed_session_time:
            session_ended = True

        if session_ended and position is not None:
            slip = slippage_ticks * tick_size
            fill_price = bar_close - slip if position == "long" else bar_close + slip

            gross_pnl = _compute_pnl(position, entry_price, fill_price)
            gross_dollars = gross_pnl * point_value
            round_trip_pnl = gross_dollars - 2 * commission
            cash += gross_dollars - commission

            trades.append(Trade(
                entry_time=datetime_arr[entry_bar],
                exit_time=bar_datetime,
                direction=position,
                entry_price=entry_price,
                exit_price=fill_price,
                quantity=1,
                pnl=round_trip_pnl,
                exit_reason="session_end",
            ))

            position = None
            entry_price = 0.0
            pending = None

        # --- 2. Mark-to-market equity at bar close ---
        if position is not None:
            mtm = _compute_pnl(position, entry_price, bar_close)
            equity[i] = cash + mtm * point_value
        else:
            equity[i] = cash

        # Track peak and drawdown.
        if equity[i] > peak_equity:
            peak_equity = equity[i]
        drawdown[i] = peak_equity - equity[i]

        # --- 3. Evaluate conditions at bar close ---
        if position is not None:
            # Check exit for current position.
            exit_acc = long_exit_acc if position == "long" else short_exit_acc
            if exit_acc(i):
                pending = ("exit", position, 0)
        else:
            # No position - check both entry blocks.
            # Long takes priority over short for MVP simplicity.
            if not session_ended and pending is None:
                if long_entry_acc(i):
                    pending = ("enter", "long", execution_delay_bars)
                elif short_entry_acc(i):
                    pending = ("enter", "short", execution_delay_bars)

    # -- warn about unexecuted last-bar signal -------------------------------
    if pending is not None:
        warnings.append(
            f"Signal ({pending[1]}) pending at end of data (index {n - 1}) "
            f"but cannot execute - no next bar open available."
        )

    # -- close any open position at end of data ------------------------------
    if position is not None:
        # Exit at the last bar's close.
        last_close = float(close_arr[-1])
        gross_pnl = _compute_pnl(position, entry_price, last_close)
        gross_dollars = gross_pnl * point_value
        round_trip_pnl = gross_dollars - 2 * commission
        cash += gross_dollars - commission

        trades.append(Trade(
            entry_time=datetime_arr[entry_bar],
            exit_time=datetime_arr[-1],
            direction=position,
            entry_price=entry_price,
            exit_price=last_close,
            quantity=1,
            pnl=round_trip_pnl,
            exit_reason="end_of_data",
        ))

        # Update final equity point.
        equity[-1] = cash
        if equity[-1] > peak_equity:
            peak_equity = equity[-1]
        drawdown[-1] = peak_equity - equity[-1]

    # -- build result ---------------------------------------------------------
    from backtest_engine.metrics import compute_metrics

    eq_df = pd.DataFrame({
        "datetime": data["datetime"],
        "equity": equity,
    })
    dd_df = pd.DataFrame({
        "datetime": data["datetime"],
        "drawdown": drawdown,
    })

    assumptions = {
        "execution_model": "next_bar_open",
        "same_bar_ambiguity": "stop_loss_first",
        "initial_capital": initial_capital,
        "commission_per_side": commission,
        "commission_model": "per_side",
        "slippage_per_side_ticks": slippage_ticks,
        "tick_size": tick_size,
        "point_value": point_value,
        "instrument": instrument.symbol if instrument else "default",
        "signal_confirmation": "bar_close",
        "position_model": "single_position",
        "stop_take_profit_enabled": False,
        "execution_delay_bars": execution_delay_bars,
    }
    
    from core.models.strategy import RiskManagement
    rm = strategy.risk_management or RiskManagement()
    has_rm = (
        rm.stop_loss_ticks is not None or 
        rm.take_profit_ticks is not None or 
        rm.stop_loss_pct is not None or 
        rm.take_profit_pct is not None
    )
    
    if has_rm:
        assumptions["stop_take_profit_enabled"] = True
        assumptions["risk_management_precedence"] = "ticks_over_percent"
        if rm.stop_loss_ticks is not None:
            assumptions["stop_loss_ticks"] = rm.stop_loss_ticks
        if rm.stop_loss_pct is not None:
            assumptions["stop_loss_pct"] = rm.stop_loss_pct
        if rm.take_profit_ticks is not None:
            assumptions["take_profit_ticks"] = rm.take_profit_ticks
        if rm.take_profit_pct is not None:
            assumptions["take_profit_pct"] = rm.take_profit_pct

    if has_session_end:
        assumptions["close_end_of_session"] = True
        assumptions["session_end_time"] = rm.session_end_time

    result = BacktestResult(
        trades=trades,
        equity_curve=eq_df,
        drawdown_curve=dd_df,
        metrics=compute_metrics(trades, drawdown_curve=dd_df),
        assumptions=assumptions,
        warnings=warnings,
    )

    return result


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


def _precompute_indicators(df: pd.DataFrame, strategy: Strategy, cache: IndicatorCache | None = None) -> None:
    """Add indicator columns to *df* for all conditions referenced by *strategy*.

    - Base-timeframe conditions: backward-looking rolling windows on *df* directly.
    - Multi-timeframe conditions (``params[\"timeframe\"]`` present):
      resample -> compute indicator -> merge_asof back to *df* via ``available_at``.

    Only backward-looking rolling windows are used - no future leak.
    """
    from strategy_engine.indicators import atr as _atr, macd as _macd, rsi as _rsi

    seen: set[tuple] = set()
    base_minutes = _infer_base_minutes(df)

    use_cache = False
    if cache is not None:
        if cache.is_valid(df):
            use_cache = True
            resampled_cache = cache.resampled
        else:
            # fingerprint failed, bypass cache safely
            use_cache = False
            resampled_cache = {}
    else:
        resampled_cache = {}

    for block in (strategy.long_entry, strategy.long_exit,
                  strategy.short_entry, strategy.short_exit):
        for cond in block.conditions:
            ind = cond.indicator.upper()
            tf = cond.params.get("timeframe")

            # -- base-timeframe path -------------------------------------
            if tf is None:
                params_no_tf = tuple((k, v) for k, v in sorted(cond.params.items()))
                key = ("BASE", ind, params_no_tf)
                if key in seen:
                    continue
                seen.add(key)
                
                if use_cache and key in cache.columns:
                    for k, v in cache.columns[key].items():
                        df[k] = v
                    continue
                    
                added_cols = _compute_base_indicator_cols(df, cond, ind)
                if use_cache and added_cols:
                    cache.columns[key] = {k: df[k] for k in added_cols}
                continue

            # -- MTF path ------------------------------------------------
            tf = _validate_mtf_timeframe(tf, base_minutes, ind)
            if tf == base_minutes:
                params_no_tf = tuple((k, v) for k, v in sorted(cond.params.items()))
                key = ("BASE", ind, params_no_tf)
                if key in seen:
                    continue
                seen.add(key)
                
                if use_cache and key in cache.columns:
                    for k, v in cache.columns[key].items():
                        df[k] = v
                    continue
                    
                added_cols = _compute_base_indicator_cols(df, cond, ind)
                if use_cache and added_cols:
                    cache.columns[key] = {k: df[k] for k in added_cols}
                continue

            # Build dedup key: (indicator, params-without-timeframe, timeframe)
            params_no_tf = tuple(
                (k, v) for k, v in sorted(cond.params.items()) if k != "timeframe"
            )
            key = ("MTF", ind, params_no_tf, tf)
            if key in seen:
                continue
            seen.add(key)
            
            if use_cache and key in cache.columns:
                for k, v in cache.columns[key].items():
                    df[k] = v
                continue

            # Resample once per timeframe (cached).
            if tf not in resampled_cache:
                htf_df = _resample_for_mtf(df, base_minutes, tf)
                htf_df = _drop_incomplete_final_htf_group(htf_df, base_minutes, tf)
                resampled_cache[tf] = htf_df
            else:
                htf_df = resampled_cache[tf]

            # Compute indicator on HTF series.
            htf_col_names = _compute_indicator_on_htf(htf_df, cond, ind, tf)
            cached_cols_to_save = {}
            for htf_col, base_col in htf_col_names:
                _merge_htf_indicator(df, htf_df, htf_col, base_col)
                cached_cols_to_save[base_col] = df[base_col]
                
            if use_cache:
                cache.columns[key] = cached_cols_to_save


# ---------------------------------------------------------------------------
# MTF helpers (Task 049B)
# ---------------------------------------------------------------------------


def _compute_base_indicator_cols(
    df: pd.DataFrame,
    cond,  # Condition
    ind: str,
) -> list[str]:
    """Compute a base-timeframe indicator on *df*. Returns list of added column names."""
    from strategy_engine.indicators import atr as _atr, macd as _macd, rsi as _rsi

    if ind == "SMA":
        period = int(cond.params.get("period", 20))
        col = f"sma_{period}"
        df[col] = sma(df["close"], period)
        return [col]

    elif ind == "RSI":
        period = int(cond.params.get("period", 14))
        col = f"rsi_{period}"
        df[col] = _rsi(df["close"], period)
        return [col]

    elif ind == "MACD":
        fast = int(cond.params.get("fast", 12))
        slow = int(cond.params.get("slow", 26))
        sig = int(cond.params.get("signal", 9))
        macd_df = _macd(df["close"], fast=fast, slow=slow, signal=sig)
        l, s, h = f"macd_line_{fast}_{slow}_{sig}", f"macd_signal_{fast}_{slow}_{sig}", f"macd_histogram_{fast}_{slow}_{sig}"
        df[l] = macd_df["macd_line"]
        df[s] = macd_df["macd_signal"]
        df[h] = macd_df["macd_histogram"]
        return [l, s, h]

    elif ind == "ATR":
        period = int(cond.params.get("period", 14))
        col = f"atr_{period}"
        df[col] = _atr(df, period)
        return [col]

    elif ind == "VOLUME_SMA":
        from strategy_engine.indicators import volume_sma as _volume_sma
        period = int(cond.params.get("period", 20))
        col = f"volume_sma_{period}"
        df[col] = _volume_sma(df["volume"], period)
        return [col]

    elif ind == "VOLUME":
        # VOLUME is a raw column reference - no computation needed.
        return []

    return []


def _infer_base_minutes(df: pd.DataFrame) -> int:
    """Infer the base timeframe in minutes from datetime spacing."""
    if len(df) < 2:
        return 1  # safe default for trivial DataFrames
    diffs = df["datetime"].diff().dropna()
    seconds = diffs.dt.total_seconds().mode()
    if len(seconds) == 0:
        return 1
    return int(seconds.iloc[0] / 60)


def _validate_mtf_timeframe(tf: object, base_minutes: int, indicator: str) -> int:
    """Validate that *tf* is a positive int, >= base, and a multiple.

    Returns the validated int *tf*.  Raises ``ValueError`` on invalid input.
    """
    if not isinstance(tf, int) or isinstance(tf, bool):
        raise ValueError(
            f"Multi-timeframe condition ({indicator}): "
            f"timeframe must be an int, got {type(tf).__name__} ({tf!r})."
        )
    if tf <= 0:
        raise ValueError(
            f"Multi-timeframe condition ({indicator}): "
            f"timeframe must be positive, got {tf}."
        )
    if tf < base_minutes:
        raise ValueError(
            f"Multi-timeframe condition ({indicator}): "
            f"timeframe ({tf} min) is smaller than base timeframe "
            f"({base_minutes} min)."
        )
    if tf % base_minutes != 0:
        raise ValueError(
            f"Multi-timeframe condition ({indicator}): "
            f"timeframe ({tf} min) is not an integer multiple of "
            f"base timeframe ({base_minutes} min)."
        )
    return tf


def _resample_for_mtf(df: pd.DataFrame, base_minutes: int, target_minutes: int) -> pd.DataFrame:
    """Resample *df* to *target_minutes*, returning HTF bars with ``available_at``."""
    from data_engine.resampler import resample
    return resample(df, source_minutes=base_minutes, target_minutes=target_minutes)


def _drop_incomplete_final_htf_group(
    htf_df: pd.DataFrame,
    base_minutes: int,
    target_minutes: int,
) -> pd.DataFrame:
    """Drop the last HTF candle if it has fewer constituent bars than expected.

    The number of base bars per HTF candle is ``target_minutes / base_minutes``.
    We derive the actual count from the ``available_at`` column: each HTF candle's
    ``available_at`` timestamp minus its ``datetime``, plus one base bar.

    WARNING: This span-based logic assumes regular base-bar spacing.
    If the base data has internal gaps (e.g., missing bars that don't bridge a
    holiday/weekend), a final candle missing its last few bars might still pass
    this span check and be kept. This is a known limitation of the current MVP
    precompute design.

    For simplicity, we compute the expected span and verify:
      - If the last HTF row's ``datetime`` to ``available_at`` span is less than
        ``(target_minutes / base_minutes - 1) * base_minutes`` minutes, drop it.
    """
    if len(htf_df) == 0:
        return htf_df

    expected_bars = target_minutes // base_minutes
    if expected_bars <= 1:
        return htf_df  # No multi-bar grouping - nothing to drop.

    last = htf_df.iloc[-1]
    dt = last["datetime"]
    avail = last["available_at"]
    if pd.isna(dt) or pd.isna(avail):
        return htf_df

    # Span in minutes between candle start and last constituent bar.
    span_minutes = int((avail - dt).total_seconds() / 60)
    # Expected span: (expected_bars - 1) * base_minutes
    expected_span = (expected_bars - 1) * base_minutes

    if span_minutes < expected_span:
        return htf_df.iloc[:-1].copy()

    return htf_df


def _compute_indicator_on_htf(
    htf_df: pd.DataFrame,
    cond,  # Condition
    ind: str,
    tf: int,
) -> list[tuple[str, str]]:
    """Compute an indicator on *htf_df* and return ``[(htf_col, base_col), ...]`` pairs.

    Each pair is (column_name_on_htf_df, target_column_name_on_base_df).
    """
    from strategy_engine.indicators import atr as _atr, macd as _macd, rsi as _rsi

    if ind == "SMA":
        period = int(cond.params.get("period", 20))
        col = f"sma_{period}"
        htf_df[col] = sma(htf_df["close"], period)
        return [(col, f"{col}_tf_{tf}")]

    elif ind == "RSI":
        period = int(cond.params.get("period", 14))
        col = f"rsi_{period}"
        htf_df[col] = _rsi(htf_df["close"], period)
        return [(col, f"{col}_tf_{tf}")]

    elif ind == "MACD":
        fast = int(cond.params.get("fast", 12))
        slow = int(cond.params.get("slow", 26))
        sig = int(cond.params.get("signal", 9))
        macd_df = _macd(htf_df["close"], fast=fast, slow=slow, signal=sig)
        hl, hs, hh = f"macd_line_{fast}_{slow}_{sig}", f"macd_signal_{fast}_{slow}_{sig}", f"macd_histogram_{fast}_{slow}_{sig}"
        htf_df[hl] = macd_df["macd_line"]
        htf_df[hs] = macd_df["macd_signal"]
        htf_df[hh] = macd_df["macd_histogram"]
        return [
            (hl, f"{hl}_tf_{tf}"),
            (hs, f"{hs}_tf_{tf}"),
            (hh, f"{hh}_tf_{tf}"),
        ]

    elif ind == "ATR":
        period = int(cond.params.get("period", 14))
        col = f"atr_{period}"
        htf_df[col] = _atr(htf_df, period)
        return [(col, f"{col}_tf_{tf}")]

    elif ind == "VOLUME":
        col = "volume"
        return [(col, f"volume_tf_{tf}")]

    elif ind == "VOLUME_SMA":
        from strategy_engine.indicators import volume_sma as _volume_sma
        period = int(cond.params.get("period", 20))
        col = f"volume_sma_{period}"
        htf_df[col] = _volume_sma(htf_df["volume"], period)
        return [(col, f"{col}_tf_{tf}"), ("volume", f"volume_tf_{tf}")]

    return []


def _merge_htf_indicator(
    base_df: pd.DataFrame,
    htf_df: pd.DataFrame,
    htf_col: str,
    base_col: str,
) -> None:
    """Merge *htf_col* from *htf_df* into *base_df* as *base_col*.

    Uses ``pd.merge_asof(direction="backward")`` with base ``datetime``
    as left key and HTF ``available_at`` as right key (Section 2.7, Section 4.7 of
    the MTF design doc).  No future leak: a base bar only sees HTF values
    from candles whose last constituent bar timestamp <= the base bar start.
    """
    right = htf_df[["available_at", htf_col]].dropna(subset=[htf_col]).copy()
    merged = pd.merge_asof(
        base_df[["datetime"]].reset_index(drop=True),
        right.sort_values("available_at").reset_index(drop=True),
        left_on="datetime",
        right_on="available_at",
        direction="backward",
    )
    base_df[base_col] = merged[htf_col].values


def _compute_pnl(direction: str | None, entry_price: float, exit_price: float) -> float:
    """Compute mark-to-market PnL for the current position."""
    if direction == "long":
        return exit_price - entry_price
    elif direction == "short":
        return entry_price - exit_price
    return 0.0
