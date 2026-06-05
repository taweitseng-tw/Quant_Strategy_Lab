"""Tests for Walk-Forward Efficiency (WFE) UI wiring."""

import pytest
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.services.validation_pipeline_service import PipelineConfig
from unittest.mock import patch


@pytest.fixture
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def main_window(app):
    window = MainWindow()
    yield window
    window.close()


def test_wfe_checkbox_exists_and_defaults_unchecked(main_window):
    """Verify the WFE checkbox exists on the Validate page and is unchecked by default."""
    assert hasattr(main_window, "wfe_checkbox")
    checkbox = main_window.wfe_checkbox
    
    assert checkbox.text() == "Calculate WFE"
    assert "diagnostic only" in checkbox.toolTip().lower()
    assert "slower" in checkbox.toolTip().lower()
    assert not checkbox.isChecked(), "WFE must be opt-in (unchecked by default)"


@patch("app.ui.main_window.run_validation_pipeline")
def test_wfe_unchecked_passes_calc_wfe_false(mock_run, main_window):
    """Verify that leaving the checkbox unchecked passes calc_wfe=False to the pipeline."""
    # Ensure it's unchecked
    main_window.wfe_checkbox.setChecked(False)
    
    # Trigger validation run
    main_window._handle_run()
    
    # Check what was passed
    mock_run.assert_called_once()
    kwargs = mock_run.call_args.kwargs
    config: PipelineConfig = kwargs.get("config")
    assert config is not None
    assert config.calc_wfe is False


@patch("app.ui.main_window.run_validation_pipeline")
def test_wfe_checked_passes_calc_wfe_true(mock_run, main_window):
    """Verify that checking the checkbox passes calc_wfe=True to the pipeline."""
    # Check it
    main_window.wfe_checkbox.setChecked(True)
    
    # Trigger validation run
    main_window._handle_run()
    
    # Check what was passed
    mock_run.assert_called_once()
    kwargs = mock_run.call_args.kwargs
    config: PipelineConfig = kwargs.get("config")
    assert config is not None
    assert config.calc_wfe is True
