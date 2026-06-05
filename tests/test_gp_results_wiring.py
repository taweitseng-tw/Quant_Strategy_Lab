"""Tests for GP Results page integration — Task 031G.

Verifies that:
- StrategyService accepts GP injected_strategies and appends them with GP provenance.
- MainWindow _on_gp_success stores the latest GP strategy with a [GP Best] prefix.
- MainWindow _refresh_results_ranking injects the GP strategy into the Results ranking table.
- GP strategies can coexist with GA and imported strategies.
"""

from __future__ import annotations

import os
import sys
import pandas as pd
import pytest

from core.models.strategy import Strategy, StrategyBlock, Condition

# Skip entire module if display is unavailable (headless CI).
pytestmark = pytest.mark.skipif(
    sys.platform != "win32" and not os.environ.get("DISPLAY"),
    reason="Requires display or Windows",
)

# ---------------------------------------------------------------------------
# Service level tests
# ---------------------------------------------------------------------------

def test_strategy_service_injects_gp_strategy():
    """StrategyService must append GP injected strategies with GP provenance."""
    from app.services.strategy_service import StrategyService
    
    svc = StrategyService()
    df = svc.generate_deterministic_mock_ohlcv(count=100)
    
    gp_strat = Strategy(
        name="[GP Best] test_strat",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator=">")
        ])
    )
    
    ranked, is_mock = svc.get_ranked_strategies(dataset_df=df, injected_strategies=[gp_strat])
    
    assert len(ranked) == 11
    
    found = False
    for item in ranked:
        if item["strategy"].name == "[GP Best] test_strat":
            found = True
            assert item["provenance"].get("generator") == "gp_search"
            assert item["provenance"].get("source_type") == "gp_evolved"
            assert item["provenance"].get("injected_strategy") is True
            break
            
    assert found is True

# ---------------------------------------------------------------------------
# UI integration tests
# ---------------------------------------------------------------------------

