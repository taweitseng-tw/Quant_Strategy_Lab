"""Tests for Walk-Forward Efficiency (WFE) UI wiring."""

import json

import pytest
from PySide6.QtWidgets import QApplication, QLabel
from app.ui.main_window import MainWindow
from app.services.validation_pipeline_service import PipelineConfig, PipelineResult
from core.models.strategy import Strategy
from unittest.mock import patch

from data_engine.quality_checker import DataQualityReport


def _success_result(total_pnl: int = 1000) -> PipelineResult:
    """Return a minimal PipelineResult that passes elimination."""
    return PipelineResult(
        baseline_metrics={
            "total_pnl": total_pnl,
            "profit_factor": 1.5,
            "total_trades": 10,
        },
        elimination_result={"passed": True},
    )


def _set_prior_validation_state(window: MainWindow, total_pnl: int = 1000) -> None:
    """Set up a prior successful validation state on *window*."""
    window.latest_validation_result = _success_result(total_pnl=total_pnl)
    window.export_action.setEnabled(True)
    window.export_action.setToolTip("Export the latest validation report.")
    window.validation_status_label.setText("Validation completed.")
    window.validation_status_label.show()


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


# ---------------------------------------------------------------------------
# Archive export handler wiring (Task 061C-Impl)
# ---------------------------------------------------------------------------


def test_export_archive_handler_exists(main_window):
    """Export Archive handler must exist."""
    assert hasattr(main_window, "_handle_export_archive")
    assert callable(main_window._handle_export_archive)


def test_export_archive_handler_no_selection_blocks(main_window):
    """Handler must return early when no strategy selected (no crash)."""
    main_window.ranked_data = None
    # Just verify no exception; can't assert service not called since import is local.
    main_window._handle_export_archive()
    # If we got here without an exception, the guard worked.


def test_export_archive_handler_calls_export_service(main_window, tmp_path, monkeypatch):
    """Valid UI archive export path must call ArchiveExportService."""
    strategy = Strategy(name="archive-strategy")
    snapshot = tmp_path / "snapshot.csv"
    snapshot.write_text("datetime,open,high,low,close,volume\n", encoding="utf-8")

    class _Range:
        def topRow(self):
            return 0

    class _StrategyService:
        def list_all_raw(self):
            return [{
                "name": strategy.name,
                "strategy_json": json.dumps({
                    "name": strategy.name,
                    "strategy_uid": "uid-ok",
                    "dataset_id": 7,
                }),
            }]

    calls = []

    class _ExportService:
        def __init__(self, data_source):
            self.data_source = data_source

        def export_strategy_archive(self, **kwargs):
            calls.append(kwargs)
            return tmp_path / "exports" / "archives" / "uid-ok"

    messages = []
    main_window._project_root = tmp_path
    main_window.ranked_data = [{"strategy": strategy}]
    main_window.latest_validation_result = {
        "strategy_uid": "uid-ok",
        "elimination_result": {"passed": True},
        "baseline_metrics": {"total_trades": 1},
    }
    monkeypatch.setattr(
        main_window.results_table.table,
        "selectedRanges",
        lambda: [_Range()],
    )
    monkeypatch.setattr(
        main_window,
        "_get_strategy_persistence_service",
        lambda: _StrategyService(),
    )
    monkeypatch.setattr(
        main_window.data_service,
        "get_dataset_raw_by_id",
        lambda dataset_id: {"id": dataset_id, "normalized_path": str(snapshot)},
    )
    monkeypatch.setattr(
        main_window.log_panel,
        "add_message",
        lambda level, message: messages.append((level, message)),
    )
    monkeypatch.setattr("app.ui.main_window.QMessageBox.information", lambda *a, **k: None)
    monkeypatch.setattr("app.ui.main_window.QMessageBox.warning", lambda *a, **k: None)
    monkeypatch.setattr("app.ui.main_window.QMessageBox.critical", lambda *a, **k: None)
    monkeypatch.setattr("app.services.archive_export_service.ArchiveExportService", _ExportService)

    main_window._handle_export_archive()

    assert len(calls) == 1
    assert calls[0]["strategy_uid"] == "uid-ok"
    assert calls[0]["dataset_snapshot_path"] == str(snapshot)
    assert any(level == "INFO" and "Archive successfully exported" in msg for level, msg in messages)


