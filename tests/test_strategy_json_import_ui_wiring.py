"""Tests for JSON import preview UI wiring on the Results page (Task 039C)."""

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

def test_json_import_preview_button_exists(main_window):
    win = main_window
    assert hasattr(win, "btn_preview_json_import")
    assert win.btn_preview_json_import.text() == "Preview JSON Import"
    assert win.btn_preview_json_import.isEnabled()


def test_json_import_preview_button_has_object_name(main_window):
    """Preview JSON Import button must have a stable objectName."""
    assert main_window.btn_preview_json_import.objectName() == "btnPreviewJsonImport"


@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
@patch("PySide6.QtWidgets.QMessageBox.question")
def test_json_import_preview_success_flow(mock_question, mock_open, main_window, tmp_path):
    win = main_window
    
    # Create valid JSON file
    valid_data = {
        "name": "Test Import Strat UI",
        "long_entry": {"logic": "AND", "conditions": [{"indicator": "SMA", "params": {"period": 20}, "operator": ">"}]},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []}
    }
    test_file = str(tmp_path / "valid_ui.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    mock_open.return_value = (test_file, "JSON Files (*.json)")
    
    # User clicks "No" (decline import)
    from PySide6.QtWidgets import QMessageBox
    mock_question.return_value = QMessageBox.StandardButton.No
    
    win._handle_import_json_preview()
    
    mock_question.assert_called_once()
    msg = mock_question.call_args[0][2]
    assert "Test Import Strat UI" in msg
    assert "VALID" in msg
    assert "Blocks: 4" in msg
    assert "Conditions: 1" in msg
    
    assert len(win._imported_strategies) == 0

@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
@patch("PySide6.QtWidgets.QMessageBox.warning")
def test_json_import_preview_invalid_flow(mock_warning, mock_open, main_window, tmp_path):
    win = main_window
    
    invalid_data = {
        "long_entry": {"logic": "AND", "conditions": []}
    }
    test_file = str(tmp_path / "invalid_ui.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f)
        
    mock_open.return_value = (test_file, "JSON Files (*.json)")
    
    win._handle_import_json_preview()
    
    mock_warning.assert_called_once()
    msg = mock_warning.call_args[0][2]
    assert "Missing required field: 'name'" in msg

@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
def test_json_import_preview_cancel_flow(mock_open, main_window):
    win = main_window
    
    mock_open.return_value = ("", "")
    
    # Should not crash, and should not show any message
    win._handle_import_json_preview()


def test_export_json_button_has_object_name(main_window):
    """Export JSON button must have a stable objectName."""
    assert hasattr(main_window, "btn_export_json")
    assert main_window.btn_export_json.objectName() == "btnExportJson"


def test_export_code_button_has_object_name(main_window):
    """Export Code button must have a stable objectName."""
    assert hasattr(main_window, "btn_export_python")
    assert main_window.btn_export_python.objectName() == "btnExportCode"