def test_gp_best_strategy_appears_in_results_ranking():
    """MainWindow must store GP result and display it on the Results page."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.ui.main_window import MainWindow
    from app.services.gp_service import GPSearchResult

    window = MainWindow()
    
    gp_strat = Strategy(
        name="my_gp_strat",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 15}, operator=">"),
        ])
    )
    
    result = GPSearchResult(
        best_strategy=gp_strat,
        best_score=0.9999,
        generation_count=5,
        final_population_size=10,
        generation_best_scores=[],
        generation_avg_scores=[],
        config_snapshot={},
    )
    
    window._on_gp_success(result, source_label="Test Source")
    
    assert hasattr(window, "_latest_gp_strategy")
    assert window._latest_gp_strategy.name == "[GP Best] my_gp_strat"
    
    text = window.gp_results_summary_label.text()
    assert "[GP Best] my_gp_strat" in text
    assert "0.9999" in text
    assert "Test Source" in text
    
    found = False
    for i in range(window.results_table.table.rowCount()):
        item = window.results_table.table.item(i, 1)
        if "[GP Best] my_gp_strat" in item.text():
            found = True
            break
            
    assert found is True

def test_gp_best_strategy_has_visible_prefix():
    from app.services.gp_service import GPSearchResult
    from core.models.strategy import Strategy
    from app.ui.main_window import MainWindow
    window = MainWindow()
    
    res = GPSearchResult(
        best_strategy=Strategy(name="raw_gp_name"),
        best_score=1.0,
        generation_count=1,
        final_population_size=1,
        generation_best_scores=[],
        generation_avg_scores=[],
        config_snapshot={},
    )
    
    window._on_gp_success(res, "x")
    assert window._latest_gp_strategy.name == "[GP Best] raw_gp_name"
    assert res.best_strategy.name == "raw_gp_name"  # Original not mutated

def test_ga_and_gp_best_strategies_coexist_in_results():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.ui.main_window import MainWindow
    from app.services.ga_service import GASearchResult
    from app.services.gp_service import GPSearchResult
    
    window = MainWindow()
    
    ga_res = GASearchResult(
        best_strategy=Strategy(name="ga"), best_score=1.0, generation_count=1, final_population_size=1
    )
    window._on_ga_success(ga_res, "src")
    
    gp_res = GPSearchResult(
        best_strategy=Strategy(name="gp"), best_score=1.0, generation_count=1, final_population_size=1,
        generation_best_scores=[], generation_avg_scores=[], config_snapshot={},
    )
    window._on_gp_success(gp_res, "src")
    
    ga_found = False
    gp_found = False
    for i in range(window.results_table.table.rowCount()):
        txt = window.results_table.table.item(i, 1).text()
        if "[GA Best]" in txt: ga_found = True
        if "[GP Best]" in txt: gp_found = True
        
    assert ga_found is True
    assert gp_found is True

def test_gp_and_imported_strategies_coexist_in_results():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.ui.main_window import MainWindow
    from app.services.gp_service import GPSearchResult
    
    window = MainWindow()
    window._imported_strategies = [Strategy(name="[Imported] json_strat")]
    
    gp_res = GPSearchResult(
        best_strategy=Strategy(name="gp"), best_score=1.0, generation_count=1, final_population_size=1,
        generation_best_scores=[], generation_avg_scores=[], config_snapshot={},
    )
    window._on_gp_success(gp_res, "src")
    
    json_found = False
    gp_found = False
    for i in range(window.results_table.table.rowCount()):
        txt = window.results_table.table.item(i, 1).text()
        if "[Imported]" in txt: json_found = True
        if "[GP Best]" in txt: gp_found = True
        
    assert json_found is True
    assert gp_found is True

def test_refresh_results_includes_all_injected_strategy_types():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from app.ui.main_window import MainWindow
    
    window = MainWindow()
    window._latest_ga_strategy = Strategy(name="[GA Best] X")
    window._latest_gp_strategy = Strategy(name="[GP Best] Y")
    window._imported_strategies = [Strategy(name="[Imported] Z")]
    
    window._refresh_results_ranking()
    
    found_ga = found_gp = found_imp = False
    for i in range(window.results_table.table.rowCount()):
        txt = window.results_table.table.item(i, 1).text()
        if "[GA Best] X" in txt: found_ga = True
        if "[GP Best] Y" in txt: found_gp = True
        if "[Imported] Z" in txt: found_imp = True
        
    assert found_ga and found_gp and found_imp

def test_selecting_gp_strategy_updates_results_widgets():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.ui.main_window import MainWindow
    from app.services.gp_service import GPSearchResult
    
    window = MainWindow()
    
    gp_res = GPSearchResult(
        best_strategy=Strategy(name="gp_select_test"), best_score=1.0, generation_count=1, final_population_size=1,
        generation_best_scores=[], generation_avg_scores=[], config_snapshot={},
    )
    window._on_gp_success(gp_res, "src")
    
    # Find row of GP strat
    gp_row = -1
    for i in range(window.results_table.table.rowCount()):
        if "[GP Best]" in window.results_table.table.item(i, 1).text():
            gp_row = i
            break
            
    assert gp_row != -1
    
    # Select it
    window.results_table.table.selectRow(gp_row)
    window._handle_strategy_selection_changed()
    
    # Detail should update
    assert window.strategy_detail.lbl_name.text() == "[GP Best] gp_select_test"

def test_gp_results_integration_does_not_persist_strategy(monkeypatch):
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from app.ui.main_window import MainWindow
    from app.services.gp_service import GPSearchResult
    
    window = MainWindow()
    
    saved_flag = []
    
    def mock_save(*args, **kwargs):
        saved_flag.append(True)
        
    monkeypatch.setattr("app.services.strategy_persistence_service.StrategyPersistenceService.save_best_strategy", mock_save, raising=False)
    
    gp_res = GPSearchResult(
        best_strategy=Strategy(name="gp"), best_score=1.0, generation_count=1, final_population_size=1,
        generation_best_scores=[], generation_avg_scores=[], config_snapshot={},
    )
    window._on_gp_success(gp_res, "src")
    
    assert len(saved_flag) == 0

def test_gp_results_integration_does_not_modify_ga_state():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from app.ui.main_window import MainWindow
    from app.services.gp_service import GPSearchResult
    
    window = MainWindow()
    
    window._latest_ga_strategy = Strategy(name="my_ga_strat")
    
    gp_res = GPSearchResult(
        best_strategy=Strategy(name="gp"), best_score=1.0, generation_count=1, final_population_size=1,
        generation_best_scores=[], generation_avg_scores=[], config_snapshot={},
    )
    window._on_gp_success(gp_res, "src")
    
    assert window._latest_ga_strategy.name == "my_ga_strat"


# ---------------------------------------------------------------------------
# Hardening tests (031G-Codex)
# ---------------------------------------------------------------------------

def test_gp_best_strategy_has_visible_prefix_and_provenance():
    """GP strategy must carry [GP Best] prefix and gp_search provenance in StrategyService."""
    from app.services.strategy_service import StrategyService

    svc = StrategyService()
    df = svc.generate_deterministic_mock_ohlcv(count=100)

    gp_strat = Strategy(
        name="[GP Best] prov_check",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator=">")
        ])
    )
    ranked, _ = svc.get_ranked_strategies(dataset_df=df, injected_strategies=[gp_strat])

    entry = next(e for e in ranked if e["strategy"].name == "[GP Best] prov_check")
    assert entry["provenance"]["generator"] == "gp_search"
    assert entry["provenance"]["source_type"] == "gp_evolved"
    assert entry["provenance"]["injected_strategy"] is True
    assert entry["provenance"]["strategy_name"] == "[GP Best] prov_check"


def test_gp_strategy_selection_updates_equity_curve_and_trade_list():
    """Selecting a GP strategy must update equity curve chart and trade list widget."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.ui.main_window import MainWindow
    from app.services.gp_service import GPSearchResult

    window = MainWindow()
    gp_res = GPSearchResult(
        best_strategy=Strategy(
            name="gp_chart_test",
            long_entry=StrategyBlock(conditions=[
                Condition(indicator="SMA", params={"period": 10}, operator=">")
            ]),
            long_exit=StrategyBlock(conditions=[
                Condition(indicator="SMA", params={"period": 10}, operator="<")
            ]),
        ),
        best_score=1.0,
        generation_count=1,
        final_population_size=1,
        generation_best_scores=[],
        generation_avg_scores=[],
        config_snapshot={},
    )
    window._on_gp_success(gp_res, "src")

    gp_row = -1
    for i in range(window.results_table.table.rowCount()):
        if "[GP Best]" in window.results_table.table.item(i, 1).text():
            gp_row = i
            break
    assert gp_row != -1

    window.results_table.table.selectRow(gp_row)
    window._handle_strategy_selection_changed()

    # Detail updated
    assert window.strategy_detail.lbl_name.text() == "[GP Best] gp_chart_test"

    # Equity curve should have received data (the GP strategy ran a backtest)
    gp_entry = window.ranked_data[gp_row]
    assert gp_entry.get("equity_curve") is not None

    # Trade list row count matches the backtest trades
    expected_trades = gp_entry.get("trades", [])
    assert window.trade_list.table.rowCount() == len(expected_trades)


