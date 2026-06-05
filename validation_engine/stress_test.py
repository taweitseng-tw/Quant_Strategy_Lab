"""Basic stress test engine — re-runs or transforms backtests to measure robustness.

Supports:
  - Commission multiplier (default 2×)
  - Slippage multiplier (default 2×)
  - One-bar execution delay (shifts price data forward by 1 bar)
  - Random missed trades (deterministic seed)

All stress tests are **read-only** with respect to the baseline result.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable

import pandas as pd

from core.models.backtest_result import BacktestResult, Trade
from core.models.strategy import Strategy
from backtest_engine.runner import run_backtest  # type: ignore[import-untyped]
from backtest_engine.metrics import compute_metrics


# ---------------------------------------------------------------------------
# Stress result model
# ---------------------------------------------------------------------------


@dataclass
class StressTestResult:
    """Structured output of a single stress test."""

    test_name: str
    passed: bool
    baseline_metrics: dict = field(default_factory=dict)
    stressed_metrics: dict = field(default_factory=dict)
    degradation: dict = field(default_factory=dict)
    assumptions: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    threshold: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Stress test functions
# ---------------------------------------------------------------------------


def stress_commission_multiplier(
    strategy: Strategy,
    df: pd.DataFrame,
    baseline: BacktestResult,
    *,
    multiplier: float = 2.0,
    instrument=None,
) -> StressTestResult:
    """Re-run backtest with commission × *multiplier*.

    Baseline and stressed metrics are compared; ``passed`` is ``True`` when
    total PnL does not **improve** under higher costs.
    """
    base_comm = float(baseline.assumptions.get("commission_per_side", 0.0))
    stressed_comm = base_comm * multiplier

    # Re-run with higher commission.
    stressed = run_backtest(
        strategy, df,
        commission=stressed_comm,
        instrument=instrument,
    )

    name = f"commission_{multiplier}x"
    return _build_result(
        test_name=name,
        baseline_metrics=baseline.metrics,
        stressed_metrics=stressed.metrics,
        assumptions={
            "baseline_commission": base_comm,
            "stressed_commission": stressed_comm,
            "multiplier": multiplier,
        },
        threshold={"pnl_must_not_improve": True},
        baseline_assumptions=baseline.assumptions,
    )


def stress_slippage_multiplier(
    strategy: Strategy,
    df: pd.DataFrame,
    baseline: BacktestResult,
    *,
    multiplier: float = 2.0,
    instrument=None,
) -> StressTestResult:
    """Re-run backtest with slippage_ticks × *multiplier*."""
    base_slip = float(baseline.assumptions.get("slippage_per_side_ticks", 0.0))
    stressed_slip = base_slip * multiplier

    stressed = run_backtest(
        strategy, df,
        slippage_ticks=stressed_slip,
        instrument=instrument,
    )

    name = f"slippage_{multiplier}x"
    return _build_result(
        test_name=name,
        baseline_metrics=baseline.metrics,
        stressed_metrics=stressed.metrics,
        assumptions={
            "baseline_slippage": base_slip,
            "stressed_slippage": stressed_slip,
            "multiplier": multiplier,
        },
        threshold={"pnl_must_not_improve": True},
        baseline_assumptions=baseline.assumptions,
    )


def stress_one_bar_delay(
    strategy: Strategy,
    df: pd.DataFrame,
    baseline: BacktestResult,
    *,
    instrument=None,
) -> StressTestResult:
    """Simulate one-bar execution delay by shifting price data forward.

    Each bar's OHLCV values are shifted down by one row (the bar at index *i*
    sees the prices that were originally at index *i-1*).  The backtest is
    re-run on the shifted data, which has one fewer row.

    This is equivalent to the strategy observing prices one bar late —
    a conservative model of execution/signal latency.
    """
    if len(df) < 2:
        return StressTestResult(
            test_name="one_bar_delay",
            passed=True,
            baseline_metrics=baseline.metrics,
            stressed_metrics=baseline.metrics,
            degradation={},
            assumptions={"delay_bars": 1},
            warnings=["DataFrame too short (< 2 bars) for one-bar delay stress."],
            threshold={"pnl_must_not_improve": True},
        )

    # Shift OHLCV columns forward by 1 bar, drop the first row.
    price_cols = ["open", "high", "low", "close", "volume"]
    shifted = df.copy()
    shifted[price_cols] = shifted[price_cols].shift(1)
    shifted.dropna(subset=price_cols, inplace=True)
    shifted.reset_index(drop=True, inplace=True)

    # Re-run backtest on the delayed data.
    stressed = run_backtest(strategy, shifted, instrument=instrument)

    return _build_result(
        test_name="one_bar_delay",
        baseline_metrics=baseline.metrics,
        stressed_metrics=stressed.metrics,
        assumptions={
            "delay_bars": 1,
            "baseline_rows": len(df),
            "stressed_rows": len(shifted),
            "method": "price_shift_forward",
        },
        threshold={"pnl_must_not_improve": True},
        baseline_assumptions=baseline.assumptions,
    )


def stress_random_missed_trades(
    baseline: BacktestResult,
    *,
    miss_probability: float = 0.1,
    seed: int = 42,
) -> StressTestResult:
    """Randomly drop trades from the baseline trade list and recompute metrics.

    Uses a deterministic *seed* so results are reproducible.
    """
    trades = baseline.trades
    if not trades:
        return StressTestResult(
            test_name="random_missed_trades",
            passed=True,
            baseline_metrics=baseline.metrics,
            stressed_metrics=baseline.metrics,
            degradation={},
            assumptions={"miss_probability": miss_probability, "seed": seed},
            warnings=["No trades to stress — baseline has zero trades."],
            threshold={"pnl_must_not_improve": True},
        )

    rng = random.Random(seed)
    surviving = [t for t in trades if rng.random() >= miss_probability]

    stressed_metrics = compute_metrics(surviving)

    return _build_result(
        test_name="random_missed_trades",
        baseline_metrics=baseline.metrics,
        stressed_metrics=stressed_metrics,
        assumptions={
            "miss_probability": miss_probability,
            "seed": seed,
            "baseline_trade_count": len(trades),
            "stressed_trade_count": len(surviving),
        },
        threshold={"pnl_must_not_improve": True},
        baseline_assumptions=baseline.assumptions,
    )


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


def _build_result(
    test_name: str,
    baseline_metrics: dict,
    stressed_metrics: dict,
    assumptions: dict,
    threshold: dict,
    baseline_assumptions: dict | None = None,
) -> StressTestResult:
    # Compute per-metric degradation as percentage change.
    degradation: dict[str, float] = {}
    warnings: list[str] = []

    for key in ("total_pnl", "profit_factor", "win_rate", "avg_trade", "total_trades"):
        base = float(baseline_metrics.get(key, 0.0))
        stressed = float(stressed_metrics.get(key, 0.0))
        if abs(base) > 1e-9:
            degradation[key] = round((stressed - base) / abs(base), 6)
        else:
            degradation[key] = 0.0

    # Pass/fail: PnL must not improve under stress.
    pnl_change = degradation.get("total_pnl", 0.0)
    if baseline_metrics.get("total_trades", 0) == 0:
        passed = True  # No trades → trivially passes.
        warnings.append("No baseline trades — stress test is vacuously passed.")
    else:
        passed = pnl_change <= 1e-9  # PnL must not increase.

    return StressTestResult(
        test_name=test_name,
        passed=passed,
        baseline_metrics=baseline_metrics,
        stressed_metrics=stressed_metrics,
        degradation=degradation,
        assumptions=assumptions,
        warnings=warnings,
        threshold=threshold,
    )