def test_export_archive_handler_validation_uid_mismatch_blocks_service(
    main_window, tmp_path, monkeypatch,
):
    """A validation result for a different strategy UID must not export."""
    strategy = Strategy(name="archive-strategy")
    snapshot = tmp_path / "snapshot.csv"
    snapshot.write_text("datetime,open,high,low,close,volume\n", encoding="utf-8")

    class _Range:
        def topRow(self):
            return 0

    class _StrategyService:
        def list_all_raw(self):
            return [{
                "name": strategy.name,
                "strategy_json": json.dumps({
                    "name": strategy.name,
                    "strategy_uid": "uid-ok",
                    "dataset_id": 7,
                }),
            }]

    calls = []

    class _ExportService:
        def __init__(self, data_source):
            self.data_source = data_source

        def export_strategy_archive(self, **kwargs):
            calls.append(kwargs)
            return tmp_path / "unexpected"

    warnings = []
    main_window._project_root = tmp_path
    main_window.ranked_data = [{"strategy": strategy}]
    main_window.latest_validation_result = {
        "strategy_uid": "uid-other",
        "elimination_result": {"passed": True},
        "baseline_metrics": {"total_trades": 1},
    }
    monkeypatch.setattr(
        main_window.results_table.table,
        "selectedRanges",
        lambda: [_Range()],
    )
    monkeypatch.setattr(
        main_window,
        "_get_strategy_persistence_service",
        lambda: _StrategyService(),
    )
    monkeypatch.setattr(
        main_window.data_service,
        "get_dataset_raw_by_id",
        lambda dataset_id: {"id": dataset_id, "normalized_path": str(snapshot)},
    )
    monkeypatch.setattr("app.ui.main_window.QMessageBox.information", lambda *a, **k: None)
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.warning",
        lambda *args, **kwargs: warnings.append(args),
    )
    monkeypatch.setattr("app.ui.main_window.QMessageBox.critical", lambda *a, **k: None)
    monkeypatch.setattr("app.services.archive_export_service.ArchiveExportService", _ExportService)

    main_window._handle_export_archive()

    assert calls == []
    assert warnings


def test_export_archive_handler_missing_dataset_metadata_blocks_service(
    main_window, tmp_path, monkeypatch,
):
    """Missing dataset metadata must stop before ArchiveExportService."""
    strategy = Strategy(name="archive-strategy")

    class _Range:
        def topRow(self):
            return 0

    class _StrategyService:
        def list_all_raw(self):
            return [{
                "name": strategy.name,
                "strategy_json": json.dumps({
                    "name": strategy.name,
                    "strategy_uid": "uid-ok",
                    "dataset_id": 7,
                }),
            }]

    calls = []

    class _ExportService:
        def __init__(self, data_source):
            self.data_source = data_source

        def export_strategy_archive(self, **kwargs):
            calls.append(kwargs)
            return tmp_path / "unexpected"

    warnings = []
    main_window._project_root = tmp_path
    main_window.ranked_data = [{"strategy": strategy}]
    main_window.latest_validation_result = {
        "strategy_uid": "uid-ok",
        "elimination_result": {"passed": True},
        "baseline_metrics": {"total_trades": 1},
    }
    monkeypatch.setattr(
        main_window.results_table.table,
        "selectedRanges",
        lambda: [_Range()],
    )
    monkeypatch.setattr(
        main_window,
        "_get_strategy_persistence_service",
        lambda: _StrategyService(),
    )
    monkeypatch.setattr(main_window.data_service, "get_dataset_raw_by_id", lambda dataset_id: None)
    monkeypatch.setattr("app.ui.main_window.QMessageBox.information", lambda *a, **k: None)
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.warning",
        lambda *args, **kwargs: warnings.append(args),
    )
    monkeypatch.setattr("app.ui.main_window.QMessageBox.critical", lambda *a, **k: None)
    monkeypatch.setattr("app.services.archive_export_service.ArchiveExportService", _ExportService)

    main_window._handle_export_archive()

    assert calls == []
    assert warnings


