"""Tests for Genetic Algorithm strategy evolution primitives."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from core.models.strategy import Condition, Strategy, StrategyBlock
from strategy_engine.ga import (
    GAConfig,
    GAResult,
    create_initial_population,
    crossover,
    evolve_one_generation,
    mutate,
    run_ga,
    select_parents,
)


def _sma_strategy(name: str, entry_period: int, exit_period: int = 30) -> Strategy:
    return Strategy(
        name=name,
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": entry_period}, operator=">")]
        ),
        long_exit=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": exit_period}, operator="<")]
        ),
    )


def _mixed_strategy() -> Strategy:
    return Strategy(
        name="mixed",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20}, operator=">")]
        ),
        long_exit=StrategyBlock(
            conditions=[Condition(indicator="RSI", params={"period": 14}, operator="<", right=30.0)]
        ),
        short_entry=StrategyBlock(
            conditions=[
                Condition(
                    indicator="MACD",
                    params={"fast": 12, "slow": 26, "signal": 9},
                    operator=">",
                )
            ]
        ),
        short_exit=StrategyBlock(
            conditions=[Condition(indicator="ATR", params={"period": 14}, operator="<", right=2.5)]
        ),
    )


def _period_fitness(strategy: Strategy) -> float:
    if not strategy.long_entry.conditions:
        return 0.0
    return float(strategy.long_entry.conditions[0].params.get("period", 0))


def test_create_initial_population_count_and_seed_determinism():
    first = create_initial_population(8, seed=123)
    second = create_initial_population(8, seed=123)

    assert len(first) == 8
    assert [asdict(s) for s in first] == [asdict(s) for s in second]


def test_create_initial_population_forwards_mtf_config(monkeypatch):
    from strategy_engine import ga
    
    seen_kwargs = {}
    
    def fake_generate_strategies(*args, **kwargs):
        seen_kwargs.update(kwargs)
        # Return a valid mock output to avoid crashing the list comprehension
        return [{"strategy": _sma_strategy("dummy", 10)}]

    monkeypatch.setattr(ga, "generate_strategies", fake_generate_strategies)
    
    cfg = GAConfig(
        population_size=1,
        base_seed=42,
        allowed_timeframes=(15, 60),
        mtf_probability=0.25
    )
    
    create_initial_population(1, seed=42, config=cfg)
    
    assert "allowed_timeframes" in seen_kwargs
    assert seen_kwargs["allowed_timeframes"] == (15, 60)
    assert "mtf_probability" in seen_kwargs
    assert seen_kwargs["mtf_probability"] == 0.25


def test_select_parents_prefers_high_fitness_candidates():
    population = [_sma_strategy(f"s{i}", i) for i in range(1, 6)]
    scores = [1.0, 2.0, 3.0, 4.0, 100.0]

    selected = select_parents(population, scores, 12, tournament_size=5, seed=7)

    assert len(selected) == 12
    assert {s.name for s in selected} == {"s5"}


def test_tournament_selection_same_seed_is_deterministic():
    population = [_sma_strategy(f"s{i}", i) for i in range(1, 8)]
    scores = [float(i) for i in range(1, 8)]

    first = select_parents(population, scores, 6, tournament_size=3, seed=99)
    second = select_parents(population, scores, 6, tournament_size=3, seed=99)

    assert [asdict(s) for s in first] == [asdict(s) for s in second]


def test_crossover_returns_valid_strategy_with_blocks_from_parents():
    parent_a = _sma_strategy("a", 10, 20)
    parent_b = _sma_strategy("b", 70, 80)

    child = crossover(parent_a, parent_b, seed=2)

    assert isinstance(child, Strategy)
    assert child.long_entry.conditions
    assert child.long_exit.conditions
    assert child.long_entry.conditions[0].params["period"] in {10, 70}
    assert child.long_exit.conditions[0].params["period"] in {20, 80}


def test_crossover_same_seed_is_deterministic():
    parent_a = _sma_strategy("a", 10, 20)
    parent_b = _sma_strategy("b", 70, 80)

    first = crossover(parent_a, parent_b, seed=12)
    second = crossover(parent_a, parent_b, seed=12)

    assert asdict(first) == asdict(second)


def test_mutation_prob_one_changes_parameters_without_changing_indicator_types():
    strategy = _mixed_strategy()
    before_indicators = [
        condition.indicator
        for block in (strategy.long_entry, strategy.long_exit, strategy.short_entry, strategy.short_exit)
        for condition in block.conditions
    ]

    mutated = mutate(strategy, prob=1.0, strength=4.0, seed=4)
    after_indicators = [
        condition.indicator
        for block in (mutated.long_entry, mutated.long_exit, mutated.short_entry, mutated.short_exit)
        for condition in block.conditions
    ]

    assert asdict(mutated) != asdict(strategy)
    assert after_indicators == before_indicators


def test_mutation_clamps_ranges_and_repairs_macd_fast_slow():
    cfg = GAConfig(
        sma_period_range=(5, 6),
        rsi_period_range=(7, 8),
        rsi_threshold_range=(20, 21),
        atr_period_range=(9, 10),
        atr_threshold_range=(1.0, 1.1),
        macd_fast_range=(3, 4),
        macd_slow_range=(5, 6),
        macd_signal_range=(7, 8),
    )
    strategy = Strategy(
        name="edge",
        long_entry=StrategyBlock([Condition("SMA", {"period": 1000}, ">")]),
        long_exit=StrategyBlock([Condition("RSI", {"period": 1000}, "<", right=999.0)]),
        short_entry=StrategyBlock([Condition("MACD", {"fast": 999, "slow": 1, "signal": 999}, ">")]),
        short_exit=StrategyBlock([Condition("ATR", {"period": 1000}, "<", right=999.0)]),
    )

    mutated = mutate(strategy, prob=1.0, strength=100.0, seed=10, config=cfg)

    assert 5 <= mutated.long_entry.conditions[0].params["period"] <= 6
    assert 7 <= mutated.long_exit.conditions[0].params["period"] <= 8
    assert 20 <= float(mutated.long_exit.conditions[0].right) <= 21
    macd = mutated.short_entry.conditions[0].params
    assert 3 <= macd["fast"] <= 4
    assert 5 <= macd["slow"] <= 6
    assert macd["fast"] < macd["slow"]
    assert 7 <= macd["signal"] <= 8
    assert 9 <= mutated.short_exit.conditions[0].params["period"] <= 10
    assert 1.0 <= float(mutated.short_exit.conditions[0].right) <= 1.1


def test_evolve_one_generation_preserves_elite_and_population_size():
    population = [_sma_strategy(f"s{i}", i) for i in range(10, 60, 10)]
    scores = [1.0, 2.0, 50.0, 4.0, 5.0]
    cfg = GAConfig(population_size=5, elite_count=1, mutation_prob=0.0, base_seed=3)

    evolved = evolve_one_generation(population, scores, generation=1, config=cfg)

    assert len(evolved) == 5
    assert asdict(evolved[0]) == asdict(population[2])


def test_run_ga_returns_structured_result():
    cfg = GAConfig(population_size=6, elite_count=1, max_generations=3, mutation_prob=1.0, base_seed=11)
    initial = [_sma_strategy(f"s{i}", i * 5) for i in range(1, 7)]

    result = run_ga(initial, _period_fitness, config=cfg)

    assert isinstance(result, GAResult)
    assert len(result.final_population) == 6
    assert len(result.final_scores) == 6
    assert len(result.generations) == 3
    assert result.best_score == max(result.final_scores)
    assert isinstance(result.best_strategy, Strategy)


def test_run_ga_same_seed_is_deterministic():
    cfg = GAConfig(population_size=6, elite_count=1, max_generations=3, mutation_prob=1.0, base_seed=11)
    initial = [_sma_strategy(f"s{i}", i * 5) for i in range(1, 7)]

    first = run_ga(initial, _period_fitness, config=cfg)
    second = run_ga(initial, _period_fitness, config=cfg)

    assert [asdict(s) for s in first.final_population] == [asdict(s) for s in second.final_population]
    assert first.final_scores == second.final_scores


def test_ga_module_has_no_pyside_imports():
    source = Path("strategy_engine/ga.py").read_text(encoding="utf-8")
    assert "PySide6" not in source
