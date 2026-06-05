"""Genetic Programming evolution loop."""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Callable, Sequence

from core.models.strategy import Strategy
from strategy_engine.gp import (
    GPLogicNode,
    generate_tree,
    crossover_tree,
    mutate_tree,
    compile_tree_to_block,
)

FitnessFunction = Callable[[Strategy], float]

@dataclass
class GPConfig:
    population_size: int = 30
    elite_count: int = 2
    tournament_size: int = 3
    crossover_prob: float = 0.85
    mutation_prob: float = 0.20
    max_generations: int = 20
    base_seed: int = 42
    max_conditions: int = 5
    allowed_timeframes: tuple[int, ...] = field(default_factory=tuple)
    mtf_probability: float = 0.0

@dataclass
class GPIndividual:
    name: str
    long_entry_tree: GPLogicNode
    long_exit_tree: GPLogicNode
    short_entry_tree: GPLogicNode
    short_exit_tree: GPLogicNode

    def compile_to_strategy(self) -> Strategy:
        return Strategy(
            name=self.name,
            long_entry=compile_tree_to_block(self.long_entry_tree),
            long_exit=compile_tree_to_block(self.long_exit_tree),
            short_entry=compile_tree_to_block(self.short_entry_tree),
            short_exit=compile_tree_to_block(self.short_exit_tree),
        )

@dataclass
class GPGenerationResult:
    generation: int
    population: list[GPIndividual]
    scores: list[float]
    best_individual: GPIndividual
    best_score: float
    average_score: float

@dataclass
class GPResult:
    final_population: list[GPIndividual]
    final_scores: list[float]
    best_individual: GPIndividual
    best_score: float
    generations: list[GPGenerationResult] = field(default_factory=list)
    config: GPConfig = field(default_factory=GPConfig)


def create_initial_gp_population(size: int, seed: int, config: GPConfig | None = None) -> list[GPIndividual]:
    if size <= 0:
        raise ValueError("population size must be positive")
    cfg = config or GPConfig(population_size=size, base_seed=seed)
    rng = random.Random(seed)
    
    population = []
    for i in range(size):
        ind = GPIndividual(
            name=f"gp_init_{seed}_{i}",
            long_entry_tree=generate_tree(rng, "entry", cfg.max_conditions, cfg),
            long_exit_tree=generate_tree(rng, "exit", cfg.max_conditions, cfg),
            short_entry_tree=generate_tree(rng, "entry", cfg.max_conditions, cfg),
            short_exit_tree=generate_tree(rng, "exit", cfg.max_conditions, cfg),
        )
        population.append(ind)
    return population

def select_gp_parents(
    population: Sequence[GPIndividual],
    scores: Sequence[float],
    n: int,
    tournament_size: int = 3,
    seed: int = 42,
) -> list[GPIndividual]:
    if not population:
        raise ValueError("population must not be empty")
    if len(population) != len(scores):
        raise ValueError("population and scores must have the same length")
    if n <= 0:
        return []

    rng = random.Random(seed)
    tournament_n = max(1, min(tournament_size, len(population)))
    selected = []

    for _ in range(n):
        candidates = rng.sample(range(len(population)), k=tournament_n)
        best_idx = max(candidates, key=lambda idx: (scores[idx], -idx))
        selected.append(copy.deepcopy(population[best_idx]))

    return selected

def crossover_individual(parent_a: GPIndividual, parent_b: GPIndividual, seed: int, config: GPConfig) -> GPIndividual:
    rng = random.Random(seed)
    return GPIndividual(
        name=f"gp_child_{seed}",
        long_entry_tree=crossover_tree(parent_a.long_entry_tree, parent_b.long_entry_tree, seed=rng.randint(0, 1000000), max_conditions=config.max_conditions, config=config),
        long_exit_tree=crossover_tree(parent_a.long_exit_tree, parent_b.long_exit_tree, seed=rng.randint(0, 1000000), max_conditions=config.max_conditions, config=config),
        short_entry_tree=crossover_tree(parent_a.short_entry_tree, parent_b.short_entry_tree, seed=rng.randint(0, 1000000), max_conditions=config.max_conditions, config=config),
        short_exit_tree=crossover_tree(parent_a.short_exit_tree, parent_b.short_exit_tree, seed=rng.randint(0, 1000000), max_conditions=config.max_conditions, config=config),
    )

