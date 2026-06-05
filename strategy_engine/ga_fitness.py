"""GA fitness adapter — bridges the generic GA core to backtest/validation scoring.

The adapter wraps backtest, ranking, elimination, and optional walk-forward
into a single :data:`FitnessFunction` callable that the GA engine consumes.

All scoring is **deterministic** for a given DataFrame, strategy, and config.
No validation pipeline is hardwired into the GA core — this module is the
single integration point.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pandas as pd

from core.models.strategy import Strategy
from backtest_engine.runner import run_backtest
from strategy_engine.ranking import compute_fitness, DEFAULT_WEIGHTS
from strategy_engine.ga import FitnessFunction
from validation_engine.elimination import EliminationConfig, evaluate_elimination
from validation_engine.walk_forward import walk_forward
from backtest_engine.runner import IndicatorCache


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class GAFitnessConfig:
    """Scoring knobs for the GA fitness adapter.

    All fields are optional — defaults produce a fast, backtest-only scoring
    function suitable for prototype GA runs.
    """

    # Dimension weights forwarded to :func:`strategy_engine.ranking.compute_fitness`.
    fitness_weights: dict | None = None

    # ── Elimination ─────────────────────────────────────────────────────────
    use_elimination: bool = True
    elimination_config: EliminationConfig | None = None
    # Factor applied to the base score when a strategy is eliminated (0 < x < 1).
    elimination_penalty: float = 0.30

    # ── Walk-forward ────────────────────────────────────────────────────────
    use_walk_forward: bool = False
    wf_train_bars: int = 100
    wf_test_bars: int = 50
    # Maximum bonus a strategy can earn from walk-forward pass rate.
    wf_bonus_max: float = 0.15


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def make_fitness_adapter(
    df: pd.DataFrame,
    config: GAFitnessConfig | None = None,
    *,
    instrument=None,
    **backtest_kwargs,
) -> FitnessFunction:
    """Create a deterministic fitness function for GA evaluation.

    The returned callable scores a :class:`Strategy` by running a backtest
    on *df*, computing multi-dimensional fitness, then optionally applying
    elimination penalties and walk-forward bonuses.

    Parameters
    ----------
    df : DataFrame
        Normalized OHLCV data used for all backtests.
    config : GAFitnessConfig or None
    instrument : InstrumentProfile or None
    **backtest_kwargs
        Forwarded to :func:`run_backtest` (commission, slippage_ticks, …).

    Returns
    -------
    FitnessFunction
        ``(Strategy) -> float`` — higher is better.  Score is roughly in
        [0, 1] but can exceed 1.0 for strong strategies.

    Notes
    -----
    - The adapter is **not** a service — it lives in ``strategy_engine/``
      because it is an engine-level scoring bridge, not a UI orchestration.
    - The GA core (:mod:`strategy_engine.ga`) remains unaware of backtest
      or validation internals — it only sees the returned callable.
    """
    cfg = config or GAFitnessConfig()
    weights = cfg.fitness_weights or DEFAULT_WEIGHTS
    elim_cfg = cfg.elimination_config or EliminationConfig(
        min_total_pnl=0.0,
        min_profit_factor=1.0,
        min_trade_count=5,
    )

    # Precompile WF parameters so we don't recompute config each call.
    wf_enabled = cfg.use_walk_forward
    wf_train = cfg.wf_train_bars
    wf_test = cfg.wf_test_bars
    wf_bonus = cfg.wf_bonus_max
    elim_enabled = cfg.use_elimination
    elim_penalty = cfg.elimination_penalty

    # Create Population-Level Cache
    cache = IndicatorCache(df)

    def _score(strategy: Strategy) -> float:
        """Score a single strategy."""
        # ── 1. Backtest ─────────────────────────────────────────────────────
        bt = run_backtest(strategy, df, instrument=instrument, indicator_cache=cache, **backtest_kwargs)
        metrics = bt.metrics

        # ── 2. Base fitness ─────────────────────────────────────────────────
        base = compute_fitness(metrics, weights)

        # ── 3. Elimination penalty ──────────────────────────────────────────
        if elim_enabled:
            elim = evaluate_elimination(metrics, elim_cfg)
            if not elim.passed:
                base *= elim_penalty

        # ── 4. Walk-forward bonus ───────────────────────────────────────────
        if wf_enabled:
            wf = walk_forward(
                strategy,
                df,
                train_bars=wf_train,
                test_bars=wf_test,
                instrument=instrument,
                **backtest_kwargs,
            )
            if wf.window_count > 0:
                base += wf_bonus * wf.pass_rate

        return base

    return _score
