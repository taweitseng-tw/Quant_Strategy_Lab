"""Tests for StrategyRepository — Task 032A."""

from __future__ import annotations

from dataclasses import asdict

import pytest

from core.models.strategy import Condition, Strategy, StrategyBlock
from repository.db import DatabaseManager
from repository.strategy_repo import StrategyRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sma_strategy(name: str = "sma_test", period: int = 20) -> Strategy:
    return Strategy(
        name=name,
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": period}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": period}, operator="<"),
        ], logic="AND"),
    )


def _mixed_strategy() -> Strategy:
    return Strategy(
        name="mixed",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="RSI", params={"period": 14}, operator="<", right=30.0),
        ], logic="AND"),
        short_entry=StrategyBlock(conditions=[
            Condition(indicator="MACD", params={"fast": 12, "slow": 26, "signal": 9}, operator=">"),
        ], logic="AND"),
        short_exit=StrategyBlock(conditions=[
            Condition(indicator="ATR", params={"period": 14}, operator="<", right=2.5),
        ], logic="AND"),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db():
    manager = DatabaseManager(":memory:")
    manager.initialize()
    yield manager
    manager.close()


# ---------------------------------------------------------------------------
# Insert + retrieve
# ---------------------------------------------------------------------------


def test_insert_and_get_by_name(db):
    sr = StrategyRepository(db)
    strat = _sma_strategy("simple_sma")
    row_id = sr.insert(strat)
    assert row_id is not None
    assert row_id > 0

    loaded = sr.get_by_name("simple_sma")
    assert loaded is not None
    assert loaded.name == "simple_sma"
    assert loaded.long_entry.conditions[0].indicator == "SMA"
    assert loaded.long_entry.conditions[0].params["period"] == 20
    assert loaded.long_entry.conditions[0].operator == ">"


def test_insert_full_strategy_round_trips(db):
    """A strategy with all four blocks and mixed indicators must survive
    a full save → load cycle."""
    sr = StrategyRepository(db)
    original = _mixed_strategy()
    sr.insert(original)

    loaded = sr.get_by_name("mixed")
    assert loaded is not None
    assert asdict(loaded) == asdict(original)


def test_get_by_name_nonexistent(db):
    sr = StrategyRepository(db)
    assert sr.get_by_name("no_such_strategy") is None


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_all_returns_newest_first(db):
    sr = StrategyRepository(db)
    sr.insert(_sma_strategy("first"))
    sr.insert(_sma_strategy("second", period=30))

    all_strats = sr.list_all()
    assert len(all_strats) == 2
    assert all_strats[0].name == "second"  # newest first


def test_list_all_empty(db):
    sr = StrategyRepository(db)
    assert sr.list_all() == []


# ---------------------------------------------------------------------------
# Update / save
# ---------------------------------------------------------------------------


def test_update_existing(db):
    sr = StrategyRepository(db)
    sr.insert(_sma_strategy("updatable", period=10))

    modified = _sma_strategy("updatable", period=99)
    updated = sr.update(modified)
    assert updated is True

    loaded = sr.get_by_name("updatable")
    assert loaded.long_entry.conditions[0].params["period"] == 99


def test_update_nonexistent(db):
    sr = StrategyRepository(db)
    assert sr.update(_sma_strategy("ghost")) is False


def test_save_inserts_new(db):
    sr = StrategyRepository(db)
    row_id = sr.save(_sma_strategy("fresh"))
    assert row_id > 0
    assert sr.get_by_name("fresh") is not None


def test_save_updates_existing(db):
    sr = StrategyRepository(db)
    sr.insert(_sma_strategy("dual", period=5))
    row_id = sr.save(_sma_strategy("dual", period=88))
    assert row_id == 0  # update, not insert
    loaded = sr.get_by_name("dual")
    assert loaded.long_entry.conditions[0].params["period"] == 88


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_strategy_success(db):
    sr = StrategyRepository(db)
    sr.insert(_sma_strategy("deletable"))
    assert sr.delete("deletable") is True
    assert sr.get_by_name("deletable") is None


