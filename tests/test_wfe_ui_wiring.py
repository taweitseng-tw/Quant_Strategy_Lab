"""Tests for Walk-Forward Efficiency (WFE) UI wiring."""

import pytest
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.services.validation_pipeline_service import PipelineConfig, PipelineResult
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


# ---------------------------------------------------------------------------
# Bootstrap MC UI controls (Task 057F-Impl)
# ---------------------------------------------------------------------------


def test_bootstrap_controls_exist_and_defaults(main_window):
    """Bootstrap controls must exist with correct defaults."""
    assert hasattr(main_window, "bootstrap_checkbox")
    assert hasattr(main_window, "bootstrap_iter_spin")
    assert hasattr(main_window, "bootstrap_conf_spin")

    assert not main_window.bootstrap_checkbox.isChecked()
    assert main_window.bootstrap_iter_spin.value() == 200
    assert main_window.bootstrap_conf_spin.value() == 0.95
    assert not main_window.bootstrap_iter_spin.isEnabled()
    assert not main_window.bootstrap_conf_spin.isEnabled()


def test_bootstrap_spins_enabled_when_checked(main_window):
    """Spinboxes must enable when checkbox is checked."""
    main_window.bootstrap_checkbox.setChecked(True)
    assert main_window.bootstrap_iter_spin.isEnabled()
    assert main_window.bootstrap_conf_spin.isEnabled()

    main_window.bootstrap_checkbox.setChecked(False)
    assert not main_window.bootstrap_iter_spin.isEnabled()
    assert not main_window.bootstrap_conf_spin.isEnabled()


@patch("app.ui.main_window.run_validation_pipeline")
def test_bootstrap_unchecked_passes_false(mock_run, main_window):
    """Unchecked checkbox must pass run_bootstrap_monte_carlo=False."""
    main_window.bootstrap_checkbox.setChecked(False)
    main_window._handle_run()

    mock_run.assert_called_once()
    config = mock_run.call_args.kwargs["config"]
    assert config.run_bootstrap_monte_carlo is False
    assert config.bootstrap_iterations == 200
    assert config.bootstrap_confidence_level == 0.95


@patch("app.ui.main_window.run_validation_pipeline")
def test_bootstrap_checked_passes_custom_values(mock_run, main_window):
    """Checked checkbox must pass custom values."""
    main_window.bootstrap_checkbox.setChecked(True)
    main_window.bootstrap_iter_spin.setValue(500)
    main_window.bootstrap_conf_spin.setValue(0.90)
    main_window._handle_run()

    mock_run.assert_called_once()
    config = mock_run.call_args.kwargs["config"]
    assert config.run_bootstrap_monte_carlo is True
    assert config.bootstrap_iterations == 500
    assert config.bootstrap_confidence_level == 0.90


# ---------------------------------------------------------------------------
# Archive Export button (Task 060U-Impl)
# ---------------------------------------------------------------------------


def test_export_archive_button_exists(main_window):
    """Export Archive button must exist on the Results page."""
    assert hasattr(main_window, "btn_export_archive")
    btn = main_window.btn_export_archive
    assert btn.text() == "Export Archive"


def test_export_archive_handler_guards_no_selection(main_window, tmp_path, monkeypatch):
    """Handler must guard: no ranked_data → returns without crash."""
    messages = []
    monkeypatch.setattr(
        main_window.log_panel,
        "add_message",
        lambda level, message: messages.append((level, message)),
    )
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.warning",
        lambda *args, **kwargs: None,
    )
    main_window._project_root = tmp_path
    if hasattr(main_window, "ranked_data"):
        main_window.ranked_data = []
    # The handler should return early when no selection exists.
    # Just verify it doesn't crash.
    main_window._handle_export_archive()
    assert ("WARN", "No strategy selected for archive export.") in messages


def test_export_archive_validation_field_accepts_pipeline_result():
    """Archive guard helpers must support PipelineResult dataclasses."""
    result = PipelineResult(
        baseline_metrics={"total_trades": 1},
        elimination_result={"passed": True},
    )

    assert MainWindow._validation_field(result, "elimination_result") == {"passed": True}
    assert MainWindow._validation_field(result, "baseline_metrics") == {"total_trades": 1}