# ---------------------------------------------------------------------------
# Price-noise stress UI controls (Task 062J-Impl)
# ---------------------------------------------------------------------------


def test_price_noise_controls_exist_and_defaults(main_window):
    """Price-noise controls must exist with correct defaults."""
    assert hasattr(main_window, 'price_noise_checkbox')
    assert hasattr(main_window, 'price_noise_pct_spin')
    assert hasattr(main_window, 'price_noise_iter_spin')
    assert hasattr(main_window, 'price_noise_seed_spin')
    assert not main_window.price_noise_checkbox.isChecked()
    assert main_window.price_noise_pct_spin.value() == 0.005
    assert main_window.price_noise_iter_spin.value() == 50
    assert main_window.price_noise_seed_spin.value() == 42
    assert not main_window.price_noise_pct_spin.isEnabled()
    assert not main_window.price_noise_iter_spin.isEnabled()
    assert not main_window.price_noise_seed_spin.isEnabled()


def test_price_noise_noise_input_uses_fraction_wording(main_window):
    """Noise input wording must not imply percent units while config uses fractions."""
    labels = [label.text() for label in main_window.findChildren(QLabel)]

    assert "Noise fraction:" in labels
    assert "Noise %:" not in labels
    assert "0.005 = 0.5%" in main_window.price_noise_pct_spin.toolTip()


def test_price_noise_spins_enabled_when_checked(main_window):
    """Spinboxes must enable when checkbox is checked."""
    main_window.price_noise_checkbox.setChecked(True)
    assert main_window.price_noise_pct_spin.isEnabled()
    assert main_window.price_noise_iter_spin.isEnabled()
    assert main_window.price_noise_seed_spin.isEnabled()
    main_window.price_noise_checkbox.setChecked(False)
    assert not main_window.price_noise_pct_spin.isEnabled()
    assert not main_window.price_noise_iter_spin.isEnabled()
    assert not main_window.price_noise_seed_spin.isEnabled()


@patch("app.ui.main_window.run_validation_pipeline")
def test_price_noise_unchecked_passes_false(mock_run, main_window):
    """Unchecked checkbox must pass run_price_noise_stress=False."""
    main_window.price_noise_checkbox.setChecked(False)
    main_window._handle_run()
    mock_run.assert_called_once()
    config = mock_run.call_args.kwargs["config"]
    assert config.run_price_noise_stress is False
    assert config.price_noise_pct == 0.005
    assert config.price_noise_iterations == 50
    assert config.price_noise_seed == 42


@patch("app.ui.main_window.run_validation_pipeline")
def test_price_noise_checked_passes_custom_values(mock_run, main_window):
    """Checked checkbox must pass custom values."""
    main_window.price_noise_checkbox.setChecked(True)
    main_window.price_noise_pct_spin.setValue(0.02)
    main_window.price_noise_iter_spin.setValue(100)
    main_window.price_noise_seed_spin.setValue(77)
    main_window._handle_run()
    mock_run.assert_called_once()
    config = mock_run.call_args.kwargs["config"]
    assert config.run_price_noise_stress is True
    assert config.price_noise_pct == 0.02
    assert config.price_noise_iterations == 100
    assert config.price_noise_seed == 77


# ---------------------------------------------------------------------------
# Precheck UI controls (Task 063E-Impl)
# ---------------------------------------------------------------------------


def test_precheck_controls_exist_and_defaults(main_window):
    """Precheck controls must exist with correct defaults."""
    assert hasattr(main_window, "precheck_checkbox")
    assert hasattr(main_window, "precheck_nonpositive_checkbox")
    assert not main_window.precheck_checkbox.isChecked()
    assert not main_window.precheck_nonpositive_checkbox.isChecked()
    assert not main_window.precheck_nonpositive_checkbox.isEnabled()


