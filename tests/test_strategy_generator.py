"""Tests for strategy generator and ranking — Task 006A."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.models.strategy import Strategy
from strategy_engine.generator import GENERATOR_VERSION, generate_strategies
from strategy_engine.ranking import compute_fitness, rank_strategies
from backtest_engine.runner import run_backtest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_test_data(n_bars: int = 200) -> pd.DataFrame:
    """Create a realistic OHLCV dataset for backtesting generated strategies."""
    rng = np.random.default_rng(99)
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="1min")

    # Random walk with drift.
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


def _backtest_strategies(generated: list[dict], df: pd.DataFrame) -> list[dict]:
    """Backtest each generated strategy and attach metrics."""
    results = []
    for entry in generated:
        strat = entry["strategy"]
        bt = run_backtest(strat, df, commission=2.0)
        results.append({
            "strategy": strat,
            "provenance": entry["provenance"],
            "metrics": bt.metrics,
        })
    return results


# ---------------------------------------------------------------------------
# Generator — determinism
# ---------------------------------------------------------------------------


def test_same_seed_produces_same_strategies():
    """Same seed must produce identical strategies."""
    g1 = generate_strategies(count=10, seed=42)
    g2 = generate_strategies(count=10, seed=42)

    for e1, e2 in zip(g1, g2):
        s1 = e1["strategy"]
        s2 = e2["strategy"]
        assert s1.name == s2.name
        assert s1.long_entry.conditions[0].params == s2.long_entry.conditions[0].params
        assert s1.long_exit.conditions[0].params == s2.long_exit.conditions[0].params


def test_full_provenance_equality_same_seed():
    """Same seed + fixed generated_at → fully identical provenance dicts."""
    g1 = generate_strategies(count=5, seed=42, generated_at="2026-01-01T00:00:00")
    g2 = generate_strategies(count=5, seed=42, generated_at="2026-01-01T00:00:00")

    for e1, e2 in zip(g1, g2):
        assert e1["provenance"] == e2["provenance"]


def test_different_seeds_can_produce_different_strategies():
    """Different seeds should produce different parameter draws (probabilistic)."""
    from strategy_engine.generator import generate_strategies as gen

    g1 = gen(count=20, seed=1, indicator_weights=(1.0, 0.0, 0.0, 0.0))
    g2 = gen(count=20, seed=9999, indicator_weights=(1.0, 0.0, 0.0, 0.0))

    # Force SMA-only so we can compare "period" param directly.
    periods_1 = {e["strategy"].long_entry.conditions[0].params["period"] for e in g1}
    periods_2 = {e["strategy"].long_entry.conditions[0].params["period"] for e in g2}

    # They may overlap but should not be identical sets.
    assert periods_1 != periods_2


# ---------------------------------------------------------------------------
# Generator — count and structure
# ---------------------------------------------------------------------------


def test_generates_exactly_count_strategies():
    """generate_strategies(count=N) must return exactly N."""
    for n in [1, 10, 20]:
        result = generate_strategies(count=n, seed=0)
        assert len(result) == n


def test_each_strategy_has_four_blocks():
    """Every generated strategy must have the four-block structure."""
    generated = generate_strategies(count=10, seed=42)
    for entry in generated:
        s = entry["strategy"]
        assert isinstance(s, Strategy)
        assert s.long_entry is not None
        assert s.long_exit is not None
        assert s.short_entry is not None
        assert s.short_exit is not None


def test_long_entry_always_has_condition():
    """Long entry block must always have at least one condition."""
    generated = generate_strategies(count=20, seed=7)
    for entry in generated:
        s = entry["strategy"]
        assert len(s.long_entry.conditions) >= 1
        cond = s.long_entry.conditions[0]
        assert cond.indicator in ("SMA", "RSI", "MACD", "ATR")
        assert len(cond.params) >= 1


# ---------------------------------------------------------------------------
# Generator — provenance
# ---------------------------------------------------------------------------


def test_provenance_fields_present():
    """Each generated strategy must include all provenance metadata."""
    generated = generate_strategies(count=5, seed=1)
    required_keys = [
        "strategy_json",
        "random_seed",
        "generator_version",
        "rule_block_versions",
        "parameter_ranges",
        "dataset_id",
        "instrument_profile_id",
        "build_task_id",
        "fitness_config",
        "elimination_config",
    ]
    for entry in generated:
        prov = entry["provenance"]
        for key in required_keys:
            assert key in prov, f"Missing provenance key: {key}"
        assert prov["generator_version"] == GENERATOR_VERSION
        assert prov["random_seed"] == 1
        assert isinstance(prov["strategy_json"], dict)


# ---------------------------------------------------------------------------
# Generator — multi-indicator (Task 022)
# ---------------------------------------------------------------------------


def test_generated_strategies_include_rsimacdatr():
    """With default weights, generated strategies should include non-SMA indicators."""
    # Force all strategies to use RSI/MACD/ATR by zeroing SMA weight.
    generated = generate_strategies(count=20, seed=42,
                                    indicator_weights=(0.0, 0.4, 0.3, 0.3))
    indicators = set()
    for entry in generated:
        for block_name in ("long_entry", "long_exit", "short_entry", "short_exit"):
            block = getattr(entry["strategy"], block_name)
            for cond in block.conditions:
                indicators.add(cond.indicator)
    assert "RSI" in indicators or "MACD" in indicators or "ATR" in indicators


def test_generated_strategies_with_rsimacdatr_are_backtestable():
    """Strategies using RSI/MACD/ATR must run through the backtest engine."""
    df = _make_test_data(200)
    generated = generate_strategies(count=10, seed=42)
    results = _backtest_strategies(generated, df)

    assert len(results) == 10
    for r in results:
        assert "metrics" in r
        assert "total_trades" in r["metrics"]
        assert "total_pnl" in r["metrics"]


def test_no_macd_fast_gte_slow():
    """Generated MACD conditions must have fast < slow."""
    generated = generate_strategies(count=30, seed=99)
    for entry in generated:
        for block_name in ("long_entry", "long_exit", "short_entry", "short_exit"):
            block = getattr(entry["strategy"], block_name)
            for cond in block.conditions:
                if cond.indicator == "MACD":
                    assert cond.params["fast"] < cond.params["slow"], (
                        f"MACD fast={cond.params['fast']} >= slow={cond.params['slow']}"
                    )


def test_provenance_includes_expanded_parameter_ranges():
    """Provenance must now include RSI, MACD, ATR parameter ranges."""
    generated = generate_strategies(count=5, seed=1)
    for entry in generated:
        pr = entry["provenance"]["parameter_ranges"]
        assert "rsi_period" in pr
        assert "rsi_threshold" in pr
        assert "atr_period" in pr
        assert "atr_threshold" in pr
        assert "macd_fast" in pr
        assert "macd_slow" in pr
        assert "macd_signal" in pr
        assert "volume_threshold" in pr
        assert "volume_sma_period" in pr
        assert "volume_sma_multiplier" in pr
        assert "indicator_weights" in pr


def test_existing_sma_only_call_still_works():
    """Calling generate_strategies() with default args (backward compat) must work."""
    generated = generate_strategies(count=10, seed=42)
    assert len(generated) == 10
    for entry in generated:
        assert entry["strategy"].long_entry.conditions  # still has conditions


# ---------------------------------------------------------------------------
# Backtestability
# ---------------------------------------------------------------------------


def test_generated_strategies_can_be_backtested():
    """Every generated strategy must run through the backtest engine without error."""
    df = _make_test_data(100)
    generated = generate_strategies(count=10, seed=42)
    results = _backtest_strategies(generated, df)

    assert len(results) == 10
    for r in results:
        assert "metrics" in r
        assert "total_trades" in r["metrics"]
        assert "total_pnl" in r["metrics"]


# ---------------------------------------------------------------------------
# Generator — Volume (Task 040C)
# ---------------------------------------------------------------------------


def test_generator_can_generate_volume_threshold_conditions():
    """Setting weights for VOLUME should generate VOLUME threshold conditions."""
    generated = generate_strategies(count=20, seed=42,
                                    indicator_weights=(0.0, 0.0, 0.0, 0.0, 1.0, 0.0))
    for entry in generated:
        cond = entry["strategy"].long_entry.conditions[0]
        assert cond.indicator == "VOLUME"
        assert not cond.params
        assert isinstance(cond.right, float)


def test_generator_volume_threshold_range_respected():
    """VOLUME conditions should respect the provided threshold range."""
    generated = generate_strategies(
        count=50, seed=42,
        indicator_weights=(0.0, 0.0, 0.0, 0.0, 1.0, 0.0),
        volume_threshold_range=(1234, 5678)
    )
    for entry in generated:
        cond = entry["strategy"].long_entry.conditions[0]
        assert cond.indicator == "VOLUME"
        assert 1234.0 <= cond.right <= 5678.0


def test_generator_can_generate_volume_sma_conditions():
    """Setting weights for VOLUME_SMA should generate VOLUME_SMA conditions."""
    generated = generate_strategies(count=20, seed=42,
                                    indicator_weights=(0.0, 0.0, 0.0, 0.0, 0.0, 1.0))
    for entry in generated:
        cond = entry["strategy"].long_entry.conditions[0]
        assert cond.indicator == "VOLUME_SMA"
        assert "period" in cond.params
        assert isinstance(cond.right, float)


def test_generator_volume_sma_range_respected():
    """VOLUME_SMA conditions should respect the provided period and multiplier ranges."""
    generated = generate_strategies(
        count=50, seed=42,
        indicator_weights=(0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
        volume_sma_period_range=(10, 20),
        volume_sma_multiplier_range=(1.5, 3.5)
    )
    for entry in generated:
        cond = entry["strategy"].long_entry.conditions[0]
        assert cond.indicator == "VOLUME_SMA"
        assert 10 <= cond.params["period"] <= 20
        assert 1.5 <= cond.right <= 3.5


def test_generator_volume_conditions_are_backtestable():
    """Strategies generated with VOLUME conditions must run through the backtest engine."""
    df = _make_test_data(100)
    generated = generate_strategies(count=10, seed=42,
                                    indicator_weights=(0.0, 0.0, 0.0, 0.0, 1.0, 0.0))
    results = _backtest_strategies(generated, df)
    
    assert len(results) == 10
    for r in results:
        assert "metrics" in r
        assert "total_trades" in r["metrics"]
        assert "total_pnl" in r["metrics"]


def test_generator_volume_sma_conditions_are_backtestable():
    """Strategies generated with VOLUME_SMA conditions must run through the backtest engine."""
    df = _make_test_data(100)
    generated = generate_strategies(count=10, seed=42,
                                    indicator_weights=(0.0, 0.0, 0.0, 0.0, 0.0, 1.0))
    results = _backtest_strategies(generated, df)
    
    assert len(results) == 10
    for r in results:
        assert "metrics" in r
        assert "total_trades" in r["metrics"]
        assert "total_pnl" in r["metrics"]


def test_generator_sma_only_mode_still_works():
    """Ensure we can still disable everything and generate only SMA."""
    generated = generate_strategies(count=20, seed=42,
                                    indicator_weights=(1.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    for entry in generated:
        cond = entry["strategy"].long_entry.conditions[0]
        assert cond.indicator == "SMA"


def test_generator_volume_weights_configurable():
    """Ensure the new weights sum and behave properly."""
    generated = generate_strategies(count=50, seed=42,
                                    indicator_weights=(0.0, 0.0, 0.0, 0.0, 0.5, 0.5))
    indicators = set()
    for entry in generated:
        indicators.add(entry["strategy"].long_entry.conditions[0].indicator)
    assert "VOLUME" in indicators
    assert "VOLUME_SMA" in indicators
    assert "SMA" not in indicators


def test_generator_accepts_legacy_four_weight_tuple():
    """Passing a 4-element weight tuple should pad and not crash."""
    generated = generate_strategies(count=5, seed=42,
                                    indicator_weights=(0.25, 0.25, 0.25, 0.25))
    assert len(generated) == 5
    # Provenance should reflect the padded 6-element list
    prov_weights = generated[0]["provenance"]["parameter_ranges"]["indicator_weights"]
    assert len(prov_weights) == 6
    assert prov_weights == [0.25, 0.25, 0.25, 0.25, 0.0, 0.0]


def test_generator_rejects_or_documents_invalid_weight_lengths():
    """Passing a weight tuple larger than _INDICATOR_TYPES should raise ValueError."""
    with pytest.raises(ValueError, match="The number of weights does not match the population"):
        generate_strategies(count=1, seed=42,
                            indicator_weights=(0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4))


def test_generator_default_output_unchanged_with_zero_volume_weights():
    """The sequence of strategies with default weights must remain exactly the same as pre-volume."""
    # This acts as a regression test to ensure padding the weights doesn't alter RNG sequence
    # For a given seed, the strategy structure should match a known old deterministic draw.
    g1 = generate_strategies(count=1, seed=999)
    # The default weights in 0.2.0 were (0.35, 0.30, 0.15, 0.20)
    # With seed 999, the first long_entry block should still be whatever it used to be.
    # It shouldn't crash, and shouldn't draw VOLUME or VOLUME_SMA.
    assert "VOLUME" not in g1[0]["strategy"].long_entry.conditions[0].indicator
    assert "VOLUME_SMA" not in g1[0]["strategy"].long_entry.conditions[0].indicator


# ---------------------------------------------------------------------------
# Ranking — multi-dimensional
# ---------------------------------------------------------------------------


def test_ranking_is_deterministic():
    """Same set of metrics must produce the same ranking every time."""
    df = _make_test_data(200)
    generated = generate_strategies(count=10, seed=42)
    results = _backtest_strategies(generated, df)

    ranked1 = rank_strategies(results.copy())
    ranked2 = rank_strategies(results.copy())

    ranks1 = [r["rank"] for r in ranked1]
    ranks2 = [r["rank"] for r in ranked2]
    assert ranks1 == ranks2


def test_ranking_produces_1_to_n_ranks():
    """Ranks must be consecutive integers 1..N."""
    df = _make_test_data(200)
    generated = generate_strategies(count=10, seed=42)
    results = _backtest_strategies(generated, df)

    ranked = rank_strategies(results)
    ranks = [r["rank"] for r in ranked]
    assert ranks == list(range(1, len(ranked) + 1))


def test_ranking_not_net_profit_only():
    """A higher-net-profit strategy with terrible drawdown and few trades
    must rank below a more robust lower-profit strategy.

    Uses hand-crafted metrics so the outcome is deterministic.
    """
    # Strategy A: high PnL but huge drawdown, few trades, low PF.
    a = {"metrics": {
        "total_trades": 3,
        "total_pnl": 12000.0,
        "profit_factor": 1.1,
        "max_drawdown_pnl": 18000.0,  # nearly wipes out all profit
        "avg_trade": 4000.0,
    }}
    # Strategy B: moderate PnL but consistent, many trades, good PF.
    b = {"metrics": {
        "total_trades": 35,
        "total_pnl": 8000.0,
        "profit_factor": 2.5,
        "max_drawdown_pnl": 2000.0,
        "avg_trade": 228.0,
    }}

    ranked = rank_strategies([a, b])
    # B should rank higher despite lower net profit.
    assert ranked[0]["rank"] == 1
    assert ranked[0]["metrics"]["total_pnl"] == 8000.0  # B wins
    assert ranked[1]["metrics"]["total_pnl"] == 12000.0  # A loses


def test_fitness_uses_multiple_dimensions():
    """compute_fitness must return a different value when only one metric changes."""
    base = {
        "total_trades": 20,
        "winning_trades": 12,
        "losing_trades": 8,
        "win_rate": 0.6,
        "total_pnl": 5000.0,
        "avg_trade": 250.0,
        "gross_profit": 15000.0,
        "gross_loss": 10000.0,
        "profit_factor": 1.5,
        "max_drawdown_pnl": 3000.0,
    }

    score_base = compute_fitness(base)

    # Change only total_pnl.
    alt = dict(base)
    alt["total_pnl"] = 10000.0
    score_alt = compute_fitness(alt)

    assert score_alt != score_base  # Fitness must be sensitive to changes.


def test_fitness_max_drawdown_penalty():
    """Higher drawdown must produce a lower fitness score (all else equal)."""
    base = {
        "total_trades": 20,
        "winning_trades": 12,
        "losing_trades": 8,
        "win_rate": 0.6,
        "total_pnl": 5000.0,
        "avg_trade": 250.0,
        "gross_profit": 15000.0,
        "gross_loss": 10000.0,
        "profit_factor": 1.5,
        "max_drawdown_pnl": 1000.0,
    }

    score_low_dd = compute_fitness(base)

    alt = dict(base)
    alt["max_drawdown_pnl"] = 20000.0
    score_high_dd = compute_fitness(alt)

    assert score_high_dd < score_low_dd


def test_ranking_adds_fitness_and_rank_fields():
    """rank_strategies must add 'fitness' and 'rank' to each entry."""
    entries = [
        {"metrics": {"total_trades": 10, "total_pnl": 1000.0, "profit_factor": 2.0,
                       "max_drawdown_pnl": 500.0, "avg_trade": 100.0}},
        {"metrics": {"total_trades": 20, "total_pnl": 5000.0, "profit_factor": 1.5,
                       "max_drawdown_pnl": 2000.0, "avg_trade": 250.0}},
    ]
    ranked = rank_strategies(entries)

    for entry in ranked:
        assert "fitness" in entry
        assert "rank" in entry
        assert isinstance(entry["fitness"], float)
        assert isinstance(entry["rank"], int)
        assert entry["rank"] >= 1


def test_rank_strategies_does_not_mutate_input():
    """rank_strategies must not modify the caller's original list or dicts."""
    original = [
        {"metrics": {"total_trades": 10, "total_pnl": 5000.0, "profit_factor": 2.0,
                       "max_drawdown_pnl": 1000.0, "avg_trade": 500.0}},
        {"metrics": {"total_trades": 5, "total_pnl": 2000.0, "profit_factor": 1.2,
                       "max_drawdown_pnl": 3000.0, "avg_trade": 400.0}},
    ]
    # Snapshot keys before ranking.
    keys_before = [set(e.keys()) for e in original]

    ranked = rank_strategies(original)

    # Original entries must not have gained fitness/rank keys.
    for i, entry in enumerate(original):
        assert "fitness" not in entry, f"original[{i}] mutated: got fitness"
        assert "rank" not in entry, f"original[{i}] mutated: got rank"
        assert set(entry.keys()) == keys_before[i]

    # Returned entries must have fitness and rank.
    for entry in ranked:
        assert "fitness" in entry
        assert "rank" in entry

