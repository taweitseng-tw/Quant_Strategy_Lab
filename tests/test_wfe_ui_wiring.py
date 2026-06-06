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


# ---------------------------------------------------------------------------
# Remove Best N Trades config controls (Task 056H-Impl)
# ---------------------------------------------------------------------------


def test_remove_best_n_controls_exist_and_defaults(main_window):
    """Remove-best-N controls must exist with correct defaults."""
    assert hasattr(main_window, "remove_best_n_checkbox")
    assert hasattr(main_window, "remove_best_n_n_spin")
    assert hasattr(main_window, "remove_best_n_threshold_spin")

    # Defaults.
    assert not main_window.remove_best_n_checkbox.isChecked()
    assert main_window.remove_best_n_n_spin.value() == 3
    assert main_window.remove_best_n_n_spin.minimum() == 1
    assert main_window.remove_best_n_n_spin.maximum() == 50
    assert main_window.remove_best_n_threshold_spin.value() == 0.30
    assert main_window.remove_best_n_threshold_spin.minimum() == 0.01
    assert main_window.remove_best_n_threshold_spin.maximum() == 1.00

    # Spinboxes disabled when unchecked.
    assert not main_window.remove_best_n_n_spin.isEnabled()
    assert not main_window.remove_best_n_threshold_spin.isEnabled()


def test_remove_best_n_spins_enabled_when_checked(main_window):
    """Spinboxes must enable when checkbox is checked."""
    main_window.remove_best_n_checkbox.setChecked(True)
    assert main_window.remove_best_n_n_spin.isEnabled()
    assert main_window.remove_best_n_threshold_spin.isEnabled()

    main_window.remove_best_n_checkbox.setChecked(False)
    assert not main_window.remove_best_n_n_spin.isEnabled()
    assert not main_window.remove_best_n_threshold_spin.isEnabled()


@patch("app.ui.main_window.run_validation_pipeline")
def test_remove_best_n_unchecked_passes_false(mock_run, main_window):
    """Unchecked checkbox must pass run_remove_best_n_trades_stress=False."""
    main_window.remove_best_n_checkbox.setChecked(False)
    main_window._handle_run()

    mock_run.assert_called_once()
    config = mock_run.call_args.kwargs["config"]
    assert config.run_remove_best_n_trades_stress is False
    assert config.remove_best_n_trades_n == 3
    assert config.remove_best_n_trades_degradation_threshold == 0.30


@patch("app.ui.main_window.run_validation_pipeline")
def test_remove_best_n_checked_passes_custom_values(mock_run, main_window):
    """Checked checkbox must pass custom n and threshold values."""
    main_window.remove_best_n_checkbox.setChecked(True)
    main_window.remove_best_n_n_spin.setValue(5)
    main_window.remove_best_n_threshold_spin.setValue(0.25)
    main_window._handle_run()

    mock_run.assert_called_once()
    config = mock_run.call_args.kwargs["config"]
    assert config.run_remove_best_n_trades_stress is True
    assert config.remove_best_n_trades_n == 5
    assert config.remove_best_n_trades_degradation_threshold == 0.25