def test_ga_gp_imported_strategies_all_coexist_with_correct_count():
    """When GA, GP, and Imported are all present, row count = 10 base + 3 injected."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from app.ui.main_window import MainWindow

    window = MainWindow()
    window._latest_ga_strategy = Strategy(name="[GA Best] A")
    window._latest_gp_strategy = Strategy(name="[GP Best] B")
    window._imported_strategies = [Strategy(name="[Imported] C")]

    window._refresh_results_ranking()

    assert len(window.ranked_data) == 13  # 10 base + 3 injected
    assert window.results_table.table.rowCount() == 13


def test_ga_results_integration_does_not_modify_gp_state():
    """Running GA success must not alter _latest_gp_strategy."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from app.ui.main_window import MainWindow
    from app.services.ga_service import GASearchResult

    window = MainWindow()
    window._latest_gp_strategy = Strategy(name="[GP Best] frozen")

    ga_res = GASearchResult(
        best_strategy=Strategy(name="ga_new"), best_score=1.0,
        generation_count=1, final_population_size=1,
    )
    window._on_ga_success(ga_res, "src")

    assert window._latest_gp_strategy.name == "[GP Best] frozen"


def test_project_reset_clears_gp_and_imported_state():
    """Simulating project-new reset must clear _latest_gp_strategy and _imported_strategies.

    This is a regression test for a bug where _imported_strategies leaked across projects.
    """
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from app.ui.main_window import MainWindow

    window = MainWindow()

    # Simulate that strategies were previously loaded
    window._latest_ga_strategy = Strategy(name="[GA Best] old")
    window._latest_gp_strategy = Strategy(name="[GP Best] old")
    window._imported_strategies = [Strategy(name="[Imported] old")]

    # Simulate the reset that _handle_new_project performs (without dialogs)
    window._latest_ga_strategy = None
    window._latest_gp_strategy = None
    window._imported_strategies = []

    window._refresh_results_ranking()

    # After reset, only the 10 base strategies should be present
    assert len(window.ranked_data) == 10

    # No injected strategies should remain
    for entry in window.ranked_data:
        name = entry["strategy"].name
        assert "[GA Best]" not in name
        assert "[GP Best]" not in name
        assert "[Imported]" not in name


def test_gp_strategy_detail_shows_provenance():
    """Selecting a GP strategy must show gp_search provenance in StrategyDetailWidget."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from app.ui.main_window import MainWindow
    from app.services.gp_service import GPSearchResult

    window = MainWindow()
    gp_res = GPSearchResult(
        best_strategy=Strategy(name="gp_prov_test"),
        best_score=1.0,
        generation_count=1,
        final_population_size=1,
        generation_best_scores=[],
        generation_avg_scores=[],
        config_snapshot={},
    )
    window._on_gp_success(gp_res, "src")

    gp_row = -1
    for i in range(window.results_table.table.rowCount()):
        if "[GP Best]" in window.results_table.table.item(i, 1).text():
            gp_row = i
            break
    assert gp_row != -1

    window.results_table.table.selectRow(gp_row)
    window._handle_strategy_selection_changed()

    prov_text = window.strategy_detail.lbl_provenance.text()
    assert "gp_search" in prov_text
    assert "gp_evolved" in prov_text
