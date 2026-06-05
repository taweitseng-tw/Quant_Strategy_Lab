"""Tests for JSON import optional persistence (Task 039D2)."""

import pytest
import os
import json
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication, QMessageBox
from app.ui.main_window import MainWindow

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture
def test_project(tmp_path):
    from app.services.project_service import ProjectService
    service = ProjectService()
    meta = service.create_project("Test Project", tmp_path / "test_proj")
    return service

@pytest.fixture
def main_window(qapp, test_project):
    win = MainWindow()
    win.project_service = test_project
    # ensure clean state
    win._imported_strategies = []
    win.ranked_data = []
    return win

@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
@patch("PySide6.QtWidgets.QMessageBox.question")
@patch("PySide6.QtWidgets.QMessageBox.information")
def test_import_json_valid_and_confirmed_saves_to_project(mock_info, mock_question, mock_open, main_window, tmp_path):
    valid_data = {
        "name": "Persistence Strat",
        "long_entry": {"logic": "AND", "conditions": []},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []}
    }
    test_file = str(tmp_path / "valid_persistence.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    mock_open.return_value = (test_file, "JSON Files (*.json)")
    # Question called twice: 1 for import, 1 for save
    mock_question.side_effect = [QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.Yes]
    
    main_window._handle_import_json_preview()
    
    # Verify saved
    from app.services.strategy_persistence_service import StrategyPersistenceService
    ps = StrategyPersistenceService(main_window.project_service.repository.db)
    
    loaded = ps.load_best_strategy(label="Persistence Strat", prefix="imported_")
    assert loaded is not None
    assert loaded.name == "imported_Persistence Strat"
    
    # Confirm it still injected into Results
    assert len(main_window._imported_strategies) == 1
    assert main_window._imported_strategies[0].name == "[Imported] Persistence Strat"

@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
@patch("PySide6.QtWidgets.QMessageBox.question")
def test_import_json_valid_and_declined_save_does_not_save(mock_question, mock_open, main_window, tmp_path):
    valid_data = {
        "name": "Decline Save Strat",
        "long_entry": {"logic": "AND", "conditions": []},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []}
    }
    test_file = str(tmp_path / "valid_decline_save.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    mock_open.return_value = (test_file, "JSON Files (*.json)")
    mock_question.side_effect = [QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No]
    
    main_window._handle_import_json_preview()
    
    from app.services.strategy_persistence_service import StrategyPersistenceService
    ps = StrategyPersistenceService(main_window.project_service.repository.db)
    
    loaded = ps.load_best_strategy(label="Decline Save Strat", prefix="imported_")
    assert loaded is None
    
    # Confirm still injected
    assert len(main_window._imported_strategies) == 1

@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
@patch("PySide6.QtWidgets.QMessageBox.question")
def test_import_json_no_project_does_not_ask_save(mock_question, mock_open, main_window, tmp_path):
    main_window.project_service.close_project()
    
    valid_data = {
        "name": "No Project Strat",
        "long_entry": {"logic": "AND", "conditions": []},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []}
    }
    test_file = str(tmp_path / "valid_no_project.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    mock_open.return_value = (test_file, "JSON Files (*.json)")
    mock_question.return_value = QMessageBox.StandardButton.Yes  # Only asked once
    
    main_window._handle_import_json_preview()
    
    assert mock_question.call_count == 1
    assert len(main_window._imported_strategies) == 1

@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
@patch("PySide6.QtWidgets.QMessageBox.question")
@patch("PySide6.QtWidgets.QMessageBox.critical")
@patch("app.services.strategy_persistence_service.StrategyPersistenceService.save_best_strategy")
def test_import_json_save_failure_is_graceful(mock_save, mock_critical, mock_question, mock_open, main_window, tmp_path):
    valid_data = {
        "name": "Fail Save Strat",
        "long_entry": {"logic": "AND", "conditions": []},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []}
    }
    test_file = str(tmp_path / "valid_fail_save.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    mock_open.return_value = (test_file, "JSON Files (*.json)")
    mock_question.side_effect = [QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.Yes]
    
    mock_save.side_effect = Exception("DB Disk Full")
    
    main_window._handle_import_json_preview()
    
    mock_critical.assert_called_once()
    assert "DB Disk Full" in mock_critical.call_args[0][2]
    
    # Confirm injection is intact
    assert len(main_window._imported_strategies) == 1

@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
@patch("PySide6.QtWidgets.QMessageBox.question")
@patch("PySide6.QtWidgets.QMessageBox.information")
@patch("app.services.strategy_persistence_service.StrategyPersistenceService.save_best_strategy")
def test_import_save_happens_exactly_once(mock_save, mock_info, mock_question, mock_open, main_window, tmp_path):
    valid_data = {
        "name": "Once Strat",
        "long_entry": {"logic": "AND", "conditions": []},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []}
    }
    test_file = str(tmp_path / "valid_once.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    mock_open.return_value = (test_file, "JSON Files (*.json)")
    mock_question.side_effect = [QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.Yes]
    
    main_window._handle_import_json_preview()
    
    # Save should be called exactly once
    assert mock_save.call_count == 1

@patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
@patch("app.services.strategy_persistence_service.StrategyPersistenceService.save_best_strategy")
def test_cancel_invalid_decline_paths_do_not_call_persistence_service(mock_save, mock_open, main_window, tmp_path):
    # Path 1: Cancel file dialog
    mock_open.return_value = ("", "")
    main_window._handle_import_json_preview()
    assert mock_save.call_count == 0
    
    # Path 2: Invalid JSON
    invalid_data = {"long_entry": {"logic": "AND", "conditions": []}}
    test_file = str(tmp_path / "invalid_save.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f)
    mock_open.return_value = (test_file, "JSON Files (*.json)")
    
    with patch("PySide6.QtWidgets.QMessageBox.warning"):
        main_window._handle_import_json_preview()
    assert mock_save.call_count == 0

def test_imported_prefix_does_not_list_ga_best_entries(main_window):
    from app.services.strategy_persistence_service import StrategyPersistenceService
    from core.models.strategy import Strategy
    ps = StrategyPersistenceService(main_window.project_service.repository.db)
    
    # Save a GA best strategy
    ga_strat = Strategy(name="GA Test")
    ps.save_best_strategy(ga_strat, label="latest", prefix="ga_best_")
    
    # Save an imported strategy
    import_strat = Strategy(name="Import Test")
    ps.save_best_strategy(import_strat, label="Import Test", prefix="imported_")
    
    # Verify separation
    ga_list = ps.list_saved_strategies(prefix="ga_best_")
    assert any(s.name == "ga_best_latest" for s in ga_list)
    assert not any(s.name == "imported_Import Test" for s in ga_list)
    
    import_list = ps.list_saved_strategies(prefix="imported_")
    assert any(s.name == "imported_Import Test" for s in import_list)
    assert not any(s.name == "ga_best_latest" for s in import_list)