def test_delete_strategy_not_found(db):
    sr = StrategyRepository(db)
    assert sr.delete("Missing") is False


# ---------------------------------------------------------------------------
# Task 053B-Fix: RiskManagement persistence
# ---------------------------------------------------------------------------

def test_round_trip_risk_management_ticks(db):
    sr = StrategyRepository(db)
    from core.models.strategy import RiskManagement
    strat = _sma_strategy("ticks_test")
    strat.risk_management = RiskManagement(stop_loss_ticks=15.0, take_profit_ticks=20.0)
    sr.insert(strat)
    loaded = sr.get_by_name(strat.name)
    assert loaded is not None
    assert loaded.risk_management is not None
    assert loaded.risk_management.stop_loss_ticks == 15.0
    assert loaded.risk_management.take_profit_ticks == 20.0
    assert loaded.risk_management.stop_loss_pct is None

def test_round_trip_risk_management_percent(db):
    sr = StrategyRepository(db)
    from core.models.strategy import RiskManagement
    strat = _sma_strategy("pct_test")
    strat.risk_management = RiskManagement(stop_loss_pct=0.02, take_profit_pct=0.05)
    sr.insert(strat)
    loaded = sr.get_by_name(strat.name)
    assert loaded is not None
    assert loaded.risk_management is not None
    assert loaded.risk_management.stop_loss_pct == 0.02
    assert loaded.risk_management.take_profit_pct == 0.05
    assert loaded.risk_management.stop_loss_ticks is None

def test_load_old_json_without_risk_management_fails_safe(db):
    sr = StrategyRepository(db)
    # Manually insert old JSON format without risk_management
    now = "2024-01-01T00:00:00"
    old_json = '{"name": "Old Strat", "long_entry": {"conditions": [], "logic": "AND"}, "long_exit": {"conditions": [], "logic": "AND"}, "short_entry": {"conditions": [], "logic": "AND"}, "short_exit": {"conditions": [], "logic": "AND"}}'
    sr._db.connection.execute(
        "INSERT INTO strategies (name, strategy_json, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("Old Strat", old_json, now, now)
    )
    sr._db.connection.commit()
    
    loaded = sr.get_by_name("Old Strat")
    assert loaded is not None
    assert loaded.name == "Old Strat"
    assert loaded.risk_management is not None
    assert loaded.risk_management.stop_loss_ticks is None
    assert loaded.risk_management.take_profit_pct is None


def test_load_malformed_risk_management_fails_safe(db):
    sr = StrategyRepository(db)
    now = "2024-01-01T00:00:00"
    
    # Test with string values, negative values, and booleans
    bad_json = '{"name": "Bad Strat", "risk_management": {"stop_loss_ticks": "twenty", "take_profit_ticks": -5.0, "stop_loss_pct": true}}'
    sr._db.connection.execute(
        "INSERT INTO strategies (name, strategy_json, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("Bad Strat", bad_json, now, now)
    )
    sr._db.connection.commit()
    
    loaded = sr.get_by_name("Bad Strat")
    assert loaded is not None
    assert loaded.name == "Bad Strat"
    assert loaded.risk_management is not None
    assert loaded.risk_management.stop_loss_ticks is None
    assert loaded.risk_management.take_profit_ticks is None
    assert loaded.risk_management.stop_loss_pct is None
    assert loaded.risk_management.take_profit_pct is None
# ---------------------------------------------------------------------------
# Schema: table exists after init
# ---------------------------------------------------------------------------


def test_strategies_table_exists_after_init(db):
    row = db.connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='strategies'"
    ).fetchone()
    assert row is not None


def test_strategy_repo_uses_in_memory_database(db):
    """The strategy repository tests run against an in-memory SQLite database."""
    assert db.db_path == ":memory:"
