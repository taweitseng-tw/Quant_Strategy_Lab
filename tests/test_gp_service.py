"""Tests for GP search service integration."""

import sys
import pandas as pd
import numpy as np

from app.services.gp_service import run_gp_search, GPSearchConfig, GPSearchResult
from core.models.strategy import Strategy

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

def test_gp_service_has_no_pyside_import():
    with open("app/services/gp_service.py", "r", encoding="utf-8") as f:
        content = f.read()
    assert "PySide6" not in content
    assert "sqlite" not in content.lower()
    assert "repository" not in content

import pytest
def test_gp_service_result_has_config_snapshot():
    df = _make_test_data(50)
    cfg = GPSearchConfig(population_size=2, max_generations=1, base_seed=42)
    res = run_gp_search(df, cfg)
    
    assert res.config_snapshot["population_size"] == 2
    assert res.config_snapshot["max_generations"] == 1
    assert "fitness_weights" in res.config_snapshot

def test_gp_service_result_generation_history_shape():
    df = _make_test_data(50)
    cfg = GPSearchConfig(population_size=2, max_generations=3, base_seed=42)
    res = run_gp_search(df, cfg)
    
    assert res.generation_count == 3
    assert len(res.generation_best_scores) == 3
    assert len(res.generation_avg_scores) == 3
    assert all(isinstance(s, float) for s in res.generation_best_scores)
    assert all(isinstance(s, float) for s in res.generation_avg_scores)

from unittest import mock

def test_gp_service_uses_run_gp_path():
    df = _make_test_data(50)
    cfg = GPSearchConfig(population_size=2, max_generations=1, base_seed=42)
    
    with mock.patch("app.services.gp_service.run_gp") as mock_run_gp:
        # Give it a fake return so it doesn't crash unpacking
        from strategy_engine.gp_evolution import GPResult, GPConfig, GPIndividual
        from strategy_engine.gp import GPLogicNode
        dummy_ind = GPIndividual("dummy", GPLogicNode("AND"), GPLogicNode("AND"), GPLogicNode("AND"), GPLogicNode("AND"))
        mock_run_gp.return_value = GPResult(
            final_population=[dummy_ind, dummy_ind],
            final_scores=[1.0, 1.0],
            best_individual=dummy_ind,
            best_score=1.0,
            generations=[],
            config=GPConfig()
        )
        
        run_gp_search(df, cfg)
        mock_run_gp.assert_called_once()

def test_gp_service_small_dataset_graceful_behavior():
    # Only 5 bars, should not crash, probably returns 0.0 or negative score due to no trades
    df = _make_test_data(5)
    cfg = GPSearchConfig(population_size=2, max_generations=1, base_seed=42)
    res = run_gp_search(df, cfg)
    assert isinstance(res.best_score, float)
    assert np.isfinite(res.best_score)

def test_gp_service_best_score_is_numeric():
    df = _make_test_data(50)
    cfg = GPSearchConfig(population_size=2, max_generations=1, base_seed=42)
    res = run_gp_search(df, cfg)
    
    assert isinstance(res.best_score, (float, int))
    assert not np.isnan(res.best_score)
    assert not np.isinf(res.best_score)

def test_gp_service_result_can_be_rendered_by_future_ui_without_engine_objects_except_strategy():
    df = _make_test_data(50)
    cfg = GPSearchConfig(population_size=2, max_generations=1, base_seed=42)
    res = run_gp_search(df, cfg)
    
    # Check types of attributes on GPSearchResult
    assert isinstance(res.best_strategy, Strategy)
    assert isinstance(res.best_score, float)
    assert isinstance(res.generation_count, int)
    assert isinstance(res.final_population_size, int)
    assert isinstance(res.generation_best_scores, list)
    assert isinstance(res.generation_avg_scores, list)
    assert isinstance(res.config_snapshot, dict)

def test_run_gp_search_returns_structured_result():
    df = _make_test_data(50)
    cfg = GPSearchConfig(population_size=2, max_generations=1, base_seed=42)
    res = run_gp_search(df, cfg)
    
    assert isinstance(res, GPSearchResult)
    assert isinstance(res.best_score, float)
    assert res.generation_count == 1
    assert res.final_population_size == 2
    assert "base_seed" in res.config_snapshot

def test_run_gp_search_best_strategy_is_strategy():
    df = _make_test_data(50)
    cfg = GPSearchConfig(population_size=2, max_generations=1, base_seed=42)
    res = run_gp_search(df, cfg)
    
    assert isinstance(res.best_strategy, Strategy)
    assert isinstance(res.best_strategy.name, str)
    assert "gp_" in res.best_strategy.name

def test_run_gp_search_generation_history_present():
    df = _make_test_data(50)
    cfg = GPSearchConfig(population_size=3, max_generations=2, base_seed=42)
    res = run_gp_search(df, cfg)
    
    assert len(res.generation_best_scores) == 2
    assert len(res.generation_avg_scores) == 2
    assert all(isinstance(s, float) for s in res.generation_best_scores)

def test_run_gp_search_is_deterministic():
    df = _make_test_data(50)
    cfg = GPSearchConfig(population_size=3, max_generations=2, base_seed=42)
    
    res1 = run_gp_search(df, cfg)
    res2 = run_gp_search(df, cfg)
    
    assert res1.best_score == res2.best_score
    assert res1.generation_best_scores == res2.generation_best_scores
    # Compare name at least
    assert res1.best_strategy.name == res2.best_strategy.name

def test_run_gp_search_differs_by_seed_when_possible():
    df = _make_test_data(50)
    cfg1 = GPSearchConfig(population_size=3, max_generations=2, base_seed=1)
    cfg2 = GPSearchConfig(population_size=3, max_generations=2, base_seed=2)
    
    res1 = run_gp_search(df, cfg1)
    res2 = run_gp_search(df, cfg2)
    
    import json
    import dataclasses
    # Strategy logic should differ given different seeds, even if they happen to have the same rank/name index
    c1 = json.dumps(dataclasses.asdict(res1.best_strategy)["long_entry"])
    c2 = json.dumps(dataclasses.asdict(res2.best_strategy)["long_entry"])
    assert c1 != c2

def test_gp_service_uses_existing_fitness_adapter_path():
    df = _make_test_data(50)
    cfg = GPSearchConfig(
        population_size=2, max_generations=1, base_seed=42,
        use_elimination=True, elimination_penalty=0.1
    )
    res1 = run_gp_search(df, cfg)
    
    cfg.use_elimination = False
    res2 = run_gp_search(df, cfg)
    
    assert isinstance(res1.best_score, float)
    assert isinstance(res2.best_score, float)

def test_gp_service_does_not_modify_input_dataframe():
    df = _make_test_data(50)
    df_copy = df.copy(deep=True)
    cfg = GPSearchConfig(population_size=2, max_generations=1, base_seed=42)
    run_gp_search(df, cfg)
    pd.testing.assert_frame_equal(df, df_copy)
