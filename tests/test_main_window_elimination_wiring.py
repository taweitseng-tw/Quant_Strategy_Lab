"""Tests for wiring EliminationConfigWidget into MainWindow — Task 041D."""

import sys
import pytest
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Fixture to initialize a QApplication instance for GUI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def main_window(qapp):
    """Fixture providing a MainWindow instance."""
    window = MainWindow()
    return window


def test_main_window_has_elimination_config_widget(main_window):
    """Verify MainWindow has instantiated and attached the EliminationConfigWidget."""
    assert hasattr(main_window, "elimination_config_widget")
    assert main_window.elimination_config_widget is not None


def test_main_window_has_no_validation_engine_import():
    """Verify MainWindow does not directly import validation_engine."""
    import app.ui.main_window as mw
    
    with open(mw.__file__, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "import validation_engine" not in content
    assert "from validation_engine" not in content


def test_elimination_widget_initializes_from_strategy_service(main_window):
    """Verify widget initializes with default configuration from StrategyService."""
    default_cfg = main_window.strategy_service.get_elimination_config_dict()
    
    widget_cfg = main_window.elimination_config_widget.get_config_dict()
    
    # Check a few core properties match
    assert widget_cfg["min_trade_count"] == default_cfg["min_trade_count"]
    assert widget_cfg["max_drawdown_pnl"] == default_cfg["max_drawdown_pnl"]


def test_elimination_config_change_calls_strategy_service_update(main_window):
    """Verify changing widget state updates the underlying StrategyService configuration."""
    widget = main_window.elimination_config_widget
    svc = main_window.strategy_service
    
    # Ensure starting condition
    assert svc.get_elimination_config_dict()["min_trade_count"] == 5
    
    # Simulate UI dictionary emission (which happens when fields are edited)
    widget.config_changed.emit({"min_trade_count": 999})
    
    # Check service updated
    assert svc.get_elimination_config_dict()["min_trade_count"] == 999


def test_strict_elimination_config_eliminates_ranked_strategies(main_window):
    """Verify that emitting a strict dict immediately filters ranking results."""
    # Start with lenient defaults
    main_window.elimination_config_widget.config_changed.emit({
        "min_trade_count": 0,
        "min_profit_factor": 0.0,
        "max_drawdown_pnl": 1000000.0,
        "min_avg_trade": -100000.0
    })
    
    lenient_passed = [s for s in main_window.ranked_data if s.get("elimination_passed")]
    
    # Emit strict dict
    main_window.elimination_config_widget.config_changed.emit({
        "min_trade_count": 1000000  # Impossible requirement
    })
    
    strict_passed = [s for s in main_window.ranked_data if s.get("elimination_passed")]
    
    assert len(lenient_passed) > len(strict_passed)
    assert len(strict_passed) == 0


def test_clear_all_elimination_config_disables_thresholds(main_window):
    """Verify that clearing the widget disables active thresholds and passes strategies."""
    # Emit strict dict
    main_window.elimination_config_widget.config_changed.emit({
        "min_trade_count": 1000000
    })
    
    assert not any(s.get("elimination_passed") for s in main_window.ranked_data)
    
    # Simulate clear all (which emits a dict of Nones)
    main_window.elimination_config_widget.clear_all()
    
    # Ensure they pass again
    assert all(s.get("elimination_passed") for s in main_window.ranked_data)


def test_results_selection_still_works_after_elimination_config_change(main_window):
    """Verify clicking an item in the ranking table still populates details, even after rule changes."""
    # Set a config that allows at least one to pass (for testing selection)
    main_window.elimination_config_widget.config_changed.emit({
        "min_trade_count": 0,
        "max_drawdown_pnl": 1000000.0
    })
    
    # Select the first row
    table = main_window.results_table.table
    table.selectRow(0)
    
    # Verify strategy detail widget gets populated
    assert main_window.strategy_detail.lbl_name.text() != "No Strategy Selected"
    
    # Verify export buttons became enabled
    assert main_window.btn_export_python.isEnabled()


def test_elimination_config_signal_refreshes_ranking_once(main_window, monkeypatch):
    """Verify that emitting config_changed calls _refresh_results_ranking exactly once."""
    call_count = 0
    original_refresh = main_window._refresh_results_ranking
    
    def mock_refresh():
        nonlocal call_count
        call_count += 1
        original_refresh()
        
    monkeypatch.setattr(main_window, "_refresh_results_ranking", mock_refresh)
    
    main_window.elimination_config_widget.config_changed.emit({
        "min_trade_count": 10
    })
    
    assert call_count == 1


def test_elimination_empty_ranking_clears_detail_trade_chart(main_window):
    """Verify that if the ranking table becomes empty, the UI state is safely cleared."""
    # Ensure there is a selection first
    main_window.elimination_config_widget.config_changed.emit({"min_trade_count": 0})
    main_window.results_table.table.selectRow(0)
    
    # Verify populated state
    assert main_window.strategy_detail.lbl_name.text() != "No Strategy Selected"
    
    # Simulate empty ranking
    main_window.ranked_data = []
    main_window.results_table.set_ranking_data([])
    
    # Selection should be gone and ranking empty
    assert len(main_window.results_table.table.selectedItems()) == 0
    assert main_window.results_table.table.rowCount() == 0
    
    # Explicitly call selection handler to simulate QT clearing selection
    main_window._handle_strategy_selection_changed()
    
    # Detail should be cleared
    assert main_window.strategy_detail.lbl_name.text() == "No Strategy Selected"
    
    # Chart should be cleared
    # In EquityCurveChart, clear() sets the title to 'No Strategy Selected'
    if getattr(main_window.results_chart, "equity_plot", None):
        assert "No Strategy Selected" in main_window.results_chart.equity_plot.plotItem.titleLabel.text
        
    # Trade list should be empty
    assert main_window.trade_list.table.rowCount() == 0


def test_frequent_elimination_changes_do_not_duplicate_rows_or_connections(main_window):
    """Verify rapid checkbox changes do not compound rows in the ranking table."""
    main_window.elimination_config_widget.config_changed.emit({"min_trade_count": 0})
    initial_rows = main_window.results_table.table.rowCount()
    
    for _ in range(5):
        main_window.elimination_config_widget.config_changed.emit({"min_trade_count": 0})
        
    final_rows = main_window.results_table.table.rowCount()
    
    assert initial_rows > 0
    assert initial_rows == final_rows

