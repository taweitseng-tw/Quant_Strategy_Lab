"""Tests for GP population evolution loop."""

import random
from dataclasses import asdict
import pandas as pd
import numpy as np

from strategy_engine.gp_evolution import (
    GPConfig,
    create_initial_gp_population,
    score_gp_population,
    select_gp_parents,
    evolve_gp_one_generation,
    run_gp,
    GPIndividual,
)
from core.models.strategy import Strategy
from backtest_engine.runner import run_backtest

def dummy_fitness(strategy: Strategy) -> float:
    # A dummy fitness that just scores based on number of conditions to prove it works
    score = 0.0
    for block in [strategy.long_entry, strategy.long_exit, strategy.short_entry, strategy.short_exit]:
        score += len(block.conditions)
    return float(score)

def test_create_initial_gp_population_size():
    cfg = GPConfig(population_size=10)
    pop = create_initial_gp_population(10, seed=42, config=cfg)
    assert len(pop) == 10
    assert all(isinstance(ind, GPIndividual) for ind in pop)

def test_create_initial_gp_population_deterministic():
    pop1 = create_initial_gp_population(5, seed=42)
    pop2 = create_initial_gp_population(5, seed=42)
    for ind1, ind2 in zip(pop1, pop2):
        assert asdict(ind1) == asdict(ind2)

def test_create_initial_gp_population_differs_by_seed():
    pop1 = create_initial_gp_population(5, seed=1)
    pop2 = create_initial_gp_population(5, seed=2)
    assert asdict(pop1[0]) != asdict(pop2[0])

def test_score_gp_population_uses_injected_fitness_fn():
    pop = create_initial_gp_population(5, seed=42)
    scores = score_gp_population(pop, dummy_fitness)
    assert len(scores) == 5
    assert all(isinstance(s, float) for s in scores)

def test_select_gp_parents_prefers_high_scores():
    pop = create_initial_gp_population(10, seed=42)
    # Give index 7 a massive score
    scores = [1.0] * 10
    scores[7] = 1000.0
    
    # Select parents many times
    parents = select_gp_parents(pop, scores, n=20, tournament_size=3, seed=1)
    
    # Parent index 7 should be selected very frequently
    match_count = sum(1 for p in parents if asdict(p) == asdict(pop[7]))
    assert match_count > 5  # Statistical preference

def test_evolve_gp_one_generation_preserves_population_size():
    cfg = GPConfig(population_size=10, elite_count=2)
    pop = create_initial_gp_population(10, seed=42, config=cfg)
    scores = score_gp_population(pop, dummy_fitness)
    next_pop = evolve_gp_one_generation(pop, scores, generation=1, config=cfg)
    
    assert len(next_pop) == 10

def test_evolve_gp_one_generation_preserves_elite():
    cfg = GPConfig(population_size=10, elite_count=2)
    pop = create_initial_gp_population(10, seed=42, config=cfg)
    scores = [float(i) for i in range(10)]  # Index 9 is best, 8 is second best
    
    next_pop = evolve_gp_one_generation(pop, scores, generation=1, config=cfg)
    
    # Elites should be placed at the beginning of the next generation exactly as they were
    assert asdict(next_pop[0]) == asdict(pop[9])
    assert asdict(next_pop[1]) == asdict(pop[8])

def test_run_gp_returns_structured_result():
    cfg = GPConfig(population_size=5, max_generations=2)
    result = run_gp(initial_population=None, fitness_fn=dummy_fitness, config=cfg)
    
    assert len(result.generations) == 2
    assert len(result.final_population) == 5
    assert len(result.final_scores) == 5
    assert isinstance(result.best_individual, GPIndividual)
    assert isinstance(result.best_score, float)

