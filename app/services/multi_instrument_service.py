"""Multi-instrument backtest service — Task 032B.

This is a thin orchestrator that runs a single :class:`Strategy` across
multiple (DataFrame, instrument-profile) pairs by *reusing* the existing
single-instrument :func:`backtest_engine.runner.run_backtest`.  The
underlying engine is **not modified**; the service just loops over the
inputs and aggregates structured per-instrument results.

Design references:

* ``docs/multi_instrument_design_032A.md`` — orchestration, data
  structures, aggregation rules, error handling.
* AGENTS.md §3.2 — layer separation.  No PySide6 imports here.

Engine layer is preserved:

* The single-instrument :func:`run_backtest` in
  ``backtest_engine/runner.py`` remains strictly single-instrument and
  is **not** modified.
* All backtest logic lives in that engine.  The service only collects
  per-instrument results and aggregates them.

Aggregation rules (Task 032B):

* ``total_trades_sum`` — sum of ``total_trades`` across successful runs.
* ``mean_total_pnl``   — arithmetic mean of ``total_pnl`` across successful runs.
* ``min_total_pnl``    — minimum ``total_pnl`` across successful runs.
* ``max_total_pnl``    — maximum ``total_pnl`` across successful runs.
* ``worst_max_drawdown_pnl`` — maximum (largest positive magnitude) ``max_drawdown_pnl``
  across successful runs.  Higher drawdown is worse, hence "worst".
* ``mean_profit_factor`` — mean of numeric ``profit_factor`` values across
  successful runs.  Non-numeric, NaN, and infinite values are excluded.
  When no eligible values exist, the field is ``None`` and a warning is
  emitted.

Failure handling:

* Per-instrument exceptions are caught and converted into a
  :class:`PerInstrumentBacktestResult` with ``success=False`` and a
  non-empty ``error_message``.
* One failed instrument never aborts the rest of the run.
* Empty input list is handled safely — returns a structured result with
  safe empty aggregate values and a warning.

Determinism:

* The output ``per_instrument`` list preserves the input order exactly.
* Input DataFrames are never mutated.  The engine itself only
  ``.copy().reset_index()`` its internal working copy.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from backtest_engine.runner import run_backtest
from core.models.backtest_result import BacktestResult
from core.models.instrument import InstrumentProfile
from core.models.strategy import Strategy


# ---------------------------------------------------------------------------
# Input dataclass
# ---------------------------------------------------------------------------


@dataclass
class InstrumentBacktestInput:
    """One (DataFrame, instrument-profile) pair to be backtested.

    Attributes
    ----------
    label : str
        Human-readable label used to identify the result.  Required so
        the caller can correlate per-instrument outputs to its inputs.
    df : pandas.DataFrame
        Normalized OHLCV data (``datetime, open, high, low, close,
        volume``) for this instrument.  The DataFrame is **not**
        mutated by the service.
    instrument : InstrumentProfile or None
        Optional per-instrument cost / tick / point-value profile.  When
        ``None``, the underlying engine falls back to its hard defaults
        (point_value=1, tick_size=1, commission=0, slippage=0).
    """

    label: str
    df: pd.DataFrame
    instrument: InstrumentProfile | None = None


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------


@dataclass
class PerInstrumentBacktestResult:
    """Structured result of one instrument's backtest.

    On success, ``metrics`` and ``warnings`` are populated from the
    underlying :class:`BacktestResult`.  On failure, ``success`` is
    ``False`` and ``error_message`` captures the exception text.  In
    that case ``metrics`` is an empty dict and ``warnings`` is an empty
    list.
    """

    label: str
    success: bool
    metrics: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    error_message: str | None = None


@dataclass
class MultiInstrumentBacktestResult:
    """Aggregated result of a multi-instrument backtest run.

    Aggregations are computed **only** from instruments with
    ``success == True``.  When no instruments succeed, the aggregate
    values fall back to safe empties (``0`` / ``0.0`` / ``None``) and a
    warning is added.
    """

    instrument_count: int
    success_count: int
    failure_count: int
    per_instrument: list[PerInstrumentBacktestResult]
    aggregate_metrics: dict
    warnings: list[str]
    assumptions: dict


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_multi_instrument_backtest(
    strategy: Strategy,
    inputs: list[InstrumentBacktestInput],
    *,
    initial_capital: float = 100_000.0,
    commission: float | None = None,
    slippage_ticks: float | None = None,
    tick_size: float | None = None,
    point_value: float | None = None,
) -> MultiInstrumentBacktestResult:
    """Run *strategy* across every (df, instrument) pair in *inputs*.

    The underlying :func:`run_backtest` is invoked once per input, with
    per-input instrument profiles and shared scalar backtest defaults.
    Per-instrument exceptions are caught and recorded as
    :class:`PerInstrumentBacktestResult` failures; they never abort the
    whole run.

    Parameters
    ----------
    strategy : Strategy
        The four-block strategy template to apply to every instrument.
    inputs : list[InstrumentBacktestInput]
        Ordered list of (label, df, instrument) triples.  The order is
        preserved in the output's ``per_instrument`` list.
    initial_capital, commission, slippage_ticks, tick_size, point_value :
        Scalar defaults passed to every :func:`run_backtest` call.  When
        an individual ``InstrumentBacktestInput.instrument`` is
        provided, the engine's per-side precedence rules apply (per
        ``backtest_engine/runner.py`` §6.1).
    """
    warnings: list[str] = []
    per_instrument: list[PerInstrumentBacktestResult] = []

    # --- Empty input list: structured safe result with warning. -----
    if not inputs:
        warnings.append("run_multi_instrument_backtest received empty inputs; no backtests executed.")
        empty_aggregates = _empty_aggregate_metrics()
        return MultiInstrumentBacktestResult(
            instrument_count=0,
            success_count=0,
            failure_count=0,
            per_instrument=[],
            aggregate_metrics=empty_aggregates,
            warnings=warnings,
            assumptions=_build_assumptions(
                initial_capital=initial_capital,
                commission=commission,
                slippage_ticks=slippage_ticks,
                tick_size=tick_size,
                point_value=point_value,
                input_count=0,
            ),
        )

    # --- Run each instrument, isolating per-instrument failures. -----
    for spec in inputs:
        result = _run_single(
            strategy=strategy,
            spec=spec,
            initial_capital=initial_capital,
            commission=commission,
            slippage_ticks=slippage_ticks,
            tick_size=tick_size,
            point_value=point_value,
        )
        per_instrument.append(result)

    success_count = sum(1 for r in per_instrument if r.success)
    failure_count = len(per_instrument) - success_count

    # --- Aggregate metrics only from successful runs. ---------------
    aggregate_metrics, agg_warnings = _aggregate_metrics(per_instrument)
    warnings.extend(agg_warnings)

    if failure_count > 0:
        warnings.append(
            f"{failure_count} of {len(per_instrument)} instrument(s) failed; "
            "aggregates were computed from successful runs only."
        )

    return MultiInstrumentBacktestResult(
        instrument_count=len(per_instrument),
        success_count=success_count,
        failure_count=failure_count,
        per_instrument=per_instrument,
        aggregate_metrics=aggregate_metrics,
        warnings=warnings,
        assumptions=_build_assumptions(
            initial_capital=initial_capital,
            commission=commission,
            slippage_ticks=slippage_ticks,
            tick_size=tick_size,
            point_value=point_value,
            input_count=len(per_instrument),
        ),
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run_single(
    *,
    strategy: Strategy,
    spec: InstrumentBacktestInput,
    initial_capital: float,
    commission: float | None,
    slippage_ticks: float | None,
    tick_size: float | None,
    point_value: float | None,
) -> PerInstrumentBacktestResult:
    """Run :func:`run_backtest` for one input, isolating failures."""
    try:
        bt: BacktestResult = run_backtest(
            strategy,
            spec.df,
            initial_capital=initial_capital,
            commission=commission,
            slippage_ticks=slippage_ticks,
            tick_size=tick_size,
            point_value=point_value,
            instrument=spec.instrument,
        )
    except Exception as exc:  # noqa: BLE001 — deliberately broad
        # The service-level contract is: one failure must not stop the
        # rest.  Record the failure and return a safe empty result.
        return PerInstrumentBacktestResult(
            label=spec.label,
            success=False,
            metrics={},
            warnings=[],
            error_message=f"{type(exc).__name__}: {exc}",
        )

    return PerInstrumentBacktestResult(
        label=spec.label,
        success=True,
        metrics=dict(bt.metrics) if bt.metrics else {},
        warnings=list(bt.warnings) if bt.warnings else [],
        error_message=None,
    )


def _is_finite_number(value: Any) -> bool:
    """Return True iff *value* is a finite real number (no NaN, no inf)."""
    if value is None:
        return False
    if isinstance(value, bool):  # bool is a subclass of int; exclude explicitly
        return False
    if isinstance(value, (int, float)):
        return not (math.isnan(value) or math.isinf(value))
    return False


def _aggregate_metrics(
    per_instrument: list[PerInstrumentBacktestResult],
) -> tuple[dict, list[str]]:
    """Compute aggregated metrics from successful runs only.

    Returns a tuple of (aggregate_dict, warnings_list).  When no
    instrument succeeded, all numeric fields are ``0.0`` and
    ``mean_profit_factor`` is ``None``.
    """
    successes = [r for r in per_instrument if r.success]

    if not successes:
        return _empty_aggregate_metrics(), [
            "No successful instruments; aggregate metrics defaulted to safe empty values."
        ]

    # total_pnl series
    pnls: list[float] = []
    for r in successes:
        v = r.metrics.get("total_pnl")
        if _is_finite_number(v):
            pnls.append(float(v))

    total_trades_sum = 0
    for r in successes:
        n = r.metrics.get("total_trades")
        if _is_finite_number(n):
            total_trades_sum += int(n)

    # max_drawdown_pnl series — "worst" is the maximum (largest positive magnitude).
    drawdowns: list[float] = []
    for r in successes:
        v = r.metrics.get("max_drawdown_pnl")
        if _is_finite_number(v):
            drawdowns.append(float(v))

    # profit_factor mean — exclude non-numeric / NaN / inf.
    pfs: list[float] = []
    pf_excluded = 0
    for r in successes:
        v = r.metrics.get("profit_factor")
        if _is_finite_number(v):
            pfs.append(float(v))
        else:
            pf_excluded += 1

    agg: dict = {
        "total_trades_sum": int(total_trades_sum),
        "mean_total_pnl": float(sum(pnls) / len(pnls)) if pnls else 0.0,
        "median_total_pnl": float(statistics.median(pnls)) if pnls else 0.0,
        "min_total_pnl": float(min(pnls)) if pnls else 0.0,
        "max_total_pnl": float(max(pnls)) if pnls else 0.0,
        "worst_max_drawdown_pnl": float(max(drawdowns)) if drawdowns else 0.0,
        "mean_profit_factor": float(sum(pfs) / len(pfs)) if pfs else None,
    }

    warnings: list[str] = []
    if pf_excluded > 0:
        warnings.append(
            f"Excluded {pf_excluded} non-numeric / NaN / infinite profit_factor "
            "value(s) from mean_profit_factor."
        )
    if not pnls:
        warnings.append("No numeric total_pnl values found; total_pnl aggregates defaulted to 0.0.")
    if not drawdowns:
        warnings.append("No numeric max_drawdown_pnl values found; worst_max_drawdown_pnl defaulted to 0.0.")

    return agg, warnings


def _empty_aggregate_metrics() -> dict:
    """Safe empty aggregate values used when nothing succeeded."""
    return {
        "total_trades_sum": 0,
        "mean_total_pnl": 0.0,
        "median_total_pnl": 0.0,
        "min_total_pnl": 0.0,
        "max_total_pnl": 0.0,
        "worst_max_drawdown_pnl": 0.0,
        "mean_profit_factor": None,
    }


def _build_assumptions(
    *,
    initial_capital: float,
    commission: float | None,
    slippage_ticks: float | None,
    tick_size: float | None,
    point_value: float | None,
    input_count: int,
) -> dict:
    """Record the assumptions used to drive the multi-instrument run.

    Per-instrument ``InstrumentProfile`` values may still override
    these on a per-instrument basis (handled inside the engine).
    """
    return {
        "execution_model": "next_bar_open",
        "same_bar_ambiguity": "stop_loss_first",
        "signal_confirmation": "bar_close",
        "position_model": "single_position",
        "initial_capital": initial_capital,
        "commission_per_side": commission,
        "slippage_per_side_ticks": slippage_ticks,
        "tick_size": tick_size,
        "point_value": point_value,
        "input_count": input_count,
        "engine": "backtest_engine.runner.run_backtest",
    }