def test_precheck_nonpositive_enabled_when_parent_checked(main_window):
    """Non-positive checkbox must enable when parent is checked."""
    assert not main_window.precheck_nonpositive_checkbox.isEnabled()
    main_window.precheck_checkbox.setChecked(True)
    assert main_window.precheck_nonpositive_checkbox.isEnabled()
    main_window.precheck_checkbox.setChecked(False)
    assert not main_window.precheck_nonpositive_checkbox.isEnabled()


@patch("app.ui.main_window.run_validation_pipeline")
def test_precheck_unchecked_passes_false(mock_run, main_window):
    """Unchecked parent must pass both precheck fields as False."""
    main_window.precheck_checkbox.setChecked(False)
    main_window._handle_run()
    mock_run.assert_called_once()
    config = mock_run.call_args.kwargs["config"]
    assert config.run_is_baseline_quality_precheck is False
    assert config.fail_is_baseline_on_nonpositive_pnl is False


@patch("app.ui.main_window.run_validation_pipeline")
def test_precheck_parent_checked_nonpositive_checked(mock_run, main_window):
    """Parent + nonpositive both checked must pass True/True."""
    main_window.precheck_checkbox.setChecked(True)
    main_window.precheck_nonpositive_checkbox.setChecked(True)
    main_window._handle_run()
    mock_run.assert_called_once()
    config = mock_run.call_args.kwargs["config"]
    assert config.run_is_baseline_quality_precheck is True
    assert config.fail_is_baseline_on_nonpositive_pnl is True


@patch("app.ui.main_window.run_validation_pipeline")
def test_precheck_parent_checked_nonpositive_unchecked(mock_run, main_window):
    """Parent checked but nonpositive unchecked must pass True/False."""
    main_window.precheck_checkbox.setChecked(True)
    main_window.precheck_nonpositive_checkbox.setChecked(False)
    main_window._handle_run()
    mock_run.assert_called_once()
    config = mock_run.call_args.kwargs["config"]
    assert config.run_is_baseline_quality_precheck is True
    assert config.fail_is_baseline_on_nonpositive_pnl is False


# ---------------------------------------------------------------------------
# Data import format guidance — Task 065A
# ---------------------------------------------------------------------------


def test_data_format_guide_label_exists(main_window):
    """The Data page must show a format guidance label near the import button."""
    assert hasattr(main_window, "data_format_guide_label")
    label = main_window.data_format_guide_label
    assert label.text() != ""
    assert "CSV" in label.text() or "csv" in label.text() or "Date" in label.text()


# ---------------------------------------------------------------------------
# Validation run progress indicator (Task 071A-071F)
# ---------------------------------------------------------------------------


def test_validation_status_label_exists_and_hidden_by_default(main_window):
    """Status label must exist on the Validate page and be hidden initially."""
    assert hasattr(main_window, "validation_status_label")
    label = main_window.validation_status_label
    assert label.isHidden(), "Status must be hidden by default"


def test_validation_status_set_before_pipeline_call(main_window):
    """Verify status is set to 'Validating...' before the pipeline service runs."""
    captured = {}

    def _side_effect(*args, **kwargs):
        # Capture label state at the moment the mock is called.
        captured["text"] = main_window.validation_status_label.text()
        captured["hidden"] = main_window.validation_status_label.isHidden()
        return _success_result()

    patcher = patch("app.ui.main_window.run_validation_pipeline", side_effect=_side_effect)
    patcher.start()
    try:
        main_window._handle_run()
    finally:
        patcher.stop()

    assert not captured["hidden"], "Status must be visible when pipeline runs"
    assert captured["text"] == "Validating...", (
        f"Expected 'Validating...' before pipeline call, got {captured['text']!r}"
    )


@patch("app.ui.main_window.run_validation_pipeline")
def test_validation_status_shows_completed_on_success(mock_run, main_window):
    """Status label must show completion message after success."""
    mock_run.return_value = _success_result()
    main_window._handle_run()
    assert not main_window.validation_status_label.isHidden()
    assert "completed" in main_window.validation_status_label.text().lower()