def test_run_gp_is_deterministic():
    cfg = GPConfig(population_size=5, max_generations=2)
    res1 = run_gp(initial_population=None, fitness_fn=dummy_fitness, config=cfg)
    res2 = run_gp(initial_population=None, fitness_fn=dummy_fitness, config=cfg)
    
    assert asdict(res1.best_individual) == asdict(res2.best_individual)
    assert res1.best_score == res2.best_score

def _make_test_data(n_bars: int = 100) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="1min")
    returns = rng.normal(0.0001, 0.001, n_bars)
    close = 100.0 * np.cumprod(1.0 + returns)
    noise = rng.uniform(0.1, 1.0, n_bars)
    return pd.DataFrame({
        "datetime": times,
        "open":  close - noise * 0.5,
        "high":  close + noise,
        "low":   close - noise,
        "close": close,
        "volume": rng.integers(500, 5000, n_bars),
    })

def test_run_gp_best_strategy_is_backtestable():
    cfg = GPConfig(population_size=5, max_generations=2)
    result = run_gp(initial_population=None, fitness_fn=dummy_fitness, config=cfg)
    
    strat = result.best_individual.compile_to_strategy()
    df = _make_test_data(100)
    bt = run_backtest(strat, df)
    
    assert "total_trades" in bt.metrics

def test_gp_evolution_does_not_use_global_random_state():
    cfg = GPConfig(population_size=5, max_generations=2)
    state_before = random.getstate()
    run_gp(initial_population=None, fitness_fn=dummy_fitness, config=cfg)
    state_after = random.getstate()
    assert state_before == state_after

def test_gp_evolution_preserves_condition_contracts():
    cfg = GPConfig(population_size=10, max_generations=3, mutation_prob=1.0)
    result = run_gp(initial_population=None, fitness_fn=dummy_fitness, config=cfg)
    
    for ind in result.final_population:
        for tree in (ind.long_entry_tree, ind.long_exit_tree, ind.short_entry_tree, ind.short_exit_tree):
            for leaf in tree.children:
                cond = leaf.condition
                if cond.indicator == "MACD":
                    assert cond.params["fast"] < cond.params["slow"]
                elif cond.indicator == "SMA":
                    assert "period" in cond.params

def test_gp_evolution_module_has_no_ui_repo_or_backtest_imports():
    # Check that it didn't pull in UI or persistence by inspecting source
    with open("strategy_engine/gp_evolution.py", "r", encoding="utf-8") as f:
        content = f.read()
    assert "backtest" not in content
    assert "PySide6" not in content
    assert "sqlite" not in content.lower()

def test_gp_individual_to_strategy_has_four_valid_blocks():
    cfg = GPConfig()
    pop = create_initial_gp_population(1, seed=42, config=cfg)
    strat = pop[0].compile_to_strategy()
    assert isinstance(strat, Strategy)
    assert len(strat.long_entry.conditions) >= 1
    assert len(strat.long_exit.conditions) >= 1
    assert len(strat.short_entry.conditions) >= 1
    assert len(strat.short_exit.conditions) >= 1

def test_elite_preservation_uses_deep_copies():
    cfg = GPConfig(population_size=5, elite_count=1)
    pop = create_initial_gp_population(5, seed=42, config=cfg)
    scores = score_gp_population(pop, dummy_fitness)
    next_pop = evolve_gp_one_generation(pop, scores, generation=1, config=cfg)
    
    # next_pop[0] is the elite. It should have the same values but not be the same object
    # Find the best in original
    best_idx = max(range(len(pop)), key=lambda idx: scores[idx])
    best_original = pop[best_idx]
    
    assert next_pop[0] is not best_original
    assert next_pop[0].long_entry_tree is not best_original.long_entry_tree
    
    # The conditions inside should also be completely independent
    assert next_pop[0].long_entry_tree.children[0] is not best_original.long_entry_tree.children[0]
    assert next_pop[0].long_entry_tree.children[0].condition is not best_original.long_entry_tree.children[0].condition

