"""Tests for JSON export UI wiring on the Results page (Task 039A)."""

import pytest
import os
import json
from unittest.mock import patch
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
    """Ensure clean UI state between tests."""
    main_window.results_table.table.clearSelection()

def test_json_export_button_exists_and_starts_disabled(main_window):
    win = main_window
    assert hasattr(win, "btn_export_json")
    assert win.btn_export_json.text() == "Export JSON"
    
    win.results_table.table.clearSelection()
    assert not win.btn_export_json.isEnabled()

def test_json_export_button_enabled_on_selection(main_window):
    win = main_window
    assert len(win.ranked_data) > 0
    win.results_table.table.selectRow(0)
    assert win.btn_export_json.isEnabled()

@patch("PySide6.QtWidgets.QFileDialog.getSaveFileName")
@patch("PySide6.QtWidgets.QMessageBox.information")
def test_json_export_success_flow(mock_info, mock_save, main_window, tmp_path):
    win = main_window
    win.results_table.table.selectRow(0)
    
    # Mock save dialog to return a valid path
    test_file = str(tmp_path / "test_strategy.json")
    mock_save.return_value = (test_file, "JSON Files (*.json)")
    
    win._handle_export_json()
    
    # Verify file was written
    assert os.path.exists(test_file)
    with open(test_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    strat = win.ranked_data[0]["strategy"]
    assert data["name"] == strat.name
    assert "long_entry" in data
    assert "metrics" not in data
    assert "trades" not in data
    assert "equity_curve" not in data
    assert "drawdown_curve" not in data
    assert data.get("provenance") == win.ranked_data[0].get("provenance")
    
    # Verify success message
    mock_info.assert_called_once()
    assert "successfully exported" in mock_info.call_args[0][2]

@patch("PySide6.QtWidgets.QFileDialog.getSaveFileName")
def test_json_export_cancel_flow(mock_save, main_window):
    win = main_window
    win.results_table.table.selectRow(0)
    
    # Mock user cancelling dialog
    mock_save.return_value = ("", "")
    
    # Should not crash, and should not write anything
    win._handle_export_json()

@patch("PySide6.QtWidgets.QMessageBox.warning")
def test_json_export_no_selection_warning(mock_warning, main_window):
    win = main_window
    win.results_table.table.clearSelection()
    
    win._handle_export_json()
    mock_warning.assert_called_once()
    assert "select a strategy" in mock_warning.call_args[0][2]


@patch("PySide6.QtWidgets.QFileDialog.getSaveFileName")
@patch("PySide6.QtWidgets.QMessageBox.information")
def test_json_export_forces_json_extension(mock_info, mock_save, main_window, tmp_path):
    win = main_window
    win.results_table.table.selectRow(0)

    test_file = str(tmp_path / "strategy_without_extension")
    mock_save.return_value = (test_file, "JSON Files (*.json)")

    win._handle_export_json()

    assert os.path.exists(test_file + ".json")


def test_json_export_preserves_condition_timeframe(main_window, tmp_path):
    from core.models.strategy import Condition
    with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName") as mock_save, \
         patch("PySide6.QtWidgets.QMessageBox.information"):
         
        win = main_window
        # Modify the first strategy to have an MTF condition, but restore it after
        strat = win.ranked_data[0]["strategy"]
        original_conditions = list(strat.long_entry.conditions)
        strat.long_entry.conditions.append(Condition(indicator="SMA", params={"period": 20, "timeframe": 15}, operator=">"))
        
        try:
            win.results_table.table.selectRow(0)

            test_file = str(tmp_path / "test_mtf_export.json")
            mock_save.return_value = (test_file, "JSON Files (*.json)")

            win._handle_export_json()

            assert os.path.exists(test_file)
            with open(test_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            conds = data["long_entry"]["conditions"]
            assert any(c.get("params", {}).get("timeframe") == 15 for c in conds)
        finally:
            strat.long_entry.conditions = original_conditions