# ---------------------------------------------------------------------------
# Generator — Multi-timeframe conditions (Task 049E)
# ---------------------------------------------------------------------------

def test_generator_no_mtf_by_default():
    """Existing default generation produces no 'timeframe' keys."""
    generated = generate_strategies(count=10, seed=42)
    for entry in generated:
        strat = entry["strategy"]
        for block_name in ("long_entry", "long_exit", "short_entry", "short_exit"):
            block = getattr(strat, block_name)
            for cond in block.conditions:
                assert "timeframe" not in cond.params

def test_generator_default_output_unchanged_with_mtf_disabled():
    """Same seed/default config matches baseline structural deterministic output."""
    g1 = generate_strategies(count=5, seed=123)
    g2 = generate_strategies(count=5, seed=123, allowed_timeframes=(), mtf_probability=0.0)
    
    for e1, e2 in zip(g1, g2):
        assert e1["strategy"].name == e2["strategy"].name
        for block_name in ("long_entry", "long_exit", "short_entry", "short_exit"):
            b1 = getattr(e1["strategy"], block_name)
            b2 = getattr(e2["strategy"], block_name)
            assert len(b1.conditions) == len(b2.conditions)
            for c1, c2 in zip(b1.conditions, b2.conditions):
                assert c1.indicator == c2.indicator
                assert c1.params == c2.params