def test_evolve_generation_does_not_mutate_parent_population():
    cfg = GPConfig(population_size=5)
    pop = create_initial_gp_population(5, seed=42, config=cfg)
    pop_snapshot = [asdict(ind) for ind in pop]
    
    scores = score_gp_population(pop, dummy_fitness)
    _ = evolve_gp_one_generation(pop, scores, generation=1, config=cfg)
    
    for i, ind in enumerate(pop):
        assert asdict(ind) == pop_snapshot[i]

import pytest

def test_population_size_zero_or_negative_is_handled_safely():
    with pytest.raises(ValueError, match="positive"):
        create_initial_gp_population(0, seed=42)
    with pytest.raises(ValueError, match="positive"):
        create_initial_gp_population(-5, seed=42)
        
    cfg = GPConfig(population_size=0)
    with pytest.raises(ValueError, match="empty"):
        evolve_gp_one_generation([], [], 1, cfg)
        
    with pytest.raises(ValueError, match="positive"):
        run_gp(None, dummy_fitness, cfg)

def test_elite_count_above_population_size_is_clamped_or_documented():
    cfg = GPConfig(population_size=5, elite_count=10)
    pop = create_initial_gp_population(5, seed=42, config=cfg)
    scores = score_gp_population(pop, dummy_fitness)
    next_pop = evolve_gp_one_generation(pop, scores, generation=1, config=cfg)
    
    assert len(next_pop) == 5
    # Since elite count is clamped to population size, all 5 are elites (copies)
    # Plus it handles parents generation properly.
    assert asdict(next_pop[0]) == asdict(pop[max(range(5), key=lambda i: scores[i])])

def test_tournament_size_invalid_values_are_clamped_or_documented():
    pop = create_initial_gp_population(5, seed=42)
    scores = score_gp_population(pop, dummy_fitness)
    
    # <= 0
    parents1 = select_gp_parents(pop, scores, 2, tournament_size=0, seed=42)
    assert len(parents1) == 2
    
    # > pop size
    parents2 = select_gp_parents(pop, scores, 2, tournament_size=10, seed=42)
    assert len(parents2) == 2

def test_run_gp_zero_generations_safe_behavior():
    cfg = GPConfig(population_size=5, max_generations=0)
    result = run_gp(None, dummy_fitness, cfg)
    
    assert len(result.final_population) == 5
    assert len(result.generations) == 0
    
    with pytest.raises(ValueError, match="non-negative"):
        cfg.max_generations = -1
        run_gp(None, dummy_fitness, cfg)

def test_run_gp_calls_fitness_with_strategy_objects():
    calls = []
    def spy_fitness(strategy: Strategy) -> float:
        calls.append(strategy)
        return 1.0
        
    cfg = GPConfig(population_size=2, max_generations=1)
    run_gp(None, spy_fitness, cfg)
    
    # 2 for initial population scoring, 2 for final scores after 1 generation evolution
    assert len(calls) == 4
    assert all(isinstance(s, Strategy) for s in calls)

def test_run_gp_full_determinism_including_generation_history():
    cfg = GPConfig(population_size=5, max_generations=3)
    res1 = run_gp(None, dummy_fitness, cfg)
    res2 = run_gp(None, dummy_fitness, cfg)
    
    assert len(res1.generations) == 3
    assert len(res2.generations) == 3
    
    for gen1, gen2 in zip(res1.generations, res2.generations):
        assert gen1.best_score == gen2.best_score
        assert gen1.average_score == gen2.average_score
        assert asdict(gen1.best_individual) == asdict(gen2.best_individual)

