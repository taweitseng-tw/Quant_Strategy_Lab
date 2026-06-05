"""Tests for GA fitness adapter — Task 031B."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from core.models.instrument import InstrumentProfile
from core.models.strategy import Condition, Strategy, StrategyBlock
from strategy_engine.ga import GAConfig, run_ga, create_initial_population
from strategy_engine.ga_fitness import GAFitnessConfig, make_fitness_adapter
from validation_engine.elimination import EliminationConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_df(n_bars: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(99)
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="1min")
    close = 100.0 + np.cumsum(rng.normal(0.03, 0.5, n_bars))
    close = np.maximum(close, 10.0)
    noise = rng.uniform(0.2, 1.0, n_bars)
    return pd.DataFrame({
        "datetime": times,
        "open":  close - noise * 0.3,
        "high":  close + noise,
        "low":   close - noise,
        "close": close,
        "volume": rng.integers(500, 5000, n_bars),
    })


def _strong_strategy() -> Strategy:
    """SMA crossover on trending data — should produce positive PnL."""
    return Strategy(
        name="strong",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 5}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 5}, operator="<"),
        ], logic="AND"),
    )


def _weak_strategy() -> Strategy:
    """RSI with extreme threshold — trades rarely, poor performance."""
    return Strategy(
        name="weak",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="RSI", params={"period": 14}, operator="<", right=5.0),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="RSI", params={"period": 14}, operator=">", right=95.0),
        ], logic="AND"),
    )


# ---------------------------------------------------------------------------
# Core adapter tests
# ---------------------------------------------------------------------------


def test_adapter_returns_callable():
    df = _make_df()
    fn = make_fitness_adapter(df)
    assert callable(fn)


def test_strong_strategy_scores_higher_than_weak():
    df = _make_df(200)
    fn = make_fitness_adapter(df, GAFitnessConfig(use_elimination=False, use_walk_forward=False))
    strong_score = fn(_strong_strategy())
    weak_score = fn(_weak_strategy())
    assert strong_score > weak_score, f"strong={strong_score:.4f} <= weak={weak_score:.4f}"


def test_score_is_deterministic():
    df = _make_df(200)
    fn = make_fitness_adapter(df)
    strat = _strong_strategy()
    assert fn(strat) == fn(strat)


def test_eliminated_strategy_penalised():
    df = _make_df(200)
    # Strict elimination: requires very high PnL → most strategies fail.
    strict_elim = EliminationConfig(min_total_pnl=1_000_000.0, min_profit_factor=10.0)
    cfg = GAFitnessConfig(
        use_elimination=True,
        elimination_config=strict_elim,
        elimination_penalty=0.30,
        use_walk_forward=False,
    )
    fn = make_fitness_adapter(df, cfg)
    score = fn(_strong_strategy())

    # With elimination disabled, same strategy should score higher.
    cfg_no_elim = GAFitnessConfig(use_elimination=False, use_walk_forward=False)
    fn_no = make_fitness_adapter(df, cfg_no_elim)
    score_no = fn_no(_strong_strategy())

    # Penalised score must be strictly lower because the strategy is
    # eliminated under the strict config.
    assert score < score_no, f"penalised={score:.4f} >= unpenalised={score_no:.4f}"


def test_walk_forward_bonus_added():
    df = _make_df(200)
    cfg_with = GAFitnessConfig(
        use_elimination=False,
        use_walk_forward=True,
        wf_train_bars=60,
        wf_test_bars=30,
        wf_bonus_max=0.15,
    )
    cfg_without = GAFitnessConfig(use_elimination=False, use_walk_forward=False)

    fn_with = make_fitness_adapter(df, cfg_with)
    fn_without = make_fitness_adapter(df, cfg_without)

    score_with = fn_with(_strong_strategy())
    score_without = fn_without(_strong_strategy())

    # Bonus must not decrease the score.
    assert score_with >= score_without, f"wf={score_with:.4f} < base={score_without:.4f}"


def test_walk_forward_receives_instrument_and_backtest_kwargs(monkeypatch):
    """WF scoring must use the same instrument/cost assumptions as baseline."""
    df = _make_df(200)
    seen = {}

    class DummyWF:
        window_count = 1
        pass_rate = 0.5

    def fake_walk_forward(strategy, data, **kwargs):
        seen.update(kwargs)
        return DummyWF()

    instrument = InstrumentProfile(
        symbol="TST",
        point_value=10.0,
        tick_size=0.25,
        commission_value=2.0,
        slippage_ticks=1.0,
    )
    monkeypatch.setattr("strategy_engine.ga_fitness.walk_forward", fake_walk_forward)
    fn = make_fitness_adapter(
        df,
        GAFitnessConfig(use_elimination=False, use_walk_forward=True),
        instrument=instrument,
        commission=7.0,
        slippage_ticks=2.0,
    )

    fn(_strong_strategy())

    assert seen["instrument"] is instrument
    assert seen["commission"] == 7.0
    assert seen["slippage_ticks"] == 2.0


def test_walk_forward_disabled_no_bonus():
    df = _make_df(200)
    fn = make_fitness_adapter(
        df,
        GAFitnessConfig(use_elimination=False, use_walk_forward=False),
    )
    fn_wf = make_fitness_adapter(
        df,
        GAFitnessConfig(use_elimination=False, use_walk_forward=True, wf_bonus_max=0.15),
    )
    strat = _strong_strategy()
    base = fn(strat)
    wf_score = fn_wf(strat)
    # With bonus, score should be >= base (never lower).
    assert wf_score >= base


def test_score_is_finite_for_no_trade_edge_case():
    """Strategies that produce zero trades must still return a finite score."""
    df = _make_df(50)
    # Use tiny SMA period that won't warm up on a short df.
    no_trade = Strategy(
        name="no_trade",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 200}, operator=">"),
        ], logic="AND"),
    )
    fn = make_fitness_adapter(df, GAFitnessConfig(use_elimination=False, use_walk_forward=False))
    score = fn(no_trade)
    assert np.isfinite(score)
    assert score >= 0.0


def test_custom_weights_forwarded():
    """Custom fitness weights must produce different scores than defaults."""
    df = _make_df(200)
    custom_w = {"total_pnl": 1.0, "profit_factor": 0.0, "max_drawdown_pnl": 0.0,
                 "avg_trade": 0.0, "total_trades": 0.0}
    fn_custom = make_fitness_adapter(
        df,
        GAFitnessConfig(fitness_weights=custom_w, use_elimination=False, use_walk_forward=False),
    )
    fn_default = make_fitness_adapter(
        df,
        GAFitnessConfig(use_elimination=False, use_walk_forward=False),
    )
    strat = _strong_strategy()
    assert fn_custom(strat) != fn_default(strat)


# ---------------------------------------------------------------------------
# GA integration smoke
# ---------------------------------------------------------------------------


def test_adapter_works_with_run_ga():
    df = _make_df(200)
    fn = make_fitness_adapter(
        df,
        GAFitnessConfig(
            use_elimination=True,
            elimination_config=EliminationConfig(min_trade_count=0),
            use_walk_forward=False,
        ),
    )
    cfg = GAConfig(population_size=4, elite_count=1, max_generations=2,
                   mutation_prob=1.0, base_seed=77)
    initial = create_initial_population(4, seed=77, config=cfg)

    result = run_ga(initial, fn, config=cfg)

    assert len(result.final_population) == 4
    assert len(result.generations) == 2
    assert isinstance(result.best_strategy, Strategy)
    assert np.isfinite(result.best_score)


def test_ga_integration_is_deterministic():
    df = _make_df(200)
    fn = make_fitness_adapter(df, GAFitnessConfig(use_elimination=False, use_walk_forward=False))
    cfg = GAConfig(population_size=4, elite_count=1, max_generations=2,
                   mutation_prob=1.0, base_seed=77)
    initial = create_initial_population(4, seed=77, config=cfg)

    r1 = run_ga(initial, fn, config=cfg)
    r2 = run_ga(initial, fn, config=cfg)

    assert r1.final_scores == r2.final_scores
    assert r1.best_score == r2.best_score


# ---------------------------------------------------------------------------
# Guard
# ---------------------------------------------------------------------------


def test_ga_fitness_has_no_pyside_imports():
    source = Path("strategy_engine/ga_fitness.py").read_text(encoding="utf-8")
    assert "PySide6" not in source


def test_ga_integration_caching_is_deterministic(monkeypatch):
    from backtest_engine.runner import IndicatorCache
    df = _make_df(200)
    
    # 1. Run without cache (mock it out)
    monkeypatch.setattr("strategy_engine.ga_fitness.IndicatorCache", lambda d: None)
    fn_no_cache = make_fitness_adapter(df, GAFitnessConfig(use_elimination=False, use_walk_forward=False))
    
    cfg = GAConfig(population_size=4, elite_count=1, max_generations=2,
                   mutation_prob=1.0, base_seed=77)
    initial1 = create_initial_population(4, seed=77, config=cfg)
    r_no_cache = run_ga(initial1, fn_no_cache, config=cfg)
    
    # 2. Run with cache
    monkeypatch.setattr("strategy_engine.ga_fitness.IndicatorCache", IndicatorCache)
    fn_with_cache = make_fitness_adapter(df, GAFitnessConfig(use_elimination=False, use_walk_forward=False))
    
    initial2 = create_initial_population(4, seed=77, config=cfg)
    r_with_cache = run_ga(initial2, fn_with_cache, config=cfg)
    
    # Assert equivalence
    assert r_no_cache.final_scores == r_with_cache.final_scores
    assert r_no_cache.best_score == r_with_cache.best_score

