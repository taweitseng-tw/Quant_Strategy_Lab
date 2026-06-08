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

import numpy as np
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


def stress_remove_best_n_trades(
    baseline: BacktestResult,
    *,
    n: int = 3,
    degradation_threshold: float = 0.30,
) -> StressTestResult:
    """Remove the top *n* best-performing trades (by PnL) and recompute metrics.

    This is a worst-case sensitivity check: if a strategy only passes because
    of 1-2 lucky outlier trades, this test should flag it.

    Parameters
    ----------
    baseline : BacktestResult
        Baseline IS backtest result containing a trade list.
    n : int
        Number of best trades to remove. Must be a non-negative int.
    degradation_threshold : float
        Maximum allowed PnL loss ratio before failing.
        ``pnl_loss_ratio = (base_pnl - stressed_pnl) / abs(base_pnl)``.
        Must be non-negative.

    Returns
    -------
    StressTestResult

    Raises
    ------
    ValueError
        If *n* is not a non-negative int.
    ValueError
        If *degradation_threshold* is negative.
    """
    # -- input validation ----------------------------------------------------
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError(f"n must be a non-negative int, got {n!r}.")
    if not isinstance(degradation_threshold, (int, float)) or degradation_threshold < 0:
        raise ValueError(
            f"degradation_threshold must be a non-negative number, got {degradation_threshold!r}."
        )

    trades = baseline.trades

    # -- zero trades ---------------------------------------------------------
    if not trades:
        return StressTestResult(
            test_name="remove_best_n_trades",
            passed=True,
            baseline_metrics=baseline.metrics,
            stressed_metrics=baseline.metrics,
            degradation={},
            assumptions={"n": n, "removed_count": 0, "surviving_count": 0,
                         "total_baseline_count": 0, "pnl_loss_ratio": 0.0},
            warnings=["No trades to stress — baseline has zero trades."],
            threshold={"max_pnl_loss": degradation_threshold},
        )

    # -- sort by PnL descending, remove top n ---------------------------------
    sorted_trades = sorted(trades, key=lambda t: t.pnl, reverse=True)
    removed = min(n, len(trades))
    surviving = sorted_trades[removed:]  # a new list — no mutation

    # -- recompute metrics ----------------------------------------------------
    stressed_metrics = compute_metrics(surviving)
    base_pnl = float(baseline.metrics.get("total_pnl", 0.0))
    stressed_pnl = float(stressed_metrics.get("total_pnl", 0.0))

    # -- degradation (existing _build_result convention) ----------------------
    degradation: dict[str, float] = {}
    for key in ("total_pnl", "profit_factor", "win_rate", "avg_trade", "total_trades"):
        base = float(baseline.metrics.get(key, 0.0))
        stressed = float(stressed_metrics.get(key, 0.0))
        degradation[key] = round((stressed - base) / abs(base), 6) if abs(base) > 1e-9 else 0.0

    # -- pnl_loss_ratio (separate, positive = worse, for pass/fail) ----------
    if abs(base_pnl) > 1e-9:
        pnl_loss_ratio = (base_pnl - stressed_pnl) / abs(base_pnl)
    else:
        pnl_loss_ratio = 0.0

    # -- pass/fail ------------------------------------------------------------
    if removed >= len(trades) and len(trades) > 0:
        # All trades removed (0 < trades <= n).
        passed = False
        warnings = [
            f"Insufficient trades for remove-best-n stress test "
            f"(trades={len(trades)}, n={n})."
        ]
        insufficient = True
    elif abs(base_pnl) < 1e-9:
        passed = True
        warnings = []
        insufficient = False
    else:
        passed = pnl_loss_ratio <= degradation_threshold
        warnings = []
        insufficient = False

    assumptions = {
        "n": n,
        "removed_count": removed,
        "surviving_count": len(surviving),
        "total_baseline_count": len(trades),
        "pnl_loss_ratio": round(pnl_loss_ratio, 6),
    }
    if n == 0:
        assumptions["n_zero"] = True
    if insufficient:
        assumptions["insufficient_trades"] = True

    return StressTestResult(
        test_name="remove_best_n_trades",
        passed=passed,
        baseline_metrics=baseline.metrics,
        stressed_metrics=stressed_metrics,
        degradation=degradation,
        assumptions=assumptions,
        warnings=warnings,
        threshold={"max_pnl_loss": degradation_threshold},
    )


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