def mutate_individual(ind: GPIndividual, seed: int, config: GPConfig) -> GPIndividual:
    rng = random.Random(seed)
    mutated = copy.deepcopy(ind)
    mutated.name = f"{ind.name}_mut_{seed}"
    
    mutated.long_entry_tree = mutate_tree(mutated.long_entry_tree, seed=rng.randint(0, 1000000), mutation_prob=config.mutation_prob, max_conditions=config.max_conditions, direction="entry", config=config)
    mutated.long_exit_tree = mutate_tree(mutated.long_exit_tree, seed=rng.randint(0, 1000000), mutation_prob=config.mutation_prob, max_conditions=config.max_conditions, direction="exit", config=config)
    mutated.short_entry_tree = mutate_tree(mutated.short_entry_tree, seed=rng.randint(0, 1000000), mutation_prob=config.mutation_prob, max_conditions=config.max_conditions, direction="entry", config=config)
    mutated.short_exit_tree = mutate_tree(mutated.short_exit_tree, seed=rng.randint(0, 1000000), mutation_prob=config.mutation_prob, max_conditions=config.max_conditions, direction="exit", config=config)
    
    return mutated

def score_gp_population(population: Sequence[GPIndividual], fitness_fn: FitnessFunction) -> list[float]:
    return [float(fitness_fn(ind.compile_to_strategy())) for ind in population]

def evolve_gp_one_generation(
    population: Sequence[GPIndividual],
    scores: Sequence[float],
    generation: int,
    config: GPConfig | None = None,
) -> list[GPIndividual]:
    cfg = config or GPConfig(population_size=len(population))
    if not population:
        raise ValueError("population must not be empty")
    if len(population) != len(scores):
        raise ValueError("population and scores must have the same length")
    if cfg.population_size <= 0:
        raise ValueError("population_size must be positive")

    ranked_indices = sorted(range(len(population)), key=lambda idx: scores[idx], reverse=True)
    elite_count = max(0, min(cfg.elite_count, cfg.population_size, len(population)))
    next_population = [copy.deepcopy(population[idx]) for idx in ranked_indices[:elite_count]]

    child_seed_base = cfg.base_seed + generation * 10_000
    parent_count = max(2, (cfg.population_size - elite_count) * 2)
    parents = select_gp_parents(
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
            child = crossover_individual(p1, p2, seed=child_seed_base + pair_idx, config=cfg)
        else:
            child = copy.deepcopy(p1)
            child.name = f"gp_clone_{generation}_{pair_idx}"
            
        child = mutate_individual(child, seed=child_seed_base + 100_000 + pair_idx, config=cfg)
        child.name = f"gp_g{generation:03d}_{len(next_population):04d}"
        
        next_population.append(child)
        pair_idx += 2

    return next_population

def run_gp(
    initial_population: Sequence[GPIndividual] | None,
    fitness_fn: FitnessFunction,
    config: GPConfig | None = None,
) -> GPResult:
    cfg = config or GPConfig()
    if cfg.population_size <= 0:
        raise ValueError("population_size must be positive")
    if cfg.max_generations < 0:
        raise ValueError("max_generations must be non-negative")

    population = (
        [copy.deepcopy(ind) for ind in initial_population]
        if initial_population is not None
        else create_initial_gp_population(cfg.population_size, cfg.base_seed, cfg)
    )
    if len(population) != cfg.population_size:
        raise ValueError("initial_population length must match config.population_size")

    generations = []

    for generation in range(cfg.max_generations):
        scores = score_gp_population(population, fitness_fn)
        
        best_idx = max(range(len(population)), key=lambda idx: scores[idx])
        avg = sum(scores) / len(scores)
        
        snapshot = GPGenerationResult(
            generation=generation,
            population=[copy.deepcopy(ind) for ind in population],
            scores=list(scores),
            best_individual=copy.deepcopy(population[best_idx]),
            best_score=scores[best_idx],
            average_score=avg,
        )
        generations.append(snapshot)
        
        if generation < cfg.max_generations - 1:
            population = evolve_gp_one_generation(population, scores, generation + 1, cfg)

    final_scores = score_gp_population(population, fitness_fn)
    best_idx = max(range(len(population)), key=lambda idx: final_scores[idx])
    
    return GPResult(
        final_population=[copy.deepcopy(ind) for ind in population],
        final_scores=list(final_scores),
        best_individual=copy.deepcopy(population[best_idx]),
        best_score=final_scores[best_idx],
        generations=generations,
        config=cfg,
    )
