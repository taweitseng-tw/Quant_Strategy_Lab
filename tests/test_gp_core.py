"""Tests for GP tree minimal core."""

import random
from dataclasses import asdict
import pandas as pd
import numpy as np

from core.models.strategy import Condition, Strategy, StrategyBlock
from strategy_engine.gp import (
    GPConditionLeaf,
    GPLogicNode,
    generate_tree,
    compile_tree_to_block,
    create_gp_strategy,
)
from backtest_engine.runner import run_backtest

def _make_test_data(n_bars: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(99)
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

def test_gp_tree_generation_is_deterministic():
    rng1 = random.Random(42)
    tree1 = generate_tree(rng1, "entry", max_conditions=5)
    
    rng2 = random.Random(42)
    tree2 = generate_tree(rng2, "entry", max_conditions=5)
    
    assert asdict(tree1) == asdict(tree2)

def test_gp_tree_generation_differs_by_seed():
    rng1 = random.Random(1)
    tree1 = generate_tree(rng1, "entry", max_conditions=5)
    
    rng2 = random.Random(2)
    tree2 = generate_tree(rng2, "entry", max_conditions=5)
    
    assert asdict(tree1) != asdict(tree2)

def test_gp_tree_root_logic_is_valid():
    rng = random.Random(42)
    for _ in range(50):
        tree = generate_tree(rng, "entry")
        assert tree.operator in ("AND", "OR")

def test_gp_tree_respects_max_conditions():
    rng = random.Random(42)
    for _ in range(50):
        tree = generate_tree(rng, "entry", max_conditions=3)
        assert 1 <= len(tree.children) <= 3

def test_gp_tree_depth_is_two_or_less():
    rng = random.Random(42)
    tree = generate_tree(rng, "entry")
    assert isinstance(tree, GPLogicNode)
    for leaf in tree.children:
        assert isinstance(leaf, GPConditionLeaf)
        assert not isinstance(leaf, GPLogicNode)

def test_gp_leaf_conditions_are_core_condition_objects():
    rng = random.Random(42)
    tree = generate_tree(rng, "entry")
    for leaf in tree.children:
        assert isinstance(leaf.condition, Condition)
        assert leaf.condition.indicator in ("SMA", "RSI", "MACD", "ATR")

def test_compile_tree_to_block_returns_strategy_block():
    rng = random.Random(42)
    tree = generate_tree(rng, "entry")
    block = compile_tree_to_block(tree)
    
    assert isinstance(block, StrategyBlock)
    assert block.logic == tree.operator
    assert len(block.conditions) == len(tree.children)
    for c1, c2 in zip(block.conditions, tree.children):
        assert c1 is c2.condition

def test_create_gp_strategy_has_four_blocks():
    strat = create_gp_strategy("test_gp", seed=10)
    assert isinstance(strat, Strategy)
    assert strat.name == "test_gp"
    assert isinstance(strat.long_entry, StrategyBlock)
    assert isinstance(strat.long_exit, StrategyBlock)
    assert isinstance(strat.short_entry, StrategyBlock)
    assert isinstance(strat.short_exit, StrategyBlock)

def test_gp_strategy_is_backtestable():
    strat = create_gp_strategy("test_gp_bt", seed=42)
    df = _make_test_data(100)
    bt = run_backtest(strat, df)
    
    assert "total_pnl" in bt.metrics
    assert "total_trades" in bt.metrics

def test_gp_module_has_no_backtest_or_pyside_imports():
    import pathlib
    source = pathlib.Path("strategy_engine/gp.py").read_text(encoding="utf-8")
    assert "PySide6" not in source
    assert "backtest" not in source.lower()
    assert "validation" not in source.lower()

def test_gp_invalid_max_conditions_raises_or_clamps_documented_behavior():
    rng = random.Random(42)
    # Clamp to 1
    tree = generate_tree(rng, "entry", max_conditions=-5)
    assert len(tree.children) == 1

def test_gp_macd_fast_less_than_slow_invariant():
    rng = random.Random(42)
    for _ in range(200):
        tree = generate_tree(rng, "entry", max_conditions=5)
        for leaf in tree.children:
            if leaf.condition.indicator == "MACD":
                fast = leaf.condition.params["fast"]
                slow = leaf.condition.params["slow"]
                assert fast < slow

def test_gp_create_strategy_blocks_are_independent_objects():
    strat = create_gp_strategy("test_indep", seed=1)
    assert strat.long_entry is not strat.long_exit
    assert strat.long_entry is not strat.short_entry
    assert strat.long_exit is not strat.short_exit
    assert strat.short_entry is not strat.short_exit

def test_compile_tree_to_block_does_not_mutate_tree():
    rng = random.Random(42)
    tree = generate_tree(rng, "entry", max_conditions=3)
    orig_op = tree.operator
    orig_len = len(tree.children)
    
    _ = compile_tree_to_block(tree)
    
    assert tree.operator == orig_op
    assert len(tree.children) == orig_len

def test_gp_generation_does_not_use_global_random_state():
    state_before = random.getstate()
    rng = random.Random(42)
    _ = generate_tree(rng, "entry", max_conditions=5)
    state_after = random.getstate()
    assert state_before == state_after

def test_gp_conditions_have_evaluator_compatible_params():
    rng = random.Random(42)
    for _ in range(50):
        tree = generate_tree(rng, "entry", max_conditions=5)
        for leaf in tree.children:
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
                assert cond.params["fast"] < cond.params["slow"]
            elif cond.indicator == "ATR":
                assert "period" in cond.params
                assert isinstance(cond.right, (int, float))