def stress_price_noise(
    baseline: "BacktestResult",
    *,
    noise_pct: float = 0.005,
    base_seed: int = 42,
    iterations: int = 50,
    strategy: "Strategy" = None,
    df: pd.DataFrame = None,
    instrument=None,
) -> StressTestResult:
    """Run a deterministic, OHLC-preserving price-noise stress test."""
    if not 0.0 <= noise_pct <= 0.05:
        raise ValueError(f"noise_pct must be in [0, 0.05], got {noise_pct}.")
    if iterations <= 0:
        raise ValueError(f"iterations must be > 0, got {iterations}.")
    if strategy is None or df is None:
        raise ValueError("strategy and df are required for price-noise stress.")

    baseline_metrics = dict(baseline.metrics)
    baseline_assumptions = dict(getattr(baseline, "assumptions", {}) or {})
    base_pnl = float(baseline_metrics.get("total_pnl", 0.0))
    base_win_rate = float(baseline_metrics.get("win_rate", 0.0))
    run_kwargs = {
        "initial_capital": baseline_assumptions.get("initial_capital", 100_000.0),
        "commission": baseline_assumptions.get("commission_per_side", 0.0),
        "slippage_ticks": baseline_assumptions.get("slippage_per_side_ticks", 0.0),
        "tick_size": baseline_assumptions.get("tick_size", 1.0),
        "point_value": baseline_assumptions.get("point_value", 1.0),
        "execution_delay_bars": baseline_assumptions.get("execution_delay_bars", 0),
    }

    metrics: list[dict] = []
    for i in range(iterations):
        perturbed = _perturb_ohlc_price_noise(df, noise_pct=noise_pct, seed=base_seed + i)
        bt = run_backtest(strategy, perturbed, instrument=instrument, **run_kwargs)
        metrics.append(dict(bt.metrics))

    pnl_values = [float(m.get("total_pnl", 0.0)) for m in metrics]
    pf_values = [float(m.get("profit_factor", 0.0)) for m in metrics]
    dd_values = [float(m.get("max_drawdown_pnl", 0.0)) for m in metrics]
    wr_values = [float(m.get("win_rate", 0.0)) for m in metrics]

    median_pnl = float(np.median(pnl_values)) if pnl_values else 0.0
    median_pf = float(np.median(pf_values)) if pf_values else 0.0
    worst_pnl = min(pnl_values) if pnl_values else 0.0
    worst_dd = min(dd_values) if dd_values else 0.0
    median_wr = float(np.median(wr_values)) if wr_values else 0.0
    win_rate_change = median_wr - base_win_rate

    warnings: list[str] = []
    degradation: dict[str, float | None] = {"win_rate_change": round(win_rate_change, 6)}
    pnl_degradation_ratio: float | None = None
    if base_pnl > 1e-9:
        pnl_degradation_ratio = median_pnl / base_pnl
        degradation["pnl_degradation_ratio"] = round(pnl_degradation_ratio, 6)
        degradation["total_pnl"] = round((median_pnl - base_pnl) / abs(base_pnl), 6)
    else:
        degradation["pnl_degradation_ratio"] = None
        degradation["total_pnl"] = None
        warnings.append("Baseline PnL is non-positive; pnl_degradation_ratio is undefined.")

    survival_flags = []
    for pnl, wr in zip(pnl_values, wr_values):
        if base_pnl > 1e-9:
            survival_flags.append((pnl / base_pnl) >= 0.8 and (wr - base_win_rate) >= -0.1)
        else:
            survival_flags.append(pnl <= base_pnl)
    survival_rate = sum(1 for flag in survival_flags if flag) / len(survival_flags)

    stressed_metrics = {
        "total_pnl": median_pnl,
        "profit_factor": median_pf,
        "max_drawdown_pnl": worst_dd,
        "win_rate": median_wr,
        "median_total_pnl": median_pnl,
        "median_profit_factor": median_pf,
        "worst_total_pnl": worst_pnl,
        "worst_max_drawdown_pnl": worst_dd,
        "survival_rate": survival_rate,
    }

    result = _build_result(
        test_name="price_noise",
        baseline_metrics=baseline_metrics,
        stressed_metrics=stressed_metrics,
        assumptions={
            "noise_pct": noise_pct,
            "base_seed": base_seed,
            "iterations": iterations,
            "method": "ohlc_preserving_gaussian_noise",
            "research_only": True,
        },
        threshold={
            "min_pnl_degradation_ratio": 0.8,
            "min_win_rate_change": -0.1,
        },
    )
    # Override _build_result's computed values with our custom logic.
    if pnl_degradation_ratio is None:
        result.passed = False
    else:
        result.passed = pnl_degradation_ratio >= 0.8 and win_rate_change >= -0.1
    result.degradation = degradation
    result.warnings = warnings
    result.warnings.append(
        "Price-noise stress test is an approximate robustness diagnostic. "
        "It does not prove live-trading robustness."
    )
    return result


def _perturb_ohlc_price_noise(
    df: pd.DataFrame,
    *,
    noise_pct: float,
    seed: int,
) -> pd.DataFrame:
    """Return an OHLC-preserving noisy copy of *df*."""
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing OHLC columns for price-noise stress: {sorted(missing)}")

    perturbed = df.copy()
    if noise_pct == 0:
        return perturbed

    rng = np.random.default_rng(seed)
    body_noise = np.clip(rng.normal(0.0, noise_pct, size=(len(df), 2)), -0.20, 0.20)
    wick_noise = np.clip(rng.normal(0.0, noise_pct, size=(len(df), 2)), -0.95, 5.00)

    original_open = df["open"].to_numpy(dtype=float)
    original_high = df["high"].to_numpy(dtype=float)
    original_low = df["low"].to_numpy(dtype=float)
    original_close = df["close"].to_numpy(dtype=float)

    open_noisy = original_open * (1.0 + body_noise[:, 0])
    close_noisy = original_close * (1.0 + body_noise[:, 1])
    upper_wick = np.maximum(0.0, original_high - np.maximum(original_open, original_close))
    lower_wick = np.maximum(0.0, np.minimum(original_open, original_close) - original_low)

    high_noisy = np.maximum(open_noisy, close_noisy) + upper_wick * (1.0 + wick_noise[:, 0])
    low_noisy = np.minimum(open_noisy, close_noisy) - lower_wick * (1.0 + wick_noise[:, 1])

    perturbed["open"] = open_noisy
    perturbed["high"] = high_noisy
    perturbed["low"] = low_noisy
    perturbed["close"] = close_noisy
    return perturbed


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
