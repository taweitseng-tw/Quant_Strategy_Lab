"""Simple fixed-window Walk-forward validator — chronological sliding windows.

Each window:
  1. Defines a contiguous train segment (start → end bars).
  2. Defines a contiguous test segment immediately after the train segment.
  3. Runs a backtest on the **test segment only** (no optimization on test/OOS).
  4. Records whether the test-segment PnL > 0 ("pass").

Aggregates per-window metrics and computes a pass rate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import statistics

import pandas as pd

from core.models.strategy import Strategy
from backtest_engine.runner import run_backtest  # type: ignore[import-untyped]


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------


@dataclass
class WalkForwardWindow:
    """Metadata and metrics for a single walk-forward window."""

    index: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    train_bars: int
    test_bars: int
    metrics: dict = field(default_factory=dict)
    passed: bool = False
    train_metrics: dict = field(default_factory=dict)
    wfe: float | None = None


@dataclass
class WalkForwardResult:
    """Aggregate result of a fixed-window walk-forward run."""

    window_count: int = 0
    pass_count: int = 0
    pass_rate: float = 0.0
    stability_score: float | None = None
    average_wfe: float | None = None
    median_wfe: float | None = None
    defined_wfe_count: int = 0
    undefined_wfe_count: int = 0
    windows: list[WalkForwardWindow] = field(default_factory=list)
    aggregate_metrics: dict = field(default_factory=dict)
    assumptions: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def walk_forward(
    strategy: Strategy,
    df: pd.DataFrame,
    *,
    train_bars: int = 500,
    test_bars: int = 200,
    step_bars: int | None = None,
    pass_criteria: dict[str, float] | None = None,
    calc_wfe: bool = False,
    instrument=None,
    **backtest_kwargs,
) -> WalkForwardResult:
    """Run fixed-window walk-forward validation on *df* with *strategy*.

    Parameters
    ----------
    strategy : Strategy
    df : DataFrame
        Normalized OHLCV data (must have ``datetime`` column).
    train_bars : int
        Number of bars in each training window.
    test_bars : int
        Number of bars in each test window (immediately after train).
    step_bars : int or None
        Bars to advance between windows.  Defaults to *test_bars*
        (non-overlapping test windows).
    instrument : InstrumentProfile or None
    **backtest_kwargs
        Passed through to :func:`run_backtest` (commission, slippage_ticks, …).

    Returns
    -------
    WalkForwardResult
    """
    # ── validate ────────────────────────────────────────────────────────────
    n = len(df)
    step = step_bars if step_bars is not None else test_bars

    if "datetime" not in df.columns:
        return WalkForwardResult(
            window_count=0,
            warnings=["DataFrame missing 'datetime' column."],
            assumptions={
                "train_bars": train_bars,
                "test_bars": test_bars,
                "step_bars": step,
                "pass_criteria": pass_criteria,
                "calc_wfe": calc_wfe,
            },
        )

    if n < train_bars + test_bars:
        return WalkForwardResult(
            window_count=0,
            warnings=[
                f"Dataset too short ({n} bars) for train={train_bars} + "
                f"test={test_bars} walk-forward."
            ],
            assumptions={
                "train_bars": train_bars,
                "test_bars": test_bars,
                "step_bars": step,
                "total_bars": n,
                "pass_criteria": pass_criteria,
                "calc_wfe": calc_wfe,
            },
        )

    # ── slide windows ───────────────────────────────────────────────────────
    windows: list[WalkForwardWindow] = []
    start = 0

    while start + train_bars + test_bars <= n:
        train_end_idx = start + train_bars - 1
        test_start_idx = train_end_idx + 1
        test_end_idx = test_start_idx + test_bars - 1

        train_seg = df.iloc[start:train_end_idx + 1]
        test_seg = df.iloc[test_start_idx:test_end_idx + 1]

        # WFE train backtest
        train_metrics = {}
        wfe = None
        if calc_wfe:
            bt_train = run_backtest(strategy, train_seg, instrument=instrument, **backtest_kwargs)
            train_metrics = bt_train.metrics

        # Run backtest on the test segment only (no optimization here).
        bt = run_backtest(strategy, test_seg, instrument=instrument, **backtest_kwargs)

        if calc_wfe:
            train_total_pnl = train_metrics.get("total_pnl")
            test_total_pnl = bt.metrics.get("total_pnl")
            if train_total_pnl is not None and train_total_pnl > 1e-9 and test_total_pnl is not None:
                wfe = test_total_pnl / train_total_pnl

        passed = _evaluate_pass_criteria(bt.metrics, pass_criteria)

        windows.append(WalkForwardWindow(
            index=len(windows),
            train_start=str(train_seg["datetime"].iloc[0]),
            train_end=str(train_seg["datetime"].iloc[-1]),
            test_start=str(test_seg["datetime"].iloc[0]),
            test_end=str(test_seg["datetime"].iloc[-1]),
            train_bars=len(train_seg),
            test_bars=len(test_seg),
            metrics=bt.metrics,
            passed=passed,
            train_metrics=train_metrics,
            wfe=wfe,
        ))

        start += step

    # ── aggregate ───────────────────────────────────────────────────────────
    pass_count = sum(1 for w in windows if w.passed)
    pass_rate = pass_count / len(windows) if windows else 0.0

    aggregate: dict = {}
    if windows:
        metric_keys = ["total_pnl", "profit_factor", "max_drawdown_pnl", "win_rate", "avg_trade", "total_trades"]
        for key in metric_keys:
            values = [w.metrics.get(key, 0.0) for w in windows]
            aggregate[key] = {
                "mean": _safe_mean(values),
                "median": _safe_median(values),
                "min": min(values),
                "max": max(values),
            }

    stability_score: float | None = None
    if len(windows) >= 2:
        pnls = [w.metrics.get("total_pnl", 0.0) for w in windows]
        std_pnl = statistics.stdev(pnls)
        if std_pnl > 0:
            mean_pnl = sum(pnls) / len(pnls)
            stability_score = mean_pnl / std_pnl

    defined_wfe_list = [w.wfe for w in windows if w.wfe is not None]
    defined_wfe_count = len(defined_wfe_list)
    undefined_wfe_count = len(windows) - defined_wfe_count

    average_wfe = None
    median_wfe = None
    if defined_wfe_count > 0:
        average_wfe = _safe_mean(defined_wfe_list)
        median_wfe = _safe_median(defined_wfe_list)

    return WalkForwardResult(
        window_count=len(windows),
        pass_count=pass_count,
        pass_rate=pass_rate,
        stability_score=stability_score,
        average_wfe=average_wfe,
        median_wfe=median_wfe,
        defined_wfe_count=defined_wfe_count,
        undefined_wfe_count=undefined_wfe_count,
        windows=windows,
        aggregate_metrics=aggregate,
        assumptions={
            "train_bars": train_bars,
            "test_bars": test_bars,
            "step_bars": step,
            "total_bars": n,
            "pass_criteria": pass_criteria,
            "method": "fixed_window_chronological",
            "calc_wfe": calc_wfe,
        },
    )


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


def _safe_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _safe_median(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def _evaluate_pass_criteria(metrics: dict, criteria: dict[str, float] | None) -> bool:
    if criteria is None:
        return metrics.get("total_pnl", 0.0) > 0

    for k, threshold in criteria.items():
        if k == "min_total_pnl" and metrics.get("total_pnl", 0.0) < threshold:
            return False
        elif k == "min_profit_factor" and metrics.get("profit_factor", 0.0) < threshold:
            return False
        elif k == "max_drawdown_pnl" and metrics.get("max_drawdown_pnl", 0.0) > threshold:
            return False
        elif k == "min_win_rate" and metrics.get("win_rate", 0.0) < threshold:
            return False
        elif k == "min_trade_count" and metrics.get("total_trades", 0) < threshold:
            return False
        # Unknown keys are safely ignored per acceptance criteria
    return True
