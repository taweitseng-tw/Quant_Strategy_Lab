"""Tests for JSON import injection into Results ranking (Task 039D1)."""

import pytest
import os
import json
from unittest.mock import patch
from PySide6.QtWidgets import QApplication, QMessageBox
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
    main_window._imported_strategies = []
    main_window.ranked_data = []

@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
def test_import_json_preview_cancel_does_not_mutate_state(mock_open, main_window):
    mock_open.return_value = ("", "")
    main_window._handle_import_json_preview()
    assert len(main_window._imported_strategies) == 0

@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
@patch("PySide6.QtWidgets.QMessageBox.warning")
def test_import_json_invalid_does_not_mutate_state(mock_warning, mock_open, main_window, tmp_path):
    invalid_data = {"long_entry": {"logic": "AND", "conditions": []}}
    test_file = str(tmp_path / "invalid_inject.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f)
        
    mock_open.return_value = (test_file, "JSON Files (*.json)")
    
    main_window._handle_import_json_preview()
    assert len(main_window._imported_strategies) == 0

@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
@patch("PySide6.QtWidgets.QMessageBox.question")
def test_import_json_valid_but_user_declines_does_not_inject(mock_question, mock_open, main_window, tmp_path):
    valid_data = {
        "name": "Super Strat Decline",
        "long_entry": {"logic": "AND", "conditions": [{"indicator": "SMA", "params": {"period": 20}, "operator": ">"}]},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []}
    }
    test_file = str(tmp_path / "valid_decline.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    mock_open.return_value = (test_file, "JSON Files (*.json)")
    mock_question.return_value = QMessageBox.StandardButton.No
    
    main_window._handle_import_json_preview()
    assert len(main_window._imported_strategies) == 0

@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
@patch("PySide6.QtWidgets.QMessageBox.question")
def test_import_json_valid_and_confirmed_injects_strategy(mock_question, mock_open, main_window, tmp_path):
    valid_data = {
        "name": "Super Strat Inject",
        "long_entry": {"logic": "AND", "conditions": [{"indicator": "SMA", "params": {"period": 20}, "operator": ">"}]},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []}
    }
    test_file = str(tmp_path / "valid_inject.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    mock_open.return_value = (test_file, "JSON Files (*.json)")
    mock_question.return_value = QMessageBox.StandardButton.Yes
    
    # We use a smaller deterministic dataset mock for speed or just let it run.
    main_window._handle_import_json_preview()
    
    mock_question.assert_called_once()
    assert len(main_window._imported_strategies) == 1
    assert main_window._imported_strategies[0].name == "[Imported] Super Strat Inject"
    
    # ranked_data should now contain the imported strategy
    
    imported_entry = next((item for item in main_window.ranked_data if item["strategy"].name == "[Imported] Super Strat Inject"), None)
    assert isinstance(imported_entry, dict), "Imported entry should be found"
    assert isinstance(imported_entry.get("metrics"), dict)
    assert isinstance(imported_entry.get("trades"), list)
    
    # Verify table has rows matching ranked_data
    assert main_window.results_table.table.rowCount() == len(main_window.ranked_data)

@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
@patch("PySide6.QtWidgets.QMessageBox.question")
def test_imported_and_ga_best_strategies_coexist_in_ranking(mock_question, mock_open, main_window, tmp_path):
    from core.models.strategy import Strategy
    main_window._latest_ga_strategy = Strategy(name="GA Best Strat")
    
    valid_data = {
        "name": "Coexist Strat",
        "long_entry": {"logic": "AND", "conditions": []},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []}
    }
    test_file = str(tmp_path / "valid_coexist.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    mock_open.return_value = (test_file, "JSON Files (*.json)")
    mock_question.return_value = QMessageBox.StandardButton.Yes
    
    main_window._handle_import_json_preview()
    
    assert main_window._latest_ga_strategy.name == "GA Best Strat"
    assert len(main_window._imported_strategies) == 1
    
    names_in_ranking = [item["strategy"].name for item in main_window.ranked_data]
    assert "GA Best Strat" in names_in_ranking
    assert "[Imported] Coexist Strat" in names_in_ranking

@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
@patch("PySide6.QtWidgets.QMessageBox.question")
def test_repeated_imports_have_stable_visible_names(mock_question, mock_open, main_window, tmp_path):
    valid_data = {
        "name": "Repeat Strat",
        "long_entry": {"logic": "AND", "conditions": []},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []}
    }
    test_file = str(tmp_path / "valid_repeat.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    mock_open.return_value = (test_file, "JSON Files (*.json)")
    mock_question.return_value = QMessageBox.StandardButton.Yes
    
    main_window._handle_import_json_preview()
    main_window._handle_import_json_preview()
    
    assert len(main_window._imported_strategies) == 2
    assert main_window._imported_strategies[0].name == "[Imported] Repeat Strat"
    assert main_window._imported_strategies[1].name == "[Imported] Repeat Strat (2)"
    
    names_in_ranking = [item["strategy"].name for item in main_window.ranked_data]
    assert "[Imported] Repeat Strat" in names_in_ranking
    assert "[Imported] Repeat Strat (2)" in names_in_ranking

@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
@patch("PySide6.QtWidgets.QMessageBox.question")
def test_imported_strategy_selection_updates_results_widgets(mock_question, mock_open, main_window, tmp_path):
    valid_data = {
        "name": "Selection Strat",
        "long_entry": {"logic": "AND", "conditions": []},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []}
    }
    test_file = str(tmp_path / "valid_selection.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    mock_open.return_value = (test_file, "JSON Files (*.json)")
    mock_question.return_value = QMessageBox.StandardButton.Yes
    
    main_window._handle_import_json_preview()
    
    row = next((i for i, item in enumerate(main_window.ranked_data) if item["strategy"].name == "[Imported] Selection Strat"), -1)
    assert row != -1, "Imported strategy not found in ranked_data"
    main_window.results_table.table.selectRow(row)
    
    # Assert detail widget was updated
    assert main_window.strategy_detail.lbl_name.text() == "[Imported] Selection Strat"

