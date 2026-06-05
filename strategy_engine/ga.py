"""Genetic Algorithm primitives for evolving Strategy objects.

This module intentionally contains only engine-level GA mechanics:
population creation, selection, crossover, mutation, and generation loops.
It does not run backtests or validation internally; callers provide a
fitness function so evaluation policy stays outside the GA core.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Callable, Sequence

from core.models.strategy import Condition, Strategy, StrategyBlock
from strategy_engine.generator import (
    DEFAULT_ATR_PERIOD_RANGE,
    DEFAULT_ATR_THRESHOLD_RANGE,
    DEFAULT_MACD_FAST_RANGE,
    DEFAULT_MACD_SIGNAL_RANGE,
    DEFAULT_MACD_SLOW_RANGE,
    DEFAULT_RSI_PERIOD_RANGE,
    DEFAULT_RSI_THRESHOLD_RANGE,
    DEFAULT_SMA_PERIOD_RANGE,
    generate_strategies,
)


FitnessFunction = Callable[[Strategy], float]


@dataclass
class GAConfig:
    """Configuration for deterministic GA operations."""

    population_size: int = 30
    elite_count: int = 2
    tournament_size: int = 3
    crossover_prob: float = 0.85
    mutation_prob: float = 0.20
    mutation_strength: float = 2.0
    max_generations: int = 20
    base_seed: int = 42

    sma_period_range: tuple[int, int] = DEFAULT_SMA_PERIOD_RANGE
    rsi_period_range: tuple[int, int] = DEFAULT_RSI_PERIOD_RANGE
    rsi_threshold_range: tuple[int, int] = DEFAULT_RSI_THRESHOLD_RANGE
    atr_period_range: tuple[int, int] = DEFAULT_ATR_PERIOD_RANGE
    atr_threshold_range: tuple[float, float] = DEFAULT_ATR_THRESHOLD_RANGE
    macd_fast_range: tuple[int, int] = DEFAULT_MACD_FAST_RANGE
    macd_slow_range: tuple[int, int] = DEFAULT_MACD_SLOW_RANGE
    macd_signal_range: tuple[int, int] = DEFAULT_MACD_SIGNAL_RANGE

    allowed_timeframes: tuple[int, ...] = ()
    mtf_probability: float = 0.0


@dataclass
class GAGenerationResult:
    """Snapshot of one evaluated generation."""

    generation: int
    population: list[Strategy]
    scores: list[float]
    best_strategy: Strategy
    best_score: float
    average_score: float


@dataclass
class GAResult:
    """Output of a full GA run."""

    final_population: list[Strategy]
    final_scores: list[float]
    best_strategy: Strategy
    best_score: float
    generations: list[GAGenerationResult] = field(default_factory=list)
    config: GAConfig = field(default_factory=GAConfig)


def create_initial_population(size: int, seed: int, config: GAConfig | None = None) -> list[Strategy]:
    """Create an initial deterministic strategy population.

    Delegates strategy construction to the existing random strategy generator
    so the GA uses the same four-block Strategy representation as the rest of
    the system.
    """
    if size <= 0:
        raise ValueError("population size must be positive")
    cfg = config or GAConfig(population_size=size, base_seed=seed)
    generated = generate_strategies(
        count=size,
        seed=seed,
        sma_period_range=cfg.sma_period_range,
        rsi_period_range=cfg.rsi_period_range,
        rsi_threshold_range=cfg.rsi_threshold_range,
        atr_period_range=cfg.atr_period_range,
        atr_threshold_range=cfg.atr_threshold_range,
        macd_fast_range=cfg.macd_fast_range,
        macd_slow_range=cfg.macd_slow_range,
        macd_signal_range=cfg.macd_signal_range,
        allowed_timeframes=cfg.allowed_timeframes,
        mtf_probability=cfg.mtf_probability,
    )
    return [copy.deepcopy(entry["strategy"]) for entry in generated]


def select_parents(
    population: Sequence[Strategy],
    scores: Sequence[float],
    n: int,
    *,
    tournament_size: int = 3,
    seed: int = 42,
) -> list[Strategy]:
    """Select *n* parents using deterministic tournament selection."""
    _validate_population_scores(population, scores)
    if n <= 0:
        return []

    rng = random.Random(seed)
    tournament_n = max(1, min(tournament_size, len(population)))
    selected: list[Strategy] = []

    for _ in range(n):
        candidates = rng.sample(range(len(population)), k=tournament_n)
        best_idx = max(candidates, key=lambda idx: (scores[idx], -idx))
        selected.append(copy.deepcopy(population[best_idx]))

    return selected


def crossover(parent_a: Strategy, parent_b: Strategy, *, seed: int = 42) -> Strategy:
    """Create a child by choosing each of the four blocks from either parent."""
    rng = random.Random(seed)
    child = Strategy(
        name=f"ga_child_{seed}",
        long_entry=copy.deepcopy(rng.choice([parent_a.long_entry, parent_b.long_entry])),
        long_exit=copy.deepcopy(rng.choice([parent_a.long_exit, parent_b.long_exit])),
        short_entry=copy.deepcopy(rng.choice([parent_a.short_entry, parent_b.short_entry])),
        short_exit=copy.deepcopy(rng.choice([parent_a.short_exit, parent_b.short_exit])),
    )
    return child


def mutate(
    strategy: Strategy,
    *,
    prob: float = 0.20,
    strength: float = 2.0,
    seed: int = 42,
    config: GAConfig | None = None,
) -> Strategy:
    """Return a mutated copy of *strategy*.

    Mutation only perturbs existing condition parameters. It preserves block
    structure, indicator type, and comparison operator.
    """
    cfg = config or GAConfig()
    rng = random.Random(seed)
    mutated = copy.deepcopy(strategy)
    mutated.name = f"{strategy.name}_mut_{seed}"

    for block in _blocks(mutated):
        for cond in block.conditions:
            if rng.random() <= prob:
                _mutate_condition(cond, rng, strength, cfg)

    return mutated


def evolve_one_generation(
    population: Sequence[Strategy],
    scores: Sequence[float],
    generation: int,
    config: GAConfig | None = None,
) -> list[Strategy]:
    """Produce the next generation while preserving top elites."""
    cfg = config or GAConfig(population_size=len(population))
    _validate_population_scores(population, scores)
    if cfg.population_size <= 0:
        raise ValueError("population_size must be positive")

    ranked_indices = sorted(range(len(population)), key=lambda idx: scores[idx], reverse=True)
    elite_count = max(0, min(cfg.elite_count, cfg.population_size, len(population)))
    next_population = [copy.deepcopy(population[idx]) for idx in ranked_indices[:elite_count]]

    child_seed_base = cfg.base_seed + generation * 10_000
    parent_count = max(2, (cfg.population_size - elite_count) * 2)
    parents = select_parents(
        population,
        scores,
        parent_count,
        tournament_size=cfg.tournament_size,
        seed=child_seed_base,
    )

    pair_idx = 0
    while len(next_population) < cfg.population_size:
        p1 = parents[pair_idx % len(parents)]
        p2 = parents[(pair_idx + 1) % len(parents)]
        rng = random.Random(child_seed_base + pair_idx)
        if rng.random() <= cfg.crossover_prob:
            child = crossover(p1, p2, seed=child_seed_base + pair_idx)
        else:
            child = copy.deepcopy(p1)
            child.name = f"ga_clone_{generation}_{pair_idx}"
        child = mutate(
            child,
            prob=cfg.mutation_prob,
            strength=cfg.mutation_strength,
            seed=child_seed_base + 100_000 + pair_idx,
            config=cfg,
        )
        child.name = f"ga_g{generation:03d}_{len(next_population):04d}"
        next_population.append(child)
        pair_idx += 2

    return next_population


def run_ga(
    initial_population: Sequence[Strategy] | None,
    fitness_fn: FitnessFunction,
    config: GAConfig | None = None,
) -> GAResult:
    """Run a deterministic GA loop with caller-provided fitness function."""
    cfg = config or GAConfig()
    if cfg.population_size <= 0:
        raise ValueError("population_size must be positive")
    if cfg.max_generations <= 0:
        raise ValueError("max_generations must be positive")

    population = (
        [copy.deepcopy(s) for s in initial_population]
        if initial_population is not None
        else create_initial_population(cfg.population_size, cfg.base_seed, cfg)
    )
    if len(population) != cfg.population_size:
        raise ValueError("initial_population length must match config.population_size")

    generations: list[GAGenerationResult] = []

    for generation in range(cfg.max_generations):
        scores = [float(fitness_fn(strategy)) for strategy in population]
        snapshot = _generation_snapshot(generation, population, scores)
        generations.append(snapshot)
        if generation < cfg.max_generations - 1:
            population = evolve_one_generation(population, scores, generation + 1, cfg)

    final_scores = [float(fitness_fn(strategy)) for strategy in population]
    best_idx = max(range(len(population)), key=lambda idx: final_scores[idx])
    return GAResult(
        final_population=[copy.deepcopy(s) for s in population],
        final_scores=list(final_scores),
        best_strategy=copy.deepcopy(population[best_idx]),
        best_score=final_scores[best_idx],
        generations=generations,
        config=cfg,
    )


def _generation_snapshot(
    generation: int,
    population: Sequence[Strategy],
    scores: Sequence[float],
) -> GAGenerationResult:
    best_idx = max(range(len(population)), key=lambda idx: scores[idx])
    avg = sum(float(score) for score in scores) / len(scores)
    return GAGenerationResult(
        generation=generation,
        population=[copy.deepcopy(s) for s in population],
        scores=list(scores),
        best_strategy=copy.deepcopy(population[best_idx]),
        best_score=float(scores[best_idx]),
        average_score=avg,
    )


def _mutate_condition(cond: Condition, rng: random.Random, strength: float, cfg: GAConfig) -> None:
    ind = cond.indicator.upper()
    if ind == "SMA":
        cond.params["period"] = _mutate_int(cond.params.get("period", 20), cfg.sma_period_range, rng, strength)
    elif ind == "RSI":
        cond.params["period"] = _mutate_int(cond.params.get("period", 14), cfg.rsi_period_range, rng, strength)
        cond.right = float(_mutate_int(int(float(cond.right)), cfg.rsi_threshold_range, rng, strength))
    elif ind == "ATR":
        cond.params["period"] = _mutate_int(cond.params.get("period", 14), cfg.atr_period_range, rng, strength)
        cond.right = _mutate_float(float(cond.right), cfg.atr_threshold_range, rng, strength)
    elif ind == "MACD":
        cond.params["fast"] = _mutate_int(cond.params.get("fast", 12), cfg.macd_fast_range, rng, strength)
        cond.params["slow"] = _mutate_int(cond.params.get("slow", 26), cfg.macd_slow_range, rng, strength)
        cond.params["signal"] = _mutate_int(cond.params.get("signal", 9), cfg.macd_signal_range, rng, strength)
        _repair_macd(cond, cfg)


def _mutate_int(value: int, bounds: tuple[int, int], rng: random.Random, strength: float) -> int:
    lo, hi = bounds
    delta_max = max(1, int(round(strength)))
    return int(_clamp(int(value) + rng.randint(-delta_max, delta_max), lo, hi))


def _mutate_float(value: float, bounds: tuple[float, float], rng: random.Random, strength: float) -> float:
    lo, hi = bounds
    return round(float(_clamp(value + rng.uniform(-strength, strength), lo, hi)), 4)


def _repair_macd(cond: Condition, cfg: GAConfig) -> None:
    fast = int(cond.params["fast"])
    slow = int(cond.params["slow"])
    if fast >= slow:
        fast = min(fast, slow - 1)
    fast = int(_clamp(fast, cfg.macd_fast_range[0], cfg.macd_fast_range[1]))
    slow = int(_clamp(slow, cfg.macd_slow_range[0], cfg.macd_slow_range[1]))
    if fast >= slow:
        fast = max(cfg.macd_fast_range[0], min(slow - 1, cfg.macd_fast_range[1]))
    cond.params["fast"] = fast
    cond.params["slow"] = slow


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _blocks(strategy: Strategy) -> list[StrategyBlock]:
    return [strategy.long_entry, strategy.long_exit, strategy.short_entry, strategy.short_exit]


def _validate_population_scores(population: Sequence[Strategy], scores: Sequence[float]) -> None:
    if not population:
        raise ValueError("population must not be empty")
    if len(population) != len(scores):
        raise ValueError("population and scores must have the same length")
