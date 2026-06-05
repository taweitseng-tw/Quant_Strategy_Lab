"""GA search service — orchestrates GA runs through the service layer.

Provides :func:`run_ga_search` which wires together the GA engine
(:mod:`strategy_engine.ga`) and the fitness adapter
(:mod:`strategy_engine.ga_fitness`) into a single deterministic end-to-end
call suitable for UI or batch consumers.

No GUI imports.  No backtest/validation logic — all scoring is
delegated to the fitness adapter and the engine core.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

import pandas as pd

from core.models.strategy import Strategy
from core.models.instrument import InstrumentProfile
from strategy_engine.ga import (
    GAConfig,
    GAResult,
    create_initial_population,
    run_ga,
)
from strategy_engine.ga_fitness import GAFitnessConfig, make_fitness_adapter


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class GASearchConfig:
    """Configuration for a service-level GA search run.

    Wraps both :class:`GAConfig` (engine) and :class:`GAFitnessConfig`
    (scoring) behind a single config surface so callers don't have to
    assemble two objects manually.

    Defaults are intentionally small and fast for prototype/test usage.
    """

    # GA engine parameters
    population_size: int = 10
    elite_count: int = 2
    tournament_size: int = 3
    crossover_prob: float = 0.85
    mutation_prob: float = 0.20
    mutation_strength: float = 2.0
    max_generations: int = 3
    base_seed: int = 42

    # Fitness adapter parameters
    use_elimination: bool = True
    elimination_penalty: float = 0.30
    use_walk_forward: bool = False
    wf_train_bars: int = 100
    wf_test_bars: int = 50
    wf_bonus_max: float = 0.15
    fitness_weights: dict | None = None

    # MTF parameters
    allowed_timeframes: tuple[int, ...] = ()
    mtf_probability: float = 0.0

    def to_ga_config(self) -> GAConfig:
        """Build the engine-level GAConfig from this service config."""
        return GAConfig(
            population_size=self.population_size,
            elite_count=self.elite_count,
            tournament_size=self.tournament_size,
            crossover_prob=self.crossover_prob,
            mutation_prob=self.mutation_prob,
            mutation_strength=self.mutation_strength,
            max_generations=self.max_generations,
            base_seed=self.base_seed,
            allowed_timeframes=self.allowed_timeframes,
            mtf_probability=self.mtf_probability,
        )

    def to_fitness_config(self) -> GAFitnessConfig:
        """Build the fitness adapter config from this service config."""
        return GAFitnessConfig(
            fitness_weights=self.fitness_weights,
            use_elimination=self.use_elimination,
            elimination_penalty=self.elimination_penalty,
            use_walk_forward=self.use_walk_forward,
            wf_train_bars=self.wf_train_bars,
            wf_test_bars=self.wf_test_bars,
            wf_bonus_max=self.wf_bonus_max,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serializable snapshot for provenance."""
        d = asdict(self)
        return d


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass
class GASearchResult:
    """Structured output of a service-level GA search run."""

    best_strategy: Strategy
    best_score: float
    generation_count: int
    final_population_size: int
    generation_best_scores: list[float] = field(default_factory=list)
    generation_avg_scores: list[float] = field(default_factory=list)
    config_snapshot: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_ga_search(
    df: pd.DataFrame,
    config: GASearchConfig | None = None,
    *,
    instrument: InstrumentProfile | None = None,
    **backtest_kwargs,
) -> GASearchResult:
    """Run a complete GA search and return a structured summary.

    Parameters
    ----------
    df : DataFrame
        Normalized OHLCV data for fitness evaluation.
    config : GASearchConfig or None
        Defaults to :class:`GASearchConfig()` with fast prototype settings.
    instrument : InstrumentProfile or None
        Forwarded to the fitness adapter for point-value / cost scaling.
    **backtest_kwargs
        Forwarded to the backtest runner (commission, slippage_ticks, …).

    Returns
    -------
    GASearchResult
        Deterministic summary including the best strategy found, per-generation
        tracking, and a config snapshot for provenance.
    """
    cfg = config or GASearchConfig()
    ga_cfg = cfg.to_ga_config()
    fitness_cfg = cfg.to_fitness_config()

    # ── 1. Build fitness function ───────────────────────────────────────────
    fitness_fn = make_fitness_adapter(
        df,
        fitness_cfg,
        instrument=instrument,
        **backtest_kwargs,
    )

    # ── 2. Create initial population ────────────────────────────────────────
    initial_pop = create_initial_population(
        ga_cfg.population_size, ga_cfg.base_seed, ga_cfg,
    )

    # ── 3. Run GA ───────────────────────────────────────────────────────────
    ga_result: GAResult = run_ga(initial_pop, fitness_fn, config=ga_cfg)

    # ── 4. Extract per-generation tracking ──────────────────────────────────
    gen_best: list[float] = [g.best_score for g in ga_result.generations]
    gen_avg: list[float] = [g.average_score for g in ga_result.generations]

    return GASearchResult(
        best_strategy=ga_result.best_strategy,
        best_score=ga_result.best_score,
        generation_count=len(ga_result.generations),
        final_population_size=len(ga_result.final_population),
        generation_best_scores=gen_best,
        generation_avg_scores=gen_avg,
        config_snapshot=cfg.to_dict(),
    )