@patch("app.ui.main_window.run_validation_pipeline")
def test_validation_status_shows_error_on_failure(mock_run, main_window):
    """Status label must show error message when pipeline raises."""
    mock_run.side_effect = ValueError("Test pipeline crash")
    main_window._handle_run()
    assert not main_window.validation_status_label.isHidden()
    assert "failed" in main_window.validation_status_label.text().lower()
    assert "Test pipeline crash" in main_window.validation_status_label.text()


# ---------------------------------------------------------------------------
# Run validation button guard (Task 073A-073F)
# ---------------------------------------------------------------------------


def test_run_button_disabled_during_pipeline(main_window):
    """Run button must be disabled before the pipeline service is called."""
    captured = {}

    def _side_effect(*args, **kwargs):
        captured["enabled"] = main_window.run_action.isEnabled()
        return _success_result()

    patcher = patch("app.ui.main_window.run_validation_pipeline", side_effect=_side_effect)
    patcher.start()
    try:
        main_window._handle_run()
    finally:
        patcher.stop()

    assert captured.get("enabled") is False, "Run button must be disabled when pipeline is called"


@patch("app.ui.main_window.run_validation_pipeline")
def test_run_button_reenabled_after_success(mock_run, main_window):
    """Run button must be re-enabled after successful pipeline completion."""
    mock_run.return_value = _success_result()
    main_window._handle_run()
    assert main_window.run_action.isEnabled(), "Run button must be enabled after success"


@patch("app.ui.main_window.run_validation_pipeline")
def test_run_button_reenabled_after_error(mock_run, main_window):
    """Run button must be re-enabled after pipeline error."""
    mock_run.side_effect = ValueError("Pipeline failure")
    main_window._handle_run()
    assert main_window.run_action.isEnabled(), "Run button must be enabled after error"


# ---------------------------------------------------------------------------
# Export report button guard (Task 074A-074F)
# ---------------------------------------------------------------------------


def test_export_button_disabled_by_default(main_window):
    """Export button must be disabled until validation succeeds."""
    assert not main_window.export_action.isEnabled()


def test_export_button_disabled_during_pipeline(main_window):
    """Export button must be disabled before the pipeline service is called."""
    captured = {}

    def _side_effect(*args, **kwargs):
        captured["enabled"] = main_window.export_action.isEnabled()
        return _success_result()

    patcher = patch("app.ui.main_window.run_validation_pipeline", side_effect=_side_effect)
    patcher.start()
    try:
        main_window._handle_run()
    finally:
        patcher.stop()

    assert captured.get("enabled") is False, "Export button must be disabled when pipeline is called"


@patch("app.ui.main_window.run_validation_pipeline")
def test_export_button_reenabled_after_success(mock_run, main_window):
    """Export button must be re-enabled after successful pipeline completion."""
    mock_run.return_value = _success_result()
    main_window._handle_run()
    assert main_window.export_action.isEnabled(), "Export button must be enabled after success"


@patch("app.ui.main_window.run_validation_pipeline")
def test_export_button_disabled_after_error(mock_run, main_window):
    """Export button must remain disabled after pipeline error."""
    main_window.export_action.setEnabled(True)
    mock_run.side_effect = ValueError("Pipeline failure")
    main_window._handle_run()
    assert not main_window.export_action.isEnabled(), "Export must stay disabled after error"


# ---------------------------------------------------------------------------
# Validation state reset on dataset change (Task 075A-075F)
# ---------------------------------------------------------------------------


def test_reset_validation_state_clears_status(main_window):
    """_reset_validation_state must hide label, clear text, and clear result."""
    # Simulate a successful run state
    main_window.validation_status_label.setText("Validation completed.")
    main_window.validation_status_label.show()
    main_window.latest_validation_result = PipelineResult(
        baseline_metrics={"total_pnl": 100},
        elimination_result={"passed": True},
    )
    main_window.export_action.setEnabled(True)

    # Reset
    main_window._reset_validation_state()

    assert main_window.validation_status_label.isHidden()
    assert main_window.validation_status_label.text() == ""
    assert main_window.latest_validation_result is None