def test_gp_mtf_config_generation():
    cfg = GPConfig(population_size=50, allowed_timeframes=(5, 15), mtf_probability=1.0, base_seed=42)
    pop = create_initial_gp_population(50, seed=42, config=cfg)
    
    indicators_seen = set()
    
    for ind in pop:
        for tree in (ind.long_entry_tree, ind.long_exit_tree, ind.short_entry_tree, ind.short_exit_tree):
            for leaf in tree.children:
                assert "timeframe" in leaf.condition.params, f"Missing timeframe in {leaf.condition.indicator}"
                assert leaf.condition.params["timeframe"] in (5, 15)
                indicators_seen.add(leaf.condition.indicator)
                
    # With pop size 50 and 4 trees each (with multiple conditions), we should see all indicators
    assert "SMA" in indicators_seen
    assert "RSI" in indicators_seen
    assert "MACD" in indicators_seen
    assert "ATR" in indicators_seen

def test_gp_mtf_disabled_preserves_rng_determinism():
    cfg1 = GPConfig(population_size=5, base_seed=42, allowed_timeframes=(), mtf_probability=0.0)
    cfg2 = GPConfig(population_size=5, base_seed=42, allowed_timeframes=(5,), mtf_probability=0.0) # probability 0 should not use rng
    res1 = run_gp(None, dummy_fitness, cfg1)
    res2 = run_gp(None, dummy_fitness, cfg2)
    
    assert asdict(res1.best_individual) == asdict(res2.best_individual)
    
    # Check that no MTF params got injected
    for ind in res1.final_population:
        for tree in (ind.long_entry_tree, ind.long_exit_tree, ind.short_entry_tree, ind.short_exit_tree):
            for leaf in tree.children:
                assert "timeframe" not in leaf.condition.params

def test_gp_mtf_mutation_injection():
    cfg = GPConfig(population_size=2, allowed_timeframes=(5, 15), mtf_probability=1.0, mutation_prob=1.0, max_conditions=5)
    
    # Generate an individual without MTF
    from strategy_engine.gp import generate_tree
    rng = random.Random(42)
    ind = GPIndividual("test", generate_tree(rng, "entry"), generate_tree(rng, "exit"), generate_tree(rng, "entry"), generate_tree(rng, "exit"))
    
    # Ensure they have no timeframe initially
    for tree in (ind.long_entry_tree, ind.long_exit_tree, ind.short_entry_tree, ind.short_exit_tree):
        for leaf in tree.children:
            assert "timeframe" not in leaf.condition.params
            
    # Now mutate with MTF config enabled
    from strategy_engine.gp_evolution import mutate_individual
    mutated = mutate_individual(ind, seed=123, config=cfg)
    
    # Because mutation_prob=1.0, all existing leaves will be replaced AND it may grow
    for tree in (mutated.long_entry_tree, mutated.long_exit_tree, mutated.short_entry_tree, mutated.short_exit_tree):
        for leaf in tree.children:
            assert "timeframe" in leaf.condition.params, f"Missing timeframe in mutated {leaf.condition.indicator}"
            assert leaf.condition.params["timeframe"] in (5, 15)

def test_gp_mtf_indicator_injection_coverage():
    """Prove that _generate_random_condition directly injects timeframe into all supported indicators."""
    from strategy_engine.gp import _generate_random_condition
    
    cfg = GPConfig(allowed_timeframes=(5, 15), mtf_probability=1.0)
    
    class MockRNG:
        def __init__(self, ind):
            self.ind = ind
            
        def choice(self, seq):
            if "SMA" in seq:
                return self.ind
            return seq[0]
            
        def random(self):
            return 0.0
            
        def randint(self, a, b):
            return a
            
        def uniform(self, a, b):
            return a

    for indicator in ["SMA", "RSI", "MACD", "ATR", "FALLBACK"]:
        mock_rng = MockRNG(indicator)
        cond = _generate_random_condition(mock_rng, "entry", config=cfg)
        
        if indicator == "FALLBACK":
            assert cond.indicator == "SMA"
        else:
            assert cond.indicator == indicator
            
        assert "timeframe" in cond.params, f"{indicator} branch bypassed MTF injection!"
        assert cond.params["timeframe"] == 5
