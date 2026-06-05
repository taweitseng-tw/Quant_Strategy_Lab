"""Tests for GA search service orchestration — Task 031C."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.models.strategy import Strategy
from app.services.ga_service import (
    GASearchConfig,
    GASearchResult,
    run_ga_search,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_df(n_bars: int = 200) -> pd.DataFrame:
    """Small deterministic OHLCV dataset for fast GA evaluation."""
    rng = np.random.default_rng(42)
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="1min")
    close = 100.0 + np.cumsum(rng.normal(0.01, 0.4, n_bars))
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_ga_search_returns_structured_result():
    """run_ga_search must return a GASearchResult with all required fields."""
    df = _make_df(150)
    cfg = GASearchConfig(population_size=4, max_generations=2, base_seed=7)

    result = run_ga_search(df, config=cfg)

    assert isinstance(result, GASearchResult)
    assert isinstance(result.best_strategy, Strategy)
    assert isinstance(result.best_score, float)
    assert result.generation_count == 2
    assert result.final_population_size == 4
    assert len(result.generation_best_scores) == 2
    assert len(result.generation_avg_scores) == 2
    assert isinstance(result.config_snapshot, dict)


def test_ga_search_deterministic_with_same_seed():
    """Same config + seed must produce identical results."""
    df = _make_df(150)
    cfg = GASearchConfig(population_size=4, max_generations=2, base_seed=11)

    r1 = run_ga_search(df, config=cfg)
    r2 = run_ga_search(df, config=cfg)

    assert r1.best_score == r2.best_score
    assert asdict(r1.best_strategy) == asdict(r2.best_strategy)
    assert r1.generation_best_scores == r2.generation_best_scores
    assert r1.generation_avg_scores == r2.generation_avg_scores


def test_ga_search_different_seed_produces_different_results():
    """Different seeds should produce different populations / results."""
    df = _make_df(150)
    r1 = run_ga_search(df, config=GASearchConfig(population_size=4, max_generations=2, base_seed=1))
    r2 = run_ga_search(df, config=GASearchConfig(population_size=4, max_generations=2, base_seed=999))

    # Very unlikely to be identical with different seeds.
    assert asdict(r1.best_strategy) != asdict(r2.best_strategy) or r1.best_score != r2.best_score


def test_ga_search_config_snapshot_preserved():
    """Config snapshot must record the service-level config."""
    df = _make_df(100)
    cfg = GASearchConfig(population_size=4, max_generations=2, base_seed=42, mutation_prob=0.5)

    result = run_ga_search(df, config=cfg)

    assert result.config_snapshot["population_size"] == 4
    assert result.config_snapshot["max_generations"] == 2
    assert result.config_snapshot["mutation_prob"] == 0.5
    assert result.config_snapshot["base_seed"] == 42


def test_ga_search_generation_best_scores_non_decreasing_or_stable():
    """Elite preservation means the generation-best should never decrease."""
    df = _make_df(200)
    cfg = GASearchConfig(population_size=6, elite_count=2, max_generations=4, base_seed=33)

    result = run_ga_search(df, config=cfg)

    best_scores = result.generation_best_scores
    for i in range(1, len(best_scores)):
        # With elitism, the best score can only stay or improve.
        assert best_scores[i] >= best_scores[i - 1] - 1e-9, (
            f"Generation {i} best score {best_scores[i]} < previous {best_scores[i - 1]}"
        )


def test_ga_search_defaults_are_fast():
    """Default GASearchConfig must have small population and few generations."""
    cfg = GASearchConfig()
    assert cfg.population_size <= 20
    assert cfg.max_generations <= 5


def test_ga_service_has_no_pyside_imports():
    """Service file must not import PySide6."""
    source = Path("app/services/ga_service.py").read_text(encoding="utf-8")
    assert "PySide6" not in source
