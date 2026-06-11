"""Tests for StrategyService fitness weight configuration."""

from __future__ import annotations

from app.services import strategy_service as strategy_service_module
from app.services.strategy_service import StrategyService
from strategy_engine.ranking import DEFAULT_WEIGHTS, compute_fitness


def test_default_weights_match_defaults():
    """Default service weights must equal DEFAULT_WEIGHTS."""
    svc = StrategyService()
    assert svc.get_fitness_weights() == DEFAULT_WEIGHTS


def test_get_weights_returns_copy():
    """get_fitness_weights must return a defensive copy."""
    svc = StrategyService()
    weights = svc.get_fitness_weights()

    weights["total_pnl"] = 0.99

    assert svc.get_fitness_weights()["total_pnl"] == DEFAULT_WEIGHTS["total_pnl"]


def test_update_valid_key():
    """Updating a valid key must change only that key."""
    svc = StrategyService()

    svc.update_fitness_weights({"profit_factor": 0.75})

    weights = svc.get_fitness_weights()
    assert weights["profit_factor"] == 0.75
    assert weights["total_pnl"] == DEFAULT_WEIGHTS["total_pnl"]
    assert weights["max_drawdown_pnl"] == DEFAULT_WEIGHTS["max_drawdown_pnl"]


def test_update_clamps_above_1():
    """Values above 1.0 must be clamped to 1.0."""
    svc = StrategyService()

    svc.update_fitness_weights({"total_pnl": 5.0})

    assert svc.get_fitness_weights()["total_pnl"] == 1.0


def test_update_clamps_below_0():
    """Values below 0.0 must be clamped to 0.0."""
    svc = StrategyService()

    svc.update_fitness_weights({"total_pnl": -1.0})

    assert svc.get_fitness_weights()["total_pnl"] == 0.0


def test_update_ignores_unknown_key():
    """Unknown keys must be ignored."""
    svc = StrategyService()

    svc.update_fitness_weights({"nonexistent": 0.5})

    assert "nonexistent" not in svc.get_fitness_weights()


def test_update_ignores_non_numeric():
    """Non-numeric values must be ignored."""
    svc = StrategyService()

    svc.update_fitness_weights({"profit_factor": "abc"})

    assert svc.get_fitness_weights()["profit_factor"] == DEFAULT_WEIGHTS["profit_factor"]


def test_update_ignores_bool_values():
    """Boolean values must not be accepted as numeric weights."""
    svc = StrategyService()

    svc.update_fitness_weights({"profit_factor": False, "total_pnl": True})

    weights = svc.get_fitness_weights()
    assert weights["profit_factor"] == DEFAULT_WEIGHTS["profit_factor"]
    assert weights["total_pnl"] == DEFAULT_WEIGHTS["total_pnl"]


def test_update_preserves_missing_keys():
    """Keys not in the update dict must preserve their existing values."""
    svc = StrategyService()

    svc.update_fitness_weights({"profit_factor": 0.3})

    weights = svc.get_fitness_weights()
    assert weights["total_pnl"] == DEFAULT_WEIGHTS["total_pnl"]
    assert weights["max_drawdown_pnl"] == DEFAULT_WEIGHTS["max_drawdown_pnl"]
    assert weights["avg_trade"] == DEFAULT_WEIGHTS["avg_trade"]
    assert weights["total_trades"] == DEFAULT_WEIGHTS["total_trades"]


def test_get_ranked_strategies_passes_service_weights(monkeypatch):
    """get_ranked_strategies must forward current service weights into ranking."""
    captured_weights = []

    def fake_generate_strategies(count, seed):
        return []

    def fake_rank_strategies(backtest_results, weights=None):
        captured_weights.append(weights)
        return []

    monkeypatch.setattr(strategy_service_module, "generate_strategies", fake_generate_strategies)
    monkeypatch.setattr(strategy_service_module, "rank_strategies", fake_rank_strategies)

    svc = StrategyService()
    svc.update_fitness_weights({"profit_factor": 0.75, "total_pnl": 0.0})

    ranked, is_mock = svc.get_ranked_strategies()

    assert ranked == []
    assert is_mock is True
    assert captured_weights == [svc.get_fitness_weights()]


def test_zero_weight_dimension_excluded():
    """A dimension weighted 0 must not affect score."""
    metrics = {"total_pnl": 5000, "profit_factor": 2.0}
    weights = {
        "total_pnl": 1.0,
        "profit_factor": 0.0,
        "max_drawdown_pnl": 0.0,
        "avg_trade": 0.0,
        "total_trades": 0.0,
    }

    score = compute_fitness(metrics, weights)

    assert abs(score - 0.1) < 1e-6


def test_all_zero_weights_returns_zero():
    """All-zero weights must produce a fitness score of 0.0."""
    metrics = {"total_pnl": 5000, "profit_factor": 2.0}
    zero_weights = {
        "total_pnl": 0.0,
        "profit_factor": 0.0,
        "max_drawdown_pnl": 0.0,
        "avg_trade": 0.0,
        "total_trades": 0.0,
    }

    assert compute_fitness(metrics, zero_weights) == 0.0
