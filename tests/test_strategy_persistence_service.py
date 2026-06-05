"""Tests for StrategyPersistenceService — Task 032B."""

from __future__ import annotations

from dataclasses import asdict

import pytest

from core.models.strategy import Condition, Strategy, StrategyBlock
from repository.db import DatabaseManager
from app.services.strategy_persistence_service import (
    GA_BEST_PREFIX,
    StrategyPersistenceService,
)


# ---------------------------------------------------------------------------
def _ga_strategy(name: str = "ga_g003_0004", period: int = 25) -> Strategy:
    """A realistic GA-generated strategy with a GA-style name."""
    return Strategy(
        name=name,
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": period}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="RSI", params={"period": 14}, operator="<", right=30.0),
        ], logic="AND"),
        short_entry=StrategyBlock(conditions=[
            Condition(indicator="MACD", params={"fast": 8, "slow": 21, "signal": 5}, operator=">"),
        ], logic="AND"),
        short_exit=StrategyBlock(conditions=[
            Condition(indicator="ATR", params={"period": 10}, operator="<", right=1.8),
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


@pytest.fixture
def svc(db):
    yield StrategyPersistenceService(db)


def test_fixture_uses_in_memory_database(db):
    assert db.db_path == ":memory:"


# ---------------------------------------------------------------------------
# Save + load
# ---------------------------------------------------------------------------


def test_save_and_load_round_trips(svc):
    original = _ga_strategy("ga_g002_0001", period=33)
    label = svc.save_best_strategy(original, label="latest")

    assert label == f"{GA_BEST_PREFIX}latest"

    loaded = svc.load_best_strategy(label="latest")
    assert loaded is not None

    # The stored name is the canonical label (ga_best_latest), not the
    # original GA name (ga_g002_0001).  Verify structural equality.
    assert loaded.name == f"{GA_BEST_PREFIX}latest"
    orig_dict = asdict(original)
    loaded_dict = asdict(loaded)
    # Compare everything except the name.
    assert loaded_dict["long_entry"] == orig_dict["long_entry"]
    assert loaded_dict["long_exit"] == orig_dict["long_exit"]
    assert loaded_dict["short_entry"] == orig_dict["short_entry"]
    assert loaded_dict["short_exit"] == orig_dict["short_exit"]


def test_save_does_not_mutate_original_name(svc):
    original = _ga_strategy("ga_g001_0099", period=17)
    original_name_before = original.name

    svc.save_best_strategy(original, label="test")

    # The original strategy's name must be unchanged after save.
    assert original.name == original_name_before


def test_load_nonexistent_label_returns_none(svc):
    assert svc.load_best_strategy(label="never_saved") is None


def test_save_overwrites_existing_label(svc):
    first = _ga_strategy(period=10)
    second = _ga_strategy(period=99)

    svc.save_best_strategy(first, label="duplicate")
    svc.save_best_strategy(second, label="duplicate")

    loaded = svc.load_best_strategy(label="duplicate")
    assert loaded is not None
    # The second save should overwrite — period=99, not 10.
    assert loaded.long_entry.conditions[0].params["period"] == 99


def test_custom_prefix(svc):
    strat = _ga_strategy()
    svc.save_best_strategy(strat, label="run1", prefix="my_prefix_")

    loaded = svc.load_best_strategy(label="run1", prefix="my_prefix_")
    assert loaded is not None
    assert loaded.long_entry.conditions[0].indicator == "SMA"

    # Default prefix lookup should not find it.
    assert svc.load_best_strategy(label="run1") is None


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_saved_strategies(svc):
    svc.save_best_strategy(_ga_strategy(), label="gen1")
    svc.save_best_strategy(_ga_strategy(), label="gen5")

    results = svc.list_saved_strategies()
    assert len(results) == 2
    names = {s.name for s in results}
    assert f"{GA_BEST_PREFIX}gen1" in names
    assert f"{GA_BEST_PREFIX}gen5" in names


def test_list_filters_by_prefix(svc):
    from core.models.strategy import Strategy as S, StrategyBlock as SB
    svc.save_best_strategy(_ga_strategy(), label="a")

    # Insert a non-GA strategy directly into the repo.
    repo = svc._repo
    repo.insert(S(name="manual_strategy",
                  long_entry=SB(conditions=[
                      Condition(indicator="SMA", params={"period": 5}, operator=">")
                  ])))

    ga_list = svc.list_saved_strategies(prefix=GA_BEST_PREFIX)
    assert len(ga_list) == 1
    assert ga_list[0].name == f"{GA_BEST_PREFIX}a"


def test_list_empty(svc):
    assert svc.list_saved_strategies() == []


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_removes_label(svc):
    svc.save_best_strategy(_ga_strategy(), label="remove_me")
    assert svc.load_best_strategy(label="remove_me") is not None

    svc.delete_best_strategy(label="remove_me")
    assert svc.load_best_strategy(label="remove_me") is None


def test_delete_nonexistent_returns_false(svc):
    assert svc.delete_best_strategy(label="no_such") is False
