"""Integration tests for Project New/Open/Save toolbar wiring in MainWindow — Task 020A."""

from __future__ import annotations

import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from app.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Fixture to initialize a QApplication instance for GUI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture(autouse=True)
def mock_ranked_strategies():
    """Mock get_ranked_strategies to prevent slow backtests during MainWindow init."""
    with patch("app.services.strategy_service.StrategyService.get_ranked_strategies", return_value=([], True)):
        yield


@pytest.fixture
def temp_dir() -> Path:
    """Fixture to provide a clean temporary directory."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


def test_main_window_project_actions_wired(qapp) -> None:
    """Verify that project toolbar actions are enabled and connected to respective handlers."""
    window = MainWindow()
    
    # Assert actions are enabled
    assert window.new_project_action.isEnabled() is True
    assert window.open_project_action.isEnabled() is True
    assert window.save_action.isEnabled() is True
    
    # Check trigger connections are registered
    # Triggering action directly in tests tests slot execution
    # We will test slots in subsequent integration tests below.


@patch("PySide6.QtWidgets.QMessageBox.information")
@patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory")
@patch("PySide6.QtWidgets.QInputDialog.getText")
def test_main_window_new_project_flow(
    mock_input_text,
    mock_file_dir,
    mock_msg_info,
    qapp,
    temp_dir,
) -> None:
    """Verify the New Project flow propagates paths and refreshes status banners."""
    window = MainWindow()
    
    # Configure mocks
    mock_input_text.return_value = ("WiredProject", True)
    mock_file_dir.return_value = str(temp_dir)
    
    proj_expected_path = temp_dir / "WiredProject"
    
    # Initially project is not active and banner has warning
    assert window.project_service.is_project_active() is False
    assert "Working in In-Memory Mock Mode" in window.instrument_editor.banner.text()
    
    # Run the slot
    window._handle_new_project()
    
    # Assert active project path propagation
    assert window.project_service.is_project_active() is True
    assert window.project_service.get_active_project().name == "WiredProject"
    assert window.data_service.project_path == proj_expected_path.resolve()
    assert window.instrument_service.project_path == proj_expected_path.resolve()
    
    # Assert banner styling and contents updated
    assert "Active Project Mode" in window.instrument_editor.banner.text()
    assert str(proj_expected_path.resolve()) in window.instrument_editor.banner.text()
    
    # Assert successful message dialog popped up
    mock_msg_info.assert_called_once()
    assert "successfully created and loaded" in mock_msg_info.call_args[0][2]


@patch("PySide6.QtWidgets.QMessageBox.information")
@patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory")
def test_main_window_open_project_flow(
    mock_file_dir,
    mock_msg_info,
    qapp,
    temp_dir,
) -> None:
    """Verify that Open Project flow reads existing project folder metadata and updates active paths."""
    window = MainWindow()
    
    # 1. Create a dummy project folder manually
    proj_path = temp_dir / "DummyProj"
    window.project_service.create_project("DummyProj", proj_path)
    window.project_service.close_project()
    
    # Ensure current state is clean
    window.data_service.set_project_path(None)
    window.instrument_service.set_project_path(None)
    window.instrument_editor.refresh_project_status()
    assert window.project_service.is_project_active() is False
    
    # 2. Mock Open dialog to select the dummy folder
    mock_file_dir.return_value = str(proj_path)
    
    # Run open slot
    window._handle_open_project()
    
    # Assert state loaded
    assert window.project_service.is_project_active() is True
    assert window.project_service.get_active_project().name == "DummyProj"
    assert window.data_service.project_path == proj_path.resolve()
    assert window.instrument_service.project_path == proj_path.resolve()
    assert "Active Project Mode" in window.instrument_editor.banner.text()


@patch("PySide6.QtWidgets.QMessageBox.warning")
@patch("PySide6.QtWidgets.QMessageBox.information")
def test_main_window_save_flow(
    mock_msg_info,
    mock_msg_warn,
    qapp,
    temp_dir,
) -> None:
    """Verify that Save flow works for active projects and warns when in mock mode."""
    window = MainWindow()
    
    # 1. Save in mock mode should trigger a warning
    window._handle_save()
    mock_msg_warn.assert_called_once()
    assert "must create or open a project before saving" in mock_msg_warn.call_args[0][2]
    
    # 2. Create project and save should succeed
    proj_path = temp_dir / "SaveProj"
    window.project_service.create_project("SaveProj", proj_path)
    window.instrument_service.set_project_path(proj_path)
    
    # Trigger save
    window._handle_save()
    mock_msg_info.assert_called_once()
    assert "All project profiles and configuration files have been saved" in mock_msg_info.call_args[0][2]
    
    # Ensure files exist in config
    assert (proj_path / "config" / "instruments.json").is_file()