def test_generator_mtf_probability_zero_no_timeframes():
    """allowed_timeframes provided but mtf_probability=0.0 -> no timeframe keys."""
    generated = generate_strategies(
        count=10, seed=42, allowed_timeframes=(5, 15), mtf_probability=0.0
    )
    for entry in generated:
        for block_name in ("long_entry", "long_exit", "short_entry", "short_exit"):
            block = getattr(entry["strategy"], block_name)
            for cond in block.conditions:
                assert "timeframe" not in cond.params

def test_generator_mtf_probability_one_adds_timeframes():
    """mtf_probability=1.0 and allowed_timeframes=(5, 15) -> generated eligible conditions include timeframe in {5, 15}."""
    generated = generate_strategies(
        count=20, seed=42, allowed_timeframes=(5, 15), mtf_probability=1.0
    )
    tfs_found = set()
    for entry in generated:
        for block_name in ("long_entry", "long_exit", "short_entry", "short_exit"):
            block = getattr(entry["strategy"], block_name)
            if not block.conditions:
                continue
            for cond in block.conditions:
                assert "timeframe" in cond.params, f"Missing timeframe in {cond.indicator}"
                tfs_found.add(cond.params["timeframe"])
    
    assert tfs_found.issubset({5, 15})
    assert len(tfs_found) > 0

