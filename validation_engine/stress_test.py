"""Basic stress test engine — re-runs or transforms backtests to measure robustness.

Supports:
  - Commission multiplier (default 2×)
  - Slippage multiplier (default 2×)
  - One-bar execution delay (shifts price data forward by 1 bar)
  - Random missed trades (deterministic seed)

All stress tests are **read-only** with respect to the baseline result.
"""

from __future__ import annotations

import copy
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
    """Simulate one-bar execution delay by instructing the engine to delay routing.

    This uses the native `execution_delay_bars=1` parameter in `run_backtest`,
    which delays the fill of an entry signal by 1 bar without shifting prices
    or indicators. This prevents future leak.
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

    if not baseline.trades:
        return StressTestResult(
            test_name="one_bar_delay",
            passed=True,
            baseline_metrics=baseline.metrics,
            stressed_metrics=baseline.metrics,
            degradation={},
            assumptions={"delay_bars": 1},
            warnings=["No trades to stress — baseline has zero trades."],
            threshold={"pnl_must_not_improve": True},
        )

    # Re-run backtest with native execution delay.
    stressed = run_backtest(strategy, df, instrument=instrument, execution_delay_bars=1)

    return _build_result(
        test_name="one_bar_delay",
        baseline_metrics=baseline.metrics,
        stressed_metrics=stressed.metrics,
        assumptions={
            "delay_bars": 1,
            "method": "engine_native_delay",
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


def stress_parameter_perturbation(
    strategy: Strategy,
    df: pd.DataFrame,
    baseline: BacktestResult,
    *,
    instrument=None,
    variants_count: int = 5,
    int_shift_range: tuple[int, int] = (-2, 2),
    float_shift_pct: float = 0.05,
    degradation_threshold: float = 0.50,
) -> StressTestResult:
    """Stress test by slightly perturbing strategy parameters and checking degradation."""

    if baseline.metrics.get("total_trades", 0) == 0:
        return StressTestResult(
            test_name="parameter_perturbation",
            passed=True,
            baseline_metrics=baseline.metrics,
            stressed_metrics=baseline.metrics,
            degradation={},
            assumptions={"variants_count": variants_count},
            warnings=["No baseline trades — stress test is vacuously passed."],
            threshold={"max_degradation": degradation_threshold},
        )

    def _perturb_int(val: int) -> int:
        shift = random.randint(int_shift_range[0], int_shift_range[1])
        # Force non-zero shift if possible, but randint is random.
        if shift == 0:
            shift = 1 if random.random() > 0.5 else -1
        return max(1, val + shift)

    def _perturb_float(val: float) -> float:
        sign = 1 if random.random() > 0.5 else -1
        return val * (1.0 + sign * float_shift_pct)

    has_params = False

    def _perturb_strategy(orig: Strategy) -> Strategy:
        nonlocal has_params
        mutated = copy.deepcopy(orig)

        # Perturb condition parameters
        for block in (mutated.long_entry, mutated.long_exit, mutated.short_entry, mutated.short_exit):
            for cond in block.conditions:
                for k, v in cond.params.items():
                    if isinstance(v, bool):
                        continue
                    if isinstance(v, int):
                        cond.params[k] = _perturb_int(v)
                        has_params = True
                    elif isinstance(v, float):
                        cond.params[k] = _perturb_float(v)
                        has_params = True

        # Perturb risk parameters
        if mutated.risk_management:
            rm = mutated.risk_management
            for field_name in ("stop_loss_ticks", "take_profit_ticks", "stop_loss_pct", "take_profit_pct"):
                v = getattr(rm, field_name)
                if v is not None:
                    if isinstance(v, int):
                        setattr(rm, field_name, _perturb_int(v))
                        has_params = True
                    elif isinstance(v, float):
                        setattr(rm, field_name, _perturb_float(v))
                        has_params = True
        return mutated

    # Check if there are params to perturb
    _perturb_strategy(strategy)
    if not has_params:
        return StressTestResult(
            test_name="parameter_perturbation",
            passed=True,
            baseline_metrics=baseline.metrics,
            stressed_metrics=baseline.metrics,
            degradation={},
            assumptions={"variants_count": variants_count},
            warnings=["No perturbable parameters found — automatic pass."],
            threshold={"max_degradation": degradation_threshold},
        )

    variant_pnls = []

    for _ in range(variants_count):
        variant_strat = _perturb_strategy(strategy)
        res = run_backtest(variant_strat, df, instrument=instrument)
        variant_pnls.append(res.metrics.get("total_pnl", 0.0))

    avg_variant_pnl = sum(variant_pnls) / len(variant_pnls)
    base_pnl = float(baseline.metrics.get("total_pnl", 0.0))

    if base_pnl > 1e-9:
        avg_degradation = (avg_variant_pnl - base_pnl) / base_pnl
    else:
        avg_degradation = 0.0

    passed = True
    if avg_variant_pnl < 0:
        passed = False
    elif avg_variant_pnl < base_pnl * (1.0 - degradation_threshold):
        passed = False

    stressed_metrics = dict(baseline.metrics)
    stressed_metrics["total_pnl"] = avg_variant_pnl

    return StressTestResult(
        test_name="parameter_perturbation",
        passed=passed,
        baseline_metrics=baseline.metrics,
        stressed_metrics=stressed_metrics,
        degradation={"total_pnl": round(avg_degradation, 6)},
        assumptions={
            "variants_count": variants_count,
            "int_shift_range": int_shift_range,
            "float_shift_pct": float_shift_pct,
            "avg_variant_pnl": avg_variant_pnl,
        },
        warnings=[],
        threshold={"max_degradation": degradation_threshold},
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