def test_reset_validation_state_disables_export(main_window):
    """_reset_validation_state must disable the export button."""
    main_window.export_action.setEnabled(True)
    main_window._reset_validation_state()
    assert not main_window.export_action.isEnabled(), "Export must be disabled after reset"


def test_reset_validation_state_does_not_touch_run(main_window):
    """_reset_validation_state must not affect the run button."""
    main_window.run_action.setEnabled(True)
    main_window._reset_validation_state()
    assert main_window.run_action.isEnabled(), "Run button must remain enabled"


# ---------------------------------------------------------------------------
# Export report tooltip hints (Task 076A-076F)
# ---------------------------------------------------------------------------


def test_export_action_default_tooltip(main_window):
    """Default tooltip must explain why export is disabled."""
    tip = main_window.export_action.toolTip()
    assert tip and "validation" in tip.lower(), f"Tooltip should mention validation, got: {tip!r}"


@patch("app.ui.main_window.run_validation_pipeline")
def test_export_tooltip_updated_after_success(mock_run, main_window):
    """Tooltip must indicate export is available after successful validation."""
    mock_run.return_value = _success_result()
    main_window._handle_run()
    tip = main_window.export_action.toolTip()
    assert "export" in tip.lower() and "report" in tip.lower(), (
        f"Tooltip should mention export, got: {tip!r}"
    )


@patch("app.ui.main_window.run_validation_pipeline")
def test_export_tooltip_reset_after_error(mock_run, main_window):
    """Tooltip must reset to disabled explanation after pipeline error."""
    mock_run.side_effect = ValueError("Pipeline failure")
    main_window._handle_run()
    tip = main_window.export_action.toolTip()
    assert "failed" in tip.lower(), f"Tooltip should mention failure, got: {tip!r}"


def test_export_tooltip_reset_after_reset(main_window):
    """Tooltip must reset to disabled explanation after _reset_validation_state."""
    main_window.export_action.setToolTip("Export the latest validation report.")
    main_window._reset_validation_state()
    tip = main_window.export_action.toolTip()
    assert "run validation" in tip.lower(), f"Tooltip should mention run validation, got: {tip!r}"


@patch("app.ui.main_window.QMessageBox.warning")
def test_validation_abort_quality_failure_disables_export(mock_warning, main_window):
    """Validation abort on failed quality checks must keep export disabled, re-enable run, and explain why."""
    # Set up a non-passing quality report so the abort guard fires.
    main_window._loaded_dataset = "not-none"  # non-mock path
    main_window._active_dataset_quality = DataQualityReport(passed=False, errors=["bad data"])

    # Export was previously enabled (simulating a prior successful run).
    main_window.export_action.setEnabled(True)
    main_window.export_action.setToolTip("Export the latest validation report.")
    main_window.run_action.setEnabled(True)

    main_window._handle_run()

    # Verify export is disabled and has explanatory tooltip.
    assert not main_window.export_action.isEnabled(), (
        "Export must stay disabled after quality abort"
    )
    tip = main_window.export_action.toolTip()
    assert "quality" in tip.lower(), f"Tooltip should mention quality, got: {tip!r}"

    # Verify run button is re-enabled.
    assert main_window.run_action.isEnabled(), "Run button must be re-enabled after abort"

    # Export tooltip explains the cause.
    assert "re-import" in tip.lower() or "quality" in tip.lower(), (
        f"Tooltip should explain the blocked state, got: {tip!r}"
    )


# ---------------------------------------------------------------------------
# Project context validation state reset (Task 078A-078F)
# ---------------------------------------------------------------------------