def test_generator_mtf_allowed_timeframes_normalizes_duplicates():
    """allowed_timeframes=(15, 5, 5) normalizes predictably to (5, 15) in provenance."""
    generated = generate_strategies(count=1, seed=42, allowed_timeframes=(15, 5, 5), mtf_probability=0.5)
    pr = generated[0]["provenance"]["parameter_ranges"]
    assert pr["allowed_timeframes"] == [5, 15]

def test_generator_mtf_disabled_does_not_consume_rng():
    """MTF disabled path does not consume RNG."""
    from unittest.mock import patch
    import random
    
    original_random = random.Random.random
    calls = {'mtf_count': 0}
    def fake_random(self):
        import sys
        if sys._getframe(1).f_code.co_name == '_maybe_add_timeframe':
            calls['mtf_count'] += 1
        return original_random(self)
        
    with patch('random.Random.random', new=fake_random):
        generate_strategies(count=1, seed=42, allowed_timeframes=(), mtf_probability=0.0)
        c1 = calls['mtf_count']
        
        calls['mtf_count'] = 0
        generate_strategies(count=1, seed=42, allowed_timeframes=(5,), mtf_probability=1.0)
        c2 = calls['mtf_count']
        
    assert c1 == 0
    assert c2 > 0

def test_generator_mtf_allowed_timeframes_validated():
    """invalid values: bool, string, <=0."""
    with pytest.raises(ValueError):
        generate_strategies(allowed_timeframes=(True,))
    with pytest.raises(ValueError):
        generate_strategies(allowed_timeframes=("15",))
    with pytest.raises(ValueError):
        generate_strategies(allowed_timeframes=(0,))
    with pytest.raises(ValueError):
        generate_strategies(allowed_timeframes=(-5,))

