"""Tests for GP tree crossover and mutation operators."""

import random
import copy
from dataclasses import asdict
import pytest

from core.models.strategy import Condition
from strategy_engine.gp import (
    GPConditionLeaf,
    GPLogicNode,
    generate_tree,
    crossover_tree,
    mutate_tree,
    compile_tree_to_block
)
from backtest_engine.runner import run_backtest
import pandas as pd
import numpy as np
from core.models.strategy import Strategy, StrategyBlock

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

@pytest.fixture
def parent_a():
    rng = random.Random(1)
    return generate_tree(rng, "entry")

@pytest.fixture
def parent_b():
    rng = random.Random(2)
    return generate_tree(rng, "entry")

def test_crossover_tree_is_deterministic(parent_a, parent_b):
    child1 = crossover_tree(parent_a, parent_b, seed=42)
    child2 = crossover_tree(parent_a, parent_b, seed=42)
    assert asdict(child1) == asdict(child2)

def test_crossover_tree_differs_by_seed_when_possible(parent_a, parent_b):
    child1 = crossover_tree(parent_a, parent_b, seed=1)
    child2 = crossover_tree(parent_a, parent_b, seed=2)
    # With these parents and different seeds, they should differ
    assert asdict(child1) != asdict(child2)

def test_crossover_returns_valid_depth_two_tree(parent_a, parent_b):
    child = crossover_tree(parent_a, parent_b, seed=42)
    assert isinstance(child, GPLogicNode)
    assert child.operator in ("AND", "OR")
    assert len(child.children) >= 1
    for leaf in child.children:
        assert isinstance(leaf, GPConditionLeaf)
        assert isinstance(leaf.condition, Condition)

def test_crossover_does_not_share_conditions_with_parents(parent_a, parent_b):
    child = crossover_tree(parent_a, parent_b, seed=42)
    for child_leaf in child.children:
        for pa_leaf in parent_a.children:
            assert child_leaf is not pa_leaf
            assert child_leaf.condition is not pa_leaf.condition
        for pb_leaf in parent_b.children:
            assert child_leaf is not pb_leaf
            assert child_leaf.condition is not pb_leaf.condition

def test_mutate_tree_is_deterministic(parent_a):
    mut1 = mutate_tree(parent_a, seed=42, mutation_prob=0.5)
    mut2 = mutate_tree(parent_a, seed=42, mutation_prob=0.5)
    assert asdict(mut1) == asdict(mut2)

def test_mutate_zero_probability_returns_safe_copy(parent_a):
    mut = mutate_tree(parent_a, seed=42, mutation_prob=0.0)
    assert asdict(mut) == asdict(parent_a)
    assert mut is not parent_a
    for mut_leaf, pa_leaf in zip(mut.children, parent_a.children):
        assert mut_leaf is not pa_leaf
        assert mut_leaf.condition is not pa_leaf.condition

def test_mutate_full_probability_changes_tree_when_possible(parent_a):
    mut = mutate_tree(parent_a, seed=42, mutation_prob=1.0)
    assert asdict(mut) != asdict(parent_a)

def test_mutate_preserves_indicator_param_contracts(parent_a):
    mut = mutate_tree(parent_a, seed=42, mutation_prob=1.0)
    for leaf in mut.children:
        cond = leaf.condition
        if cond.indicator == "SMA":
            assert "period" in cond.params
        elif cond.indicator == "RSI":
            assert "period" in cond.params
            assert isinstance(cond.right, (int, float))
        elif cond.indicator == "MACD":
            assert "fast" in cond.params
            assert "slow" in cond.params
            assert "signal" in cond.params
        elif cond.indicator == "ATR":
            assert "period" in cond.params
            assert isinstance(cond.right, (int, float))

def test_mutate_preserves_macd_fast_less_than_slow():
    rng = random.Random(10)
    tree = generate_tree(rng, "entry")
    mut = mutate_tree(tree, seed=42, mutation_prob=1.0)
    for leaf in mut.children:
        cond = leaf.condition
        if cond.indicator == "MACD":
            assert cond.params["fast"] < cond.params["slow"]