def test_new_project_resets_validation_state(main_window, tmp_path, monkeypatch):
    """Creating a new project must clear stale validation state."""
    from pathlib import Path
    from PySide6.QtWidgets import QInputDialog, QFileDialog, QMessageBox

    # Simulate prior successful validation run.
    _set_prior_validation_state(main_window, total_pnl=100)

    # Patch Qt dialogs to return fake values.
    monkeypatch.setattr(QInputDialog, "getText", lambda *a, **k: ("test_project", True))
    monkeypatch.setattr(
        QFileDialog, "getExistingDirectory", lambda *a, **k: str(tmp_path)
    )
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.No)
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: None)

    # Mock project service to return a valid ProjectMeta.
    from core.models.project import ProjectMeta

    mock_meta = ProjectMeta(name="test_project", root_path=Path(tmp_path / "test_project"))
    monkeypatch.setattr(
        main_window.project_service,
        "create_project",
        lambda name, root_path, overwrite=False: mock_meta,
    )
    # Repository.db raises RuntimeError when no project is active —
    # bypass by patching set_db to a no-op and setting _db directly.
    monkeypatch.setattr(main_window.data_service, "set_db", lambda db: None)
    object.__setattr__(main_window.project_service.repository, "_db", "mock://db")
    monkeypatch.setattr(
        main_window.instrument_service, "get_active_profile", lambda: None,
    )

    main_window._handle_new_project()

    assert main_window.validation_status_label.isHidden()
    assert main_window.validation_status_label.text() == ""
    assert main_window.latest_validation_result is None
    assert not main_window.export_action.isEnabled(), "Export must be disabled after new project"
    assert "run validation" in main_window.export_action.toolTip().lower(), (
        f"Tooltip should explain disabled state, got: {main_window.export_action.toolTip()!r}"
    )



def test_open_project_resets_validation_state(main_window, tmp_path, monkeypatch):
    """Opening a project must clear stale validation state."""
    from pathlib import Path
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    # Simulate prior successful validation run.
    _set_prior_validation_state(main_window, total_pnl=100)

    # Patch Qt dialogs.
    monkeypatch.setattr(
        QFileDialog, "getExistingDirectory", lambda *a, **k: str(tmp_path / "test_project")
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: None)

    # Mock project service to return a valid ProjectMeta.
    from core.models.project import ProjectMeta

    mock_meta = ProjectMeta(name="test_project", root_path=Path(tmp_path / "test_project"))
    monkeypatch.setattr(
        main_window.project_service,
        "open_project",
        lambda project_dir: mock_meta,
    )
    # Repository.db raises RuntimeError when no project is active;
    # patch set_db and set _db directly.
    monkeypatch.setattr(main_window.data_service, "set_db", lambda db: None)
    object.__setattr__(main_window.project_service.repository, "_db", "mock://db")
    monkeypatch.setattr(
        main_window, "_get_strategy_persistence_service", lambda: None,
    )
    monkeypatch.setattr(
        main_window.instrument_service, "get_active_profile", lambda: None,
    )

    main_window._handle_open_project()

    assert main_window.validation_status_label.isHidden()
    assert main_window.validation_status_label.text() == ""
    assert main_window.latest_validation_result is None
    assert not main_window.export_action.isEnabled(), "Export must be disabled after open project"
    assert "run validation" in main_window.export_action.toolTip().lower(), (
        f"Tooltip should explain disabled state, got: {main_window.export_action.toolTip()!r}"
    )


# ---------------------------------------------------------------------------
# Stable objectName for validation/report controls (Task 079A-079F)
# ---------------------------------------------------------------------------


def test_validation_status_label_has_object_name(main_window):
    """validation_status_label must have a stable objectName."""
    assert hasattr(main_window, "validation_status_label")
    assert main_window.validation_status_label.objectName() == "validationStatusLabel"


def test_run_action_has_object_name(main_window):
    """Run action must have a stable objectName."""
    assert hasattr(main_window, "run_action")
    assert main_window.run_action.objectName() == "actionRun"


def test_export_action_has_object_name(main_window):
    """Export action must have a stable objectName."""
    assert hasattr(main_window, "export_action")
    assert main_window.export_action.objectName() == "actionExportReport"


def test_export_archive_button_has_object_name(main_window):
    """Export Archive button must have a stable objectName."""
    assert hasattr(main_window, "btn_export_archive")
    assert main_window.btn_export_archive.objectName() == "btnExportArchive"
