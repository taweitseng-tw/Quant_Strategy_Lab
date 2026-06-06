"""Tests for StrategyService elimination configuration API — Task 041C."""

import pytest
from app.services.strategy_service import StrategyService
from validation_engine.elimination import EliminationConfig


def test_strategy_service_default_elimination_config_unchanged():
    """Verify StrategyService initializes with DEFAULT_ELIMINATION_CONFIG."""
    svc = StrategyService()
    cfg = svc.get_elimination_config_dict()
    
    # Assert against known defaults
    assert cfg["min_trade_count"] == 5
    assert cfg["min_profit_factor"] == 0.5
    assert cfg["max_drawdown_pnl"] == 50000.0
    assert cfg["min_avg_trade"] == -500.0
    assert cfg["require_optional"] is False


def test_strategy_service_get_elimination_config_dict():
    """Verify get_elimination_config_dict returns a primitive dictionary of all keys."""
    svc = StrategyService()
    cfg = svc.get_elimination_config_dict()
    
    assert isinstance(cfg, dict)
    
    expected_keys = {
        "min_total_pnl", "min_profit_factor", "max_drawdown_pnl",
        "min_avg_trade", "min_trade_count", "min_win_rate",
        "min_oos_total_pnl", "min_oos_profit_factor",
        "min_stress_pass_rate", "min_monte_carlo_p05_pnl",
        "min_walk_forward_pass_rate", "require_optional",
        "max_oos_pf_degradation", "max_oos_drawdown_ratio",
        "max_oos_avg_trade_degradation",
    }
    assert set(cfg.keys()) == expected_keys


def test_strategy_service_update_elimination_config_accepts_dict():
    """Verify update_elimination_config accepts a dict and updates internal state."""
    svc = StrategyService()
    svc.update_elimination_config({
        "min_trade_count": 10,
        "min_profit_factor": 2.5
    })
    
    cfg = svc.get_elimination_config_dict()
    assert cfg["min_trade_count"] == 10
    assert cfg["min_profit_factor"] == 2.5


def test_strategy_service_update_elimination_config_ignores_unknown_keys():
    """Verify update_elimination_config safely ignores keys that don't exist in EliminationConfig."""
    svc = StrategyService()
    svc.update_elimination_config({
        "min_trade_count": 12,
        "unknown_magic_key": 999.0
    })
    
    cfg = svc.get_elimination_config_dict()
    assert cfg["min_trade_count"] == 12
    assert "unknown_magic_key" not in cfg


def test_strategy_service_update_elimination_config_none_disables_threshold():
    """Verify setting a threshold to None disables it."""
    svc = StrategyService()
    # It's currently 5 by default
    assert svc.get_elimination_config_dict()["min_trade_count"] == 5
    
    svc.update_elimination_config({"min_trade_count": None})
    assert svc.get_elimination_config_dict()["min_trade_count"] is None


def test_strategy_service_update_elimination_config_require_optional():
    """Verify require_optional boolean can be updated."""
    svc = StrategyService()
    assert svc.get_elimination_config_dict()["require_optional"] is False
    
    svc.update_elimination_config({"require_optional": True})
    assert svc.get_elimination_config_dict()["require_optional"] is True


def test_strategy_service_update_elimination_config_empty_dict_preserves():
    """Verify passing an empty dict preserves the existing state."""
    svc = StrategyService()
    svc.update_elimination_config({"min_trade_count": 99})
    assert svc.get_elimination_config_dict()["min_trade_count"] == 99
    
    svc.update_elimination_config({})
    assert svc.get_elimination_config_dict()["min_trade_count"] == 99


def test_strategy_service_update_elimination_config_numeric_threshold_applies():
    """Verify that updated numeric thresholds actively affect ranking elimination status."""
    svc = StrategyService()
    
    # Run with lenient defaults (some pass)
    svc.update_elimination_config({
        "min_trade_count": 0,
        "min_profit_factor": 0.0,
        "max_drawdown_pnl": 1000000.0,
        "min_avg_trade": -1000000.0
    })
    ranked, _ = svc.get_ranked_strategies()
    passed_lenient = [s for s in ranked if s["elimination_passed"]]
    
    # Run with strict thresholds (fewer or none pass)
    svc.update_elimination_config({
        "min_trade_count": 1000000,  # Impossible threshold
    })
    ranked_strict, _ = svc.get_ranked_strategies()
    passed_strict = [s for s in ranked_strict if s["elimination_passed"]]
    
    assert len(passed_strict) < len(passed_lenient)
    assert len(passed_strict) == 0


def test_get_elimination_config_dict_returns_primitives_only():
    """Verify that get_elimination_config_dict only contains primitive types, not objects."""
    svc = StrategyService()
    cfg = svc.get_elimination_config_dict()
    
    for key, val in cfg.items():
        assert isinstance(val, (int, float, bool, type(None))), f"{key} has non-primitive type {type(val)}"


def test_new_strategy_service_default_config_unchanged_after_other_instance_update():
    """Verify that updating one StrategyService instance does not mutate the class default."""
    svc1 = StrategyService()
    svc1.update_elimination_config({"min_trade_count": 999})
    
    svc2 = StrategyService()
    cfg2 = svc2.get_elimination_config_dict()
    
    assert cfg2["min_trade_count"] == 5  # The default remains 5
