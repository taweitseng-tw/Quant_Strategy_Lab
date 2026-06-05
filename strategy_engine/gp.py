"""Genetic Programming minimal tree core."""

from __future__ import annotations

import random
import copy
from dataclasses import dataclass, field

from core.models.strategy import Condition, Strategy, StrategyBlock
from strategy_engine.generator import (
    _INDICATOR_TYPES,
    DEFAULT_SMA_PERIOD_RANGE,
    DEFAULT_RSI_PERIOD_RANGE,
    DEFAULT_RSI_THRESHOLD_RANGE,
    DEFAULT_MACD_FAST_RANGE,
    DEFAULT_MACD_SLOW_RANGE,
    DEFAULT_MACD_SIGNAL_RANGE,
    DEFAULT_ATR_PERIOD_RANGE,
    DEFAULT_ATR_THRESHOLD_RANGE,
)

@dataclass
class GPConditionLeaf:
    """A leaf node containing a single strategy Condition."""
    condition: Condition

@dataclass
class GPLogicNode:
    """A root logical node (AND or OR) containing Condition leaves."""
    operator: str
    children: list[GPConditionLeaf] = field(default_factory=list)

def _generate_random_condition(rng: random.Random, direction: str, config: GPConfig | None = None) -> Condition:
    ind = rng.choice(_INDICATOR_TYPES)
    
    if ind == "SMA":
        period = rng.randint(*DEFAULT_SMA_PERIOD_RANGE)
        op = ">" if direction == "entry" else "<"
        cond = Condition("SMA", {"period": period}, op)
    elif ind == "RSI":
        period = rng.randint(*DEFAULT_RSI_PERIOD_RANGE)
        threshold = float(rng.randint(*DEFAULT_RSI_THRESHOLD_RANGE))
        op = ">" if direction == "entry" else "<"
        cond = Condition("RSI", {"period": period}, op, right=threshold)
    elif ind == "MACD":
        fast = rng.randint(*DEFAULT_MACD_FAST_RANGE)
        slow = rng.randint(*DEFAULT_MACD_SLOW_RANGE)
        if fast >= slow:
            fast, slow = slow - 1, fast + 1
            fast = max(fast, DEFAULT_MACD_FAST_RANGE[0])
        sig = rng.randint(*DEFAULT_MACD_SIGNAL_RANGE)
        op = ">" if direction == "entry" else "<"
        cond = Condition("MACD", {"fast": fast, "slow": slow, "signal": sig}, op)
    elif ind == "ATR":
        period = rng.randint(*DEFAULT_ATR_PERIOD_RANGE)
        threshold = round(rng.uniform(*DEFAULT_ATR_THRESHOLD_RANGE), 2)
        op = ">" if direction == "entry" else "<"
        cond = Condition("ATR", {"period": period}, op, right=threshold)
    else:
        cond = Condition("SMA", {"period": 20}, ">")

    if config and config.mtf_probability > 0.0 and config.allowed_timeframes:
        if rng.random() < config.mtf_probability:
            cond.params["timeframe"] = rng.choice(config.allowed_timeframes)

    return cond

def generate_tree(rng: random.Random, direction: str, max_conditions: int = 5, config: GPConfig | None = None) -> GPLogicNode:
    """Generate a depth-2 GP tree with a random logic root and random condition leaves."""
    operator = rng.choice(["AND", "OR"])
    max_conditions = max(1, max_conditions)
    num_conditions = rng.randint(1, max_conditions)
    children = []
    for _ in range(num_conditions):
        cond = _generate_random_condition(rng, direction, config)
        children.append(GPConditionLeaf(condition=cond))
    return GPLogicNode(operator=operator, children=children)

def compile_tree_to_block(tree: GPLogicNode) -> StrategyBlock:
    """Compile a GP tree into a flat StrategyBlock."""
    conditions = [leaf.condition for leaf in tree.children]
    return StrategyBlock(conditions=conditions, logic=tree.operator)

def create_gp_strategy(name: str, seed: int, max_conditions: int = 5, config: GPConfig | None = None) -> Strategy:
    """Deterministically generate a four-block Strategy using GP trees."""
    rng = random.Random(seed)
    
    long_entry_tree = generate_tree(rng, "entry", max_conditions, config)
    long_exit_tree = generate_tree(rng, "exit", max_conditions, config)
    
    # Randomly decide to include short side
    if rng.random() < 0.5:
        short_entry_tree = generate_tree(rng, "entry", max_conditions, config)
        short_exit_tree = generate_tree(rng, "exit", max_conditions, config)
        short_entry_block = compile_tree_to_block(short_entry_tree)
        short_exit_block = compile_tree_to_block(short_exit_tree)
    else:
        short_entry_block = StrategyBlock()
        short_exit_block = StrategyBlock()
        
    return Strategy(
        name=name,
        long_entry=compile_tree_to_block(long_entry_tree),
        long_exit=compile_tree_to_block(long_exit_tree),
        short_entry=short_entry_block,
        short_exit=short_exit_block
    )

def crossover_tree(parent_a: GPLogicNode, parent_b: GPLogicNode, seed: int, max_conditions: int = 5, config: GPConfig | None = None) -> GPLogicNode:
    """Combine two GP trees to create a new one."""
    rng = random.Random(seed)
    max_conditions = max(1, max_conditions)
    
    # Randomly pick operator from A or B
    op = rng.choice([parent_a.operator, parent_b.operator])
    
    # Collect all children from A and B
    pool = parent_a.children + parent_b.children
    
    # Pick a random length from one of the parents to maintain relative size
    target_len = rng.choice([len(parent_a.children), len(parent_b.children)])
    target_len = min(target_len, max_conditions)
    target_len = max(1, target_len)
    
    # Sample from pool
    actual_len = min(target_len, len(pool))
    if actual_len == 0:
        selected = [GPConditionLeaf(condition=_generate_random_condition(rng, "entry", config))]
    else:
        selected = rng.sample(pool, actual_len)
    
    # Deepcopy to ensure independent references
    new_children = [copy.deepcopy(leaf) for leaf in selected]
    
    return GPLogicNode(operator=op, children=new_children)

def mutate_tree(tree: GPLogicNode, seed: int, mutation_prob: float = 0.2, max_conditions: int = 5, direction: str = "entry", config: GPConfig | None = None) -> GPLogicNode:
    """Mutate a GP tree in place (on a deep copy)."""
    mutation_prob = max(0.0, min(1.0, mutation_prob))
    max_conditions = max(1, max_conditions)
    
    rng = random.Random(seed)
    new_tree = copy.deepcopy(tree)
    
    if len(new_tree.children) > max_conditions:
        new_tree.children = rng.sample(new_tree.children, max_conditions)
    
    # Node mutation (root operator)
    if rng.random() < mutation_prob:
        new_tree.operator = "OR" if new_tree.operator == "AND" else "AND"
        
    # Structural mutation
    if rng.random() < mutation_prob:
        action = rng.choice(["grow", "shrink"])
        if action == "grow" and len(new_tree.children) < max_conditions:
            cond = _generate_random_condition(rng, direction, config)
            new_tree.children.append(GPConditionLeaf(condition=cond))
        elif action == "shrink" and len(new_tree.children) > 1:
            idx = rng.randrange(len(new_tree.children))
            new_tree.children.pop(idx)
            
    # Leaf mutation
    for leaf in new_tree.children:
        if rng.random() < mutation_prob:
            # Completely replace this condition with a new random one
            # Preserves all invariants by reusing _generate_random_condition
            leaf.condition = _generate_random_condition(rng, direction, config)
            
    return new_tree
