"""Tests for UI wiring of Python strategy code export."""

from __future__ import annotations

from unittest.mock import patch
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from core.models.strategy import Strategy


@pytest.fixture(scope="module")
def qapp():
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()
    return app


@pytest.fixture(scope="module")
def window(qapp):
    with patch("app.services.strategy_service.StrategyService.get_ranked_strategies", return_value=([], True)):
        return MainWindow()


def _select_strategy(window: MainWindow, strategy: Strategy) -> None:
    window.results_table.table.clearSelection()
    window.results_table.table.setRowCount(0)
    window.ranked_data = [{"strategy": strategy}]
    window.results_table.table.setRowCount(1)
    window.results_table.table.selectRow(0)
    window._handle_strategy_selection_changed()


def test_export_code_py_path_calls_report_service(window, tmp_path: Path):
    """Test that clicking export saves the selected strategy as a .py file."""
    # Mock ranked data with a strategy
    mock_strategy = Strategy(name="Test Strategy XYZ")
    _select_strategy(window, mock_strategy)
    assert getattr(window, "btn_export_python", None) is not None
    assert window.btn_export_python.isEnabled()
    
    export_path = tmp_path / "test_strategy_xyz.py"
    
    # Mock QFileDialog and QMessageBox
    with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=(str(export_path), "Python Files (*.py)")), \
         patch("PySide6.QtWidgets.QMessageBox.information") as mock_info:
        
        # Trigger the click
        window.btn_export_python.click()
        
        # Verify file was written
        assert export_path.exists()
        
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        assert "Test Strategy XYZ" in content
        assert "Research/backtesting only" in content
        
        # Verify success message shown
        mock_info.assert_called_once()
        assert "successfully exported" in mock_info.call_args[0][2]


def test_export_code_cancel_does_not_export_or_warn(window, tmp_path: Path):
    """Test that cancelling the save dialog prevents export."""
    mock_strategy = Strategy(name="Test Strategy XYZ")
    _select_strategy(window, mock_strategy)
    
    # Cancel returns empty string
    with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=("", "")), \
         patch("PySide6.QtWidgets.QMessageBox.information") as mock_info:
        
        window.btn_export_python.click()
        
        # Verify no success message shown
        mock_info.assert_not_called()


def test_python_export_ui_sanitize_filename(window, tmp_path: Path):
    """Test that the default filename is sanitized correctly for invalid characters."""
    # Strategy name with invalid chars
    mock_strategy = Strategy(name='My <Bad> "Strat" /\\|?*')
    _select_strategy(window, mock_strategy)
    
    export_path = tmp_path / "My__Bad___Strat_______.py"
    
    with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=(str(export_path), "Python Files (*.py)")) as mock_dialog:
        with patch("PySide6.QtWidgets.QMessageBox.information"):
            window.btn_export_python.click()
            
            # Verify QFileDialog was called with the correct default filename
            args, kwargs = mock_dialog.call_args
            assert args[2] == "My__Bad___Strat_______.py"


def test_python_export_ui_empty_strategy_name(window, tmp_path: Path):
    """Test that an empty strategy name falls back to strategy_export.py"""
    mock_strategy = Strategy(name="")
    _select_strategy(window, mock_strategy)
    
    export_path = tmp_path / "strategy_export.py"
    
    with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=(str(export_path), "Python Files (*.py)")) as mock_dialog:
        with patch("PySide6.QtWidgets.QMessageBox.information"):
            window.btn_export_python.click()
            
            args, kwargs = mock_dialog.call_args
            assert args[2] == "strategy_export.py"


def test_export_code_cs_path_calls_report_service(window, tmp_path: Path):
    """Test that choosing NinjaTrader export routes correctly."""
    mock_strategy = Strategy(name="Ninja Test")
    _select_strategy(window, mock_strategy)
    
    export_path = tmp_path / "ninja_test.cs"
    
    with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=(str(export_path), "NinjaTrader C# (*.cs)")), \
         patch("PySide6.QtWidgets.QMessageBox.information") as mock_info:
        
        window.btn_export_python.click()
        
        assert export_path.exists()
        content = export_path.read_text(encoding="utf-8")
        assert "public class ExportedResearchStrategy" in content
        assert "Research/backtesting only" in content


def test_export_code_dialog_filter_includes_py_and_cs(window, tmp_path: Path):
    """Test that the save dialog filter contains both .py and .cs options."""
    mock_strategy = Strategy(name="Filter Test")
    _select_strategy(window, mock_strategy)
    
    with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=("", "")) as mock_dialog:
        window.btn_export_python.click()
        
        args, kwargs = mock_dialog.call_args
        filter_str = args[3]
        assert "Python Files (*.py)" in filter_str
        assert "NinjaTrader C# (*.cs)" in filter_str


def test_main_window_does_not_import_ninjatrader_exporter():
    """Verify that main_window.py does not directly import the NinjaTrader exporter."""
    file_path = Path("app/ui/main_window.py")
    content = file_path.read_text(encoding="utf-8")
    assert "ninjatrader_exporter" not in content


def test_export_code_no_selection_warns_once(window):
    """Test that clicking export without a selection shows a warning exactly once."""
    window.results_table.table.clearSelection()
    
    with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warning:
        window._handle_export_code()
        mock_warning.assert_called_once()
        assert "Please select a strategy" in mock_warning.call_args[0][2]


def test_export_code_failure_critical_once(window, tmp_path: Path):
    """Test that an export failure shows a critical error dialog exactly once."""
    mock_strategy = Strategy(name="Fail Test")
    _select_strategy(window, mock_strategy)
    
    export_path = tmp_path / "fail_test.py"
    
    with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=(str(export_path), "Python Files (*.py)")), \
         patch("app.services.report_service.ReportService.export_strategy_code", side_effect=Exception("Mocked Export Failure")), \
         patch("PySide6.QtWidgets.QMessageBox.critical") as mock_critical, \
         patch("PySide6.QtWidgets.QMessageBox.information") as mock_info:
        
        window.btn_export_python.click()
        
        mock_critical.assert_called_once()
        assert "Mocked Export Failure" in mock_critical.call_args[0][2]
        mock_info.assert_not_called()
