"""Tests for StrategyService and RankingTable widget — Task 006B."""

from __future__ import annotations

import sys
import pandas as pd
import pytest
from PySide6.QtWidgets import QApplication

from app.services.strategy_service import StrategyService
from app.widgets.ranking_table import RankingTable


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Fixture to initialize a QApplication instance for GUI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_strategy_service_ranked_strategies() -> None:
    """Verify StrategyService correctly generates, backtests, and ranks 10 strategies."""
    service = StrategyService()
    ranked, is_mock = service.get_ranked_strategies()
    
    assert len(ranked) == 10
    assert is_mock is True
    
    # Check that entries are sorted by fitness descending and ranks are correct
    prev_fitness = 999.0
    for idx, item in enumerate(ranked):
        assert item["rank"] == idx + 1
        assert "strategy" in item
        assert "provenance" in item
        assert "metrics" in item
        assert "fitness" in item
        
        fitness = item["fitness"]
        assert fitness <= prev_fitness
        prev_fitness = fitness
        
        # Check canonical metrics are calculated
        metrics = item["metrics"]
        assert "total_pnl" in metrics
        assert "profit_factor" in metrics
        assert "max_drawdown_pnl" in metrics
        assert "win_rate" in metrics
        assert "total_trades" in metrics


def test_ranking_table_widget_population(qapp) -> None:
    """Verify that RankingTable displays the ranked strategy rows correctly."""
    service = StrategyService()
    ranked, is_mock = service.get_ranked_strategies()
    
    table_widget = RankingTable()
    assert table_widget.table.rowCount() == 0
    
    table_widget.set_ranking_data(ranked, is_mock=is_mock)
    
    # Check count matches
    assert table_widget.table.rowCount() == 10
    
    # Check status label
    assert "Sample / Mock" in table_widget.status_label.text()


def test_mock_ohlcv_generation_non_mutation_and_determinism() -> None:
    """Verify that mock OHLCV generation is deterministic and does not mutate NumPy global random state."""
    import numpy as np

    # Reset numpy global seed to a fixed state
    np.random.seed(99)
    state_before = np.random.get_state()
    
    # Generate mock OHLCV
    service = StrategyService()
    df1 = service.generate_deterministic_mock_ohlcv(seed=42, count=20)
    
    # Verify global random state has NOT been altered
    state_after = np.random.get_state()
    assert state_before[0] == state_after[0]
    assert np.array_equal(state_before[1], state_after[1])
    assert state_before[2] == state_after[2]
    assert state_before[3] == state_after[3]
    assert state_before[4] == state_after[4]
    
    # Generate another with same seed and verify it is completely identical (determinism)
    df2 = service.generate_deterministic_mock_ohlcv(seed=42, count=20)
    pd.testing.assert_frame_equal(df1, df2)

    # Generate one with different seed and verify it differs
    df3 = service.generate_deterministic_mock_ohlcv(seed=100, count=20)
    assert not df1.equals(df3)


# ---------------------------------------------------------------------------
# Elimination integration — Task 019B
# ---------------------------------------------------------------------------


def test_elimination_fields_present_on_results():
    """Every ranked result must have elimination_passed, elimination_failed_rules,
    and elimination_status fields."""
    service = StrategyService()
    ranked, _ = service.get_ranked_strategies()

    for entry in ranked:
        assert "elimination_passed" in entry
        assert "elimination_failed_rules" in entry
        assert "elimination_status" in entry
        assert entry["elimination_status"] in ("passed", "eliminated")
        assert isinstance(entry["elimination_passed"], bool)
        assert isinstance(entry["elimination_failed_rules"], list)


def test_elimination_ranking_remains_deterministic():
    """Elimination must not change ranking order — rankings are still by fitness."""
    service = StrategyService()
    ranked1, _ = service.get_ranked_strategies()
    ranked2, _ = service.get_ranked_strategies()

    for e1, e2 in zip(ranked1, ranked2):
        assert e1["rank"] == e2["rank"]
        assert e1["elimination_passed"] == e2["elimination_passed"]
        assert e1["elimination_failed_rules"] == e2["elimination_failed_rules"]


def test_elimination_does_not_mutate_metrics():
    """Original metrics dicts must not gain elimination keys."""
    service = StrategyService()
    ranked, _ = service.get_ranked_strategies()

    for entry in ranked:
        assert "elimination_passed" not in entry.get("metrics", {})
        assert "elimination_failed_rules" not in entry.get("metrics", {})


def test_elimination_with_lenient_config_passes_all():
    """An EliminationConfig with all-zero/negative thresholds must pass everything."""
    from validation_engine.elimination import EliminationConfig

    svc = StrategyService(elimination_config=EliminationConfig(
        min_trade_count=0,
        min_profit_factor=0.0,
        max_drawdown_pnl=1_000_000.0,
        min_avg_trade=-10_000.0,
    ))
    ranked, _ = svc.get_ranked_strategies()

    for entry in ranked:
        assert entry["elimination_passed"]
        assert entry["elimination_failed_rules"] == []
        assert entry["elimination_status"] == "passed"


def test_elimination_with_strict_config_eliminates_some():
    """A strict EliminationConfig must eliminate strategies with weak metrics."""
    from validation_engine.elimination import EliminationConfig

    svc = StrategyService(elimination_config=EliminationConfig(
        min_trade_count=50,
        min_profit_factor=2.0,
        max_drawdown_pnl=1_000.0,
        min_avg_trade=1_000.0,
    ))
    ranked, _ = svc.get_ranked_strategies()

    eliminated = [e for e in ranked if not e["elimination_passed"]]
    # With strict thresholds on mock data, at least some should be eliminated.
    assert len(eliminated) >= 1
    for e in eliminated:
        assert len(e["elimination_failed_rules"]) >= 1


def test_ranking_table_elimination_column_rendering(qapp) -> None:
    """Verify that RankingTable displays the elimination status column and tooltips correctly."""
    from validation_engine.elimination import EliminationConfig
    
    # 1. Test lenient (everything passes)
    svc_lenient = StrategyService(elimination_config=EliminationConfig(
        min_trade_count=0,
        min_profit_factor=0.0,
        max_drawdown_pnl=1_000_000.0,
        min_avg_trade=-10_000.0,
    ))
    ranked_lenient, is_mock = svc_lenient.get_ranked_strategies()
    
    table_widget = RankingTable()
    table_widget.set_ranking_data(ranked_lenient, is_mock=is_mock)
    
    assert table_widget.table.columnCount() == 9
    assert table_widget.table.horizontalHeaderItem(8).text() == "Elimination"
    
    # All rows should say "Passed"
    for r in range(10):
        item = table_widget.table.item(r, 8)
        assert item is not None
        assert item.text() == "Passed"
        assert item.toolTip() == "Passed all elimination rules"
        
    # 2. Test strict (some fail)
    svc_strict = StrategyService(elimination_config=EliminationConfig(
        min_trade_count=50,
        min_profit_factor=2.0,
        max_drawdown_pnl=1_000.0,
        min_avg_trade=1_000.0,
    ))
    ranked_strict, is_mock = svc_strict.get_ranked_strategies()
    
    table_widget_strict = RankingTable()
    table_widget_strict.set_ranking_data(ranked_strict, is_mock=is_mock)
    
    found_eliminated = False
    for r in range(10):
        item = table_widget_strict.table.item(r, 8)
        assert item is not None
        if item.text() == "Eliminated":
            found_eliminated = True
            assert "Failed rules:" in item.toolTip()
            
    assert found_eliminated

