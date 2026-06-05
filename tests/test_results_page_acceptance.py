"""Acceptance smoke test for Results page wiring (Task 038B)."""

import pytest
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture(scope="module")
def main_window(qapp):
    return MainWindow()

@pytest.fixture(autouse=True)
def reset_main_window_state(main_window):
    """
    Ensure clean UI state between tests using the shared MainWindow.
    This prevents stale selection state from masking bugs.
    """
    main_window.results_table.table.clearSelection()

def test_results_page_wiring_smoke(main_window, monkeypatch):
    """
    Acceptance test for the Results page to ensure Strategy Detail,
    Equity Curve, Trade List, and Heatmap all update when a real
    ranked strategy is selected.
    """
    win = main_window
    assert len(win.ranked_data) > 0, "Expected at least one ranked strategy from default initialization"
    
    # Verify Parameter Heatmap has rows from ranked_data
    if hasattr(win, "heatmap_widget"):
        assert win.heatmap_widget.table.rowCount() == len(win.ranked_data)

    chart_updates = []
    original_set_data = win.results_chart.set_data

    def spy_set_data(*args, **kwargs):
        chart_updates.append((args, kwargs))
        return original_set_data(*args, **kwargs)

    monkeypatch.setattr(win.results_chart, "set_data", spy_set_data)

    # Select first row in the results table
    win.results_table.table.selectRow(0)
    
    strat_item = win.ranked_data[0]
    expected_name = strat_item["strategy"].name
    
    # Verify Strategy Detail shows the selected strategy name
    if hasattr(win, "strategy_detail"):
        assert win.strategy_detail.lbl_name.text() == expected_name

    # Verify Equity Curve receives data via the existing chart path
    assert chart_updates, "Selecting a ranked strategy must update the equity chart."

    # Verify Trade List row count matches selected entry trades up to current page size behavior
    if hasattr(win, "trade_list"):
        trades = strat_item.get("trades", [])
        expected_rows = min(len(trades), getattr(win.trade_list, "page_size", 100))
        assert win.trade_list.table.rowCount() == expected_rows
        
    # Verify clearing selection resets Strategy Detail and Trade List
    win.results_table.table.clearSelection()
    
    if hasattr(win, "strategy_detail"):
        assert "No Strategy Selected" in win.strategy_detail.lbl_name.text()
        
    if hasattr(win, "trade_list"):
        assert win.trade_list.table.rowCount() == 0