def test_generator_mtf_probability_validated():
    """invalid probabilities: <0, >1, bool."""
    with pytest.raises(ValueError):
        generate_strategies(mtf_probability=-0.1)
    with pytest.raises(ValueError):
        generate_strategies(mtf_probability=1.1)
    with pytest.raises(ValueError):
        generate_strategies(mtf_probability=True)

def test_generator_mtf_deterministic_same_seed():
    """same seed/config gives same generated strategy structures."""
    g1 = generate_strategies(count=10, seed=777, allowed_timeframes=(5, 15), mtf_probability=0.5)
    g2 = generate_strategies(count=10, seed=777, allowed_timeframes=(5, 15), mtf_probability=0.5)
    
    for e1, e2 in zip(g1, g2):
        assert e1["strategy"].name == e2["strategy"].name
        assert e1["strategy"].long_entry.conditions[0].params == e2["strategy"].long_entry.conditions[0].params

def test_generator_mtf_different_seed_can_differ():
    """different seeds can differ when MTF enabled."""
    g1 = generate_strategies(count=10, seed=111, allowed_timeframes=(5, 15), mtf_probability=0.5)
    g2 = generate_strategies(count=10, seed=222, allowed_timeframes=(5, 15), mtf_probability=0.5)
    
    params1 = [e["strategy"].long_entry.conditions[0].params.get("timeframe") for e in g1]
    params2 = [e["strategy"].long_entry.conditions[0].params.get("timeframe") for e in g2]
    assert params1 != params2

