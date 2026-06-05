"""Monte Carlo simulation engine — repeated randomized robustness checks.

Orchestrates N iterations of stress scenarios and summarises metric
distributions with percentiles.  Reuses :mod:`validation_engine.stress_test`
functions where possible; does not duplicate stress logic.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from core.models.backtest_result import BacktestResult
from core.models.strategy import Strategy
from backtest_engine.runner import run_backtest  # type: ignore[import-untyped]
from validation_engine.stress_test import stress_random_missed_trades


# ---------------------------------------------------------------------------
# Monte Carlo result model
# ---------------------------------------------------------------------------


@dataclass
class MonteCarloResult:
    """Structured output of a Monte Carlo simulation."""

    test_name: str
    iterations: int
    baseline_metrics: dict = field(default_factory=dict)
    percentile_summary: dict = field(default_factory=dict)
    all_metrics: list[dict] = field(default_factory=list)
    worst_case: dict = field(default_factory=dict)
    assumptions: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    percentiles_used: tuple[float, ...] = field(default_factory=lambda: (5.0, 25.0, 50.0, 75.0, 95.0))
    stability_score: float | None = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_missed_trade_monte_carlo(
    baseline: BacktestResult,
    *,
    iterations: int = 100,
    miss_probability: float = 0.1,
    base_seed: int = 42,
    percentiles: tuple[float, ...] = (5.0, 25.0, 50.0, 75.0, 95.0),
) -> MonteCarloResult:
    """Run *iterations* random-missed-trade simulations.

    Each iteration calls :func:`stress_random_missed_trades` with a
    deterministic seed ``base_seed + i``.  Metrics from all runs are
    collected and summarised with percentiles.

    Parameters
    ----------
    baseline : BacktestResult
    iterations : int
        Number of Monte Carlo runs.
    miss_probability : float
        Probability [0, 1] of missing any given trade.
    base_seed : int
        Seed for iteration 0; iteration *i* uses ``base_seed + i``.

    Returns
    -------
    MonteCarloResult
    """
    if baseline.metrics.get("total_trades", 0) == 0:
        return MonteCarloResult(
            test_name="missed_trade_mc",
            iterations=iterations,
            baseline_metrics=baseline.metrics,
            warnings=["Baseline has zero trades — Monte Carlo is vacuously empty."],
        )

    metrics: list[dict] = []
    for i in range(iterations):
        result = stress_random_missed_trades(
            baseline,
            miss_probability=miss_probability,
            seed=base_seed + i,
        )
        metrics.append(dict(result.stressed_metrics))

    return _build_mc_result(
        test_name="missed_trade_mc",
        iterations=iterations,
        baseline_metrics=baseline.metrics,
        all_metrics=metrics,
        assumptions={
            "miss_probability": miss_probability,
            "base_seed": base_seed,
            "method": "random_missed_trades",
        },
        percentiles=percentiles,
    )


def run_slippage_monte_carlo(
    strategy: Strategy,
    df: pd.DataFrame,
    baseline: BacktestResult,
    *,
    iterations: int = 100,
    base_slippage_ticks: float = 1.0,
    perturbation_pct: float = 0.2,
    base_seed: int = 42,
    instrument=None,
    percentiles: tuple[float, ...] = (5.0, 25.0, 50.0, 75.0, 95.0),
) -> MonteCarloResult:
    """Run *iterations* backtests with randomly perturbed slippage.

    Each iteration draws slippage from a uniform distribution:
    ``slippage = base_slippage_ticks × (1 ± perturbation_pct)``.
    The draw is deterministic via ``base_seed + i``.

    Parameters
    ----------
    strategy : Strategy
    df : DataFrame
    baseline : BacktestResult
    iterations : int
    base_slippage_ticks : float
        Baseline per-side slippage in ticks.
    perturbation_pct : float
        Fractional perturbation, e.g. 0.2 = ±20 %.
    base_seed : int
    instrument : InstrumentProfile or None

    Returns
    -------
    MonteCarloResult
    """
    metrics: list[dict] = []
    for i in range(iterations):
        rng = random.Random(base_seed + i)
        factor = 1.0 + rng.uniform(-perturbation_pct, perturbation_pct)
        slip = max(0.0, base_slippage_ticks * factor)

        bt = run_backtest(strategy, df, slippage_ticks=slip, instrument=instrument)
        metrics.append(dict(bt.metrics))

    return _build_mc_result(
        test_name="slippage_perturbation_mc",
        iterations=iterations,
        baseline_metrics=baseline.metrics,
        all_metrics=metrics,
        assumptions={
            "base_slippage_ticks": base_slippage_ticks,
            "perturbation_pct": perturbation_pct,
            "base_seed": base_seed,
            "method": "random_slippage_perturbation",
        },
        percentiles=percentiles,
    )


def run_combined_monte_carlo(
    strategy: Strategy,
    df: pd.DataFrame,
    baseline: BacktestResult,
    *,
    iterations: int = 100,
    base_slippage_ticks: float = 1.0,
    perturbation_pct: float = 0.2,
    miss_probability: float = 0.1,
    base_seed: int = 42,
    instrument=None,
    percentiles: tuple[float, ...] = (5.0, 25.0, 50.0, 75.0, 95.0),
) -> MonteCarloResult:
    """Run *iterations* combined random-slippage and random-missed-trade simulations.

    Each iteration:
    1. Draws slippage perturbation deterministically using ``base_seed + i``.
    2. Re-runs the backtest with the perturbed slippage.
    3. Applies random missed trades to that iteration's result using ``base_seed + i``.

    Parameters
    ----------
    strategy : Strategy
    df : DataFrame
    baseline : BacktestResult
    iterations : int
    base_slippage_ticks : float
    perturbation_pct : float
    miss_probability : float
    base_seed : int
    instrument : InstrumentProfile or None
    percentiles : tuple[float, ...]

    Returns
    -------
    MonteCarloResult
    """
    miss_probability = max(0.0, min(1.0, float(miss_probability)))
    perturbation_pct = max(0.0, float(perturbation_pct))
    
    metrics: list[dict] = []
    for i in range(iterations):
        # 1. Slippage perturbation
        rng = random.Random(base_seed + i)
        factor = 1.0 + rng.uniform(-perturbation_pct, perturbation_pct)
        slip = max(0.0, base_slippage_ticks * factor)

        # 2. Re-run backtest
        bt = run_backtest(strategy, df, slippage_ticks=slip, instrument=instrument)

        # 3. Random missed trades (stress_random_missed_trades does NOT mutate bt)
        st = stress_random_missed_trades(bt, miss_probability=miss_probability, seed=base_seed + i)
        metrics.append(dict(st.stressed_metrics))

    return _build_mc_result(
        test_name="combined_slippage_missed_trades_mc",
        iterations=iterations,
        baseline_metrics=baseline.metrics,
        all_metrics=metrics,
        assumptions={
            "base_slippage_ticks": base_slippage_ticks,
            "perturbation_pct": perturbation_pct,
            "miss_probability": miss_probability,
            "base_seed": base_seed,
            "method": "combined_slippage_missed_trades",
        },
        percentiles=percentiles,
    )



# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


_METRIC_KEYS = (
    "total_trades", "total_pnl", "profit_factor",
    "max_drawdown_pnl", "win_rate", "avg_trade",
)


def _build_mc_result(
    test_name: str,
    iterations: int,
    baseline_metrics: dict,
    all_metrics: list[dict],
    assumptions: dict,
    percentiles: tuple[float, ...] = (5.0, 25.0, 50.0, 75.0, 95.0),
) -> MonteCarloResult:
    if not all_metrics:
        return MonteCarloResult(
            test_name=test_name,
            iterations=iterations,
            baseline_metrics=baseline_metrics,
            assumptions=assumptions,
            warnings=["No metrics collected from Monte Carlo runs."],
        )

    if not percentiles:
        percentiles = (5.0, 25.0, 50.0, 75.0, 95.0)

    for p in percentiles:
        if p < 0.0 or p > 100.0:
            raise ValueError(f"Percentile {p} is out of bounds [0, 100].")

    # Build percentile summary per metric.
    percentile_summary: dict[str, dict[str, float]] = {}
    
    # Pre-sort and deduplicate percentiles for safe min/max extraction
    sorted_p = sorted(set(percentiles))
    min_p, max_p = sorted_p[0], sorted_p[-1]

    for key in _METRIC_KEYS:
        values = [float(m.get(key, 0.0)) for m in all_metrics]
        arr = np.array(values)
        percentile_summary[key] = {
            f"p{int(p) if p.is_integer() else p}": float(np.percentile(arr, p))
            for p in sorted_p
        }

    # Worst case = lowest percentile for PnL/win-rate, highest for drawdown.
    worst_case: dict[str, float] = {}
    for key in _METRIC_KEYS:
        if key == "max_drawdown_pnl":
            worst_case[key] = percentile_summary[key][f"p{int(max_p) if max_p.is_integer() else max_p}"]
        else:
            worst_case[key] = percentile_summary[key][f"p{int(min_p) if min_p.is_integer() else min_p}"]

    # Calculate stability score based on total_pnl
    # lowest percentile / abs(p50). If p50 == 0 or not found, None.
    stability_score = None
    pnl_summary = percentile_summary.get("total_pnl", {})
    p50_key = f"p{int(50.0)}" if 50.0 in sorted_p else None
    
    if p50_key and p50_key in pnl_summary:
        p50_val = pnl_summary[p50_key]
        if abs(p50_val) > 1e-9:
            min_p_key = f"p{int(min_p) if min_p.is_integer() else min_p}"
            p_low_val = pnl_summary[min_p_key]
            stability_score = p_low_val / abs(p50_val)

    return MonteCarloResult(
        test_name=test_name,
        iterations=iterations,
        baseline_metrics=baseline_metrics,
        percentile_summary=percentile_summary,
        all_metrics=all_metrics,
        worst_case=worst_case,
        assumptions=assumptions,
        percentiles_used=tuple(sorted_p),
        stability_score=stability_score,
    )