def test_mutate_preserves_max_conditions(parent_a):
    # Grow mutation at 100%
    mut = mutate_tree(parent_a, seed=42, mutation_prob=1.0, max_conditions=len(parent_a.children))
    assert len(mut.children) <= len(parent_a.children)

def test_mutate_does_not_use_global_random_state(parent_a):
    state_before = random.getstate()
    _ = mutate_tree(parent_a, seed=42, mutation_prob=0.5)
    state_after = random.getstate()
    assert state_before == state_after

def test_mutated_and_crossover_tree_are_backtestable(parent_a, parent_b):
    child = crossover_tree(parent_a, parent_b, seed=42)
    mut = mutate_tree(child, seed=42, mutation_prob=0.5)
    
    strat = Strategy(
        name="test_gp_ops",
        long_entry=compile_tree_to_block(mut),
        long_exit=StrategyBlock(),
        short_entry=StrategyBlock(),
        short_exit=StrategyBlock()
    )
    df = _make_test_data(100)
    bt = run_backtest(strat, df)
    assert "total_trades" in bt.metrics

def test_mutate_negative_probability_behaves_as_zero_or_documented(parent_a):
    mut = mutate_tree(parent_a, seed=42, mutation_prob=-1.0)
    assert asdict(mut) == asdict(parent_a)
    assert mut is not parent_a

def test_mutate_probability_above_one_behaves_as_one_or_documented(parent_a):
    mut1 = mutate_tree(parent_a, seed=42, mutation_prob=1.0)
    mut2 = mutate_tree(parent_a, seed=42, mutation_prob=5.0)
    assert asdict(mut1) == asdict(mut2)

def test_mutate_max_conditions_one_never_grows_past_one():
    rng = random.Random(1)
    tree = generate_tree(rng, "entry", max_conditions=1)
    # Even with 100% mutation prob, it should clamp to max_conditions=1
    mut = mutate_tree(tree, seed=42, mutation_prob=1.0, max_conditions=1)
    assert len(mut.children) == 1

def test_mutate_never_removes_last_leaf():
    rng = random.Random(1)
    tree = generate_tree(rng, "entry", max_conditions=1)
    mut = mutate_tree(tree, seed=42, mutation_prob=1.0, max_conditions=1)
    assert len(mut.children) >= 1

def test_crossover_handles_mismatched_leaf_counts():
    rng = random.Random(1)
    parent_a = generate_tree(rng, "entry", max_conditions=1)
    parent_b = generate_tree(rng, "entry", max_conditions=5)
    # Ensure they actually differ in length for the test
    parent_a.children = parent_a.children[:1]
    while len(parent_b.children) < 5:
        parent_b.children.append(GPConditionLeaf(condition=Condition("SMA", {"period": 10}, ">")))
        
    child = crossover_tree(parent_a, parent_b, seed=42, max_conditions=5)
    assert 1 <= len(child.children) <= 5

def test_crossover_output_respects_valid_condition_contracts(parent_a, parent_b):
    child = crossover_tree(parent_a, parent_b, seed=42)
    for leaf in child.children:
        cond = leaf.condition
        assert cond.indicator in ("SMA", "RSI", "MACD", "ATR")

def test_crossover_does_not_use_global_random_state(parent_a, parent_b):
    state_before = random.getstate()
    _ = crossover_tree(parent_a, parent_b, seed=42)
    state_after = random.getstate()
    assert state_before == state_after

def test_crossover_result_backtestable_with_mismatched_parents():
    rng = random.Random(1)
    parent_a = generate_tree(rng, "entry", max_conditions=1)
    parent_b = generate_tree(rng, "entry", max_conditions=5)
    child = crossover_tree(parent_a, parent_b, seed=42, max_conditions=5)
    
    strat = Strategy(
        name="test_crossover_mismatch",
        long_entry=compile_tree_to_block(child),
        long_exit=StrategyBlock(),
        short_entry=StrategyBlock(),
        short_exit=StrategyBlock()
    )
    df = _make_test_data(100)
    bt = run_backtest(strat, df)
    assert "total_trades" in bt.metrics