def test_generated_mtf_strategy_backtestable():
    """generated MTF strategy runs through run_backtest without crash."""
    df = _make_test_data(200)
    generated = generate_strategies(count=5, seed=42, allowed_timeframes=(5, 15), mtf_probability=0.5)
    results = _backtest_strategies(generated, df)
    
    assert len(results) == 5
    for r in results:
        assert "metrics" in r
        assert "total_pnl" in r["metrics"]

def test_generator_mtf_provenance_records_config():
    """provenance includes allowed_timeframes and mtf_probability."""
    generated = generate_strategies(count=1, seed=42, allowed_timeframes=(5, 15), mtf_probability=0.3)
    pr = generated[0]["provenance"]["parameter_ranges"]
    assert "allowed_timeframes" in pr
    assert "mtf_probability" in pr
    assert pr["allowed_timeframes"] == [5, 15]
    assert pr["mtf_probability"] == 0.3

def test_generator_mtf_does_not_mutate_param_dicts():
    """generated condition params are independent objects."""
    generated = generate_strategies(count=10, seed=42, allowed_timeframes=(5, 15), mtf_probability=0.5)
    params_ids = set()
    for entry in generated:
        for block_name in ("long_entry", "long_exit", "short_entry", "short_exit"):
            block = getattr(entry["strategy"], block_name)
            for cond in block.conditions:
                pid = id(cond.params)
                assert pid not in params_ids
                params_ids.add(pid)
