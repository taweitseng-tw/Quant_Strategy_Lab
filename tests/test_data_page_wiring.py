"""Tests for DataService and CandlestickChart — Task 012 / Task 019A."""

from __future__ import annotations

import sys
import tempfile
import shutil
from contextlib import contextmanager
from pathlib import Path
import pandas as pd
import numpy as np
import pytest
from PySide6.QtWidgets import QApplication
from unittest.mock import patch

from app.ui.main_window import MainWindow
from app.services.data_service import DataService
from data_engine.quality_checker import DataQualityReport
from app.widgets.candlestick_chart import CandlestickChart, PYQTGRAPH_AVAILABLE


def _write_valid_ohlcv_csv(path: Path) -> None:
    """Write a minimal valid OHLCV CSV with 1 bar.  The filename becomes the
    dataset name visible in the status label."""
    pd.DataFrame({
        "Date": ["2026/01/01"], "Time": ["09:00"], "Open": [100.0],
        "High": [101.0], "Low": [99.0], "Close": [100.5], "TotalVolume": [1000],
    }).to_csv(path, index=False)


@contextmanager
def _patch_file_dialog(path: str):
    """Context manager that patches QFileDialog.getOpenFileName to return *path*."""
    with patch(
        "PySide6.QtWidgets.QFileDialog.getOpenFileName",
        return_value=(path, ""),
    ):
        yield


@contextmanager
def _patch_import_success(path: str):
    """Context manager patching file dialog + info/critical message boxes for a successful import."""
    with (
        patch("PySide6.QtWidgets.QFileDialog.getOpenFileName", return_value=(str(path), "")),
        patch("PySide6.QtWidgets.QMessageBox.information"),
        patch("PySide6.QtWidgets.QMessageBox.critical"),
    ):
        yield


@contextmanager
def _patch_import_failure(path: str):
    """Context manager patching file dialog + critical message box for a failed import."""
    with (
        patch("PySide6.QtWidgets.QFileDialog.getOpenFileName", return_value=(str(path), "")),
        patch("PySide6.QtWidgets.QMessageBox.critical"),
    ):
        yield


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Fixture to initialize a QApplication instance for GUI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def tmp_dir() -> Path:
    """Fixture to create a temporary working directory and clean it up."""
    base = Path(tempfile.mkdtemp())
    yield base
    shutil.rmtree(base, ignore_errors=True)


@pytest.fixture
def sample_ohlcv_file(tmp_dir) -> Path:
    """Fixture to generate a standard OHLCV CSV file for parsing tests."""
    file_path = tmp_dir / "sample_data.csv"
    df = pd.DataFrame({
        "Date": ["2026/01/01", "2026/01/02", "2026/01/03"],
        "Time": ["09:00:00", "09:00:00", "09:00:00"],
        "Open": [100.0, 101.0, 102.0],
        "High": [105.0, 106.0, 107.0],
        "Low": [95.0, 96.0, 97.0],
        "Close": [101.0, 102.0, 103.0],
        "TotalVolume": [1000, 1100, 1200]
    })
    df.to_csv(file_path, index=False)
    return file_path


# ---------------------------------------------------------------------------
# DataService Tests
# ---------------------------------------------------------------------------

def test_data_service_import_file_with_temp_fallback(sample_ohlcv_file) -> None:
    """Verify that DataService imports standard OHLCV CSV files using temp folders when no project exists."""
    service = DataService(project_path=None)
    assert service.project_path is None
    
    # Import
    normalized_df, meta, quality = service.import_file(sample_ohlcv_file, symbol="TEST_SYM", timeframe="5min")
    
    assert len(normalized_df) == 3
    assert list(normalized_df.columns) == ["datetime", "open", "high", "low", "close", "volume"]
    assert meta.symbol == "TEST_SYM"
    assert meta.timeframe == "5min"
    assert meta.row_count == 3
    assert quality.passed  # clean data should pass
    
    # Output path should be inside the system temp directory
    normalized_path = Path(meta.normalized_path)
    assert normalized_path.is_file()
    assert "qsl_temp_project" in str(normalized_path)


def test_data_service_import_file_with_project_path(sample_ohlcv_file, tmp_dir) -> None:
    """Verify that DataService imports and writes to the correct project raw data directory when project_path is set."""
    service = DataService(project_path=tmp_dir)
    assert service.project_path == tmp_dir
    
    # Import
    normalized_df, meta, quality = service.import_file(sample_ohlcv_file, symbol="PROJ_SYM")
    
    assert len(normalized_df) == 3
    assert meta.symbol == "PROJ_SYM"
    
    # Output path should be inside active project structure
    expected_path = tmp_dir / "data" / "raw" / "sample_data_normalized.csv"
    assert expected_path.is_file()
    assert str(expected_path) == meta.normalized_path


def test_data_service_get_render_subset() -> None:
    """Verify get_render_subset correctly slices large DataFrames."""
    dates = pd.date_range(start="2026-01-01", periods=3000, freq="min")
    df = pd.DataFrame({
        "datetime": dates,
        "open": np.random.rand(3000),
        "high": np.random.rand(3000),
        "low": np.random.rand(3000),
        "close": np.random.rand(3000),
        "volume": np.random.rand(3000)
    })
    
    # Case 1: exceeding threshold
    subset = DataService.get_render_subset(df, max_rows=1000)
    assert len(subset) == 1000
    pd.testing.assert_frame_equal(subset, df.tail(1000))
    
    # Case 2: below threshold
    subset_small = DataService.get_render_subset(df, max_rows=5000)
    assert len(subset_small) == 3000
    pd.testing.assert_frame_equal(subset_small, df)


# ---------------------------------------------------------------------------
# Data quality integration — Task 019A
# ---------------------------------------------------------------------------


def test_clean_import_returns_passed_quality_report(sample_ohlcv_file):
    """Clean OHLCV data must produce a passed quality report."""
    service = DataService()
    _, _, quality = service.import_file(sample_ohlcv_file, symbol="TEST")
    assert quality.passed
    assert quality.errors == []


def test_txf_sample_returns_passed_quality_report():
    """The TXF sample fixture must produce a passed quality report."""
    txf_path = Path(__file__).resolve().parent.parent / "sample_data" / "sample_txf.csv"
    service = DataService()
    _, _, quality = service.import_file(txf_path, symbol="TXF", timeframe="1min")
    assert quality.passed
    assert quality.errors == []


def test_bad_ohlc_data_produces_failed_quality_report(tmp_dir):
    """Data with high < low must fail quality check but still return the DataFrame."""
    bad_path = tmp_dir / "bad_ohlc.csv"
    pd.DataFrame({
        "Date": ["2024/01/02", "2024/01/02"],
        "Time": ["08:30:00", "08:31:00"],
        "Open": [100.0, 101.0],
        "High": [95.0, 96.0],   # high < open → invalid
        "Low": [99.0, 100.0],
        "Close": [98.0, 99.0],
        "TotalVolume": [1000, 1100],
    }).to_csv(bad_path, index=False)

    service = DataService()
    df, meta, quality = service.import_file(bad_path, symbol="BAD", timeframe="1min")

    assert not quality.passed
    assert any("high < low" in e for e in quality.errors)
    # Data is still returned — caller decides what to do.
    assert len(df) == 2


# ---------------------------------------------------------------------------
# Format Guidance and Actionable Error Tests — Task 065A
# ---------------------------------------------------------------------------


def test_get_expected_format_guide_returns_ohlcv_columns():
    """The format guide must mention the required OHLCV columns.
    The first line (used as UI label) must start with 'Columns:'."""
    guide = DataService.get_expected_format_guide()
    assert guide.startswith("Columns:")
    assert "Date" in guide
    assert "Time" in guide
    assert "Open" in guide
    assert "High" in guide
    assert "Low" in guide
    assert "Close" in guide
    assert "TotalVolume" in guide
    assert "Example" in guide


def test_get_actionable_import_error_file_not_found():
    """FileNotFoundError must produce an actionable message mentioning the file."""
    exc = FileNotFoundError("/path/to/missing.csv")
    msg = DataService.get_actionable_import_error(exc)
    assert "File not found" in msg
    assert "/path/to/missing.csv" in msg
    assert "check that the file exists" in msg.lower()


def test_get_actionable_import_error_no_data_rows():
    """Empty-data error must produce a message about empty file."""
    exc = ValueError("CSV file contains no data rows.")
    msg = DataService.get_actionable_import_error(exc)
    assert "empty" in msg.lower() or "no data rows" in msg.lower()


def test_get_actionable_import_error_parsing():
    """Parsing failures must mention expected format."""
    exc = RuntimeError("Failed to read CSV: Expected 7 columns, got 3")
    msg = DataService.get_actionable_import_error(exc)
    assert "CSV" in msg or "parsing" in msg.lower()
    assert "Date" in msg or "Open" in msg


def test_get_actionable_import_error_missing_columns():
    """Missing column errors must list required columns."""
    exc = KeyError("Missing column: TotalVolume")
    msg = DataService.get_actionable_import_error(exc)
    assert "Missing" in msg or "column" in msg.lower()
    assert "TotalVolume" in msg


def test_get_actionable_import_error_fallback():
    """Unknown exceptions must still produce a helpful fallback message."""
    exc = RuntimeError("Unexpected disk error")
    msg = DataService.get_actionable_import_error(exc)
    assert "Import failed" in msg
    assert "import failed" in msg.lower()
    assert "ohlcv" in msg.lower()


def test_import_file_failure_produces_actionable_message(tmp_dir):
    """When import_file raises on a nonexistent file, the converted error is
    actionable — proves the exception→actionable pipeline end-to-end."""
    service = DataService()
    missing = tmp_dir / "nonexistent.csv"
    with pytest.raises(Exception) as exc_info:
        service.import_file(missing, symbol="TEST")
    msg = DataService.get_actionable_import_error(exc_info.value)
    assert "File not found" in msg
    assert "check that the file exists" in msg.lower()
    assert str(missing.resolve()) in msg


def test_import_handler_failure_dialog_uses_actionable_message(qapp, tmp_dir):
    """The Data page import handler must show the actionable import error."""
    window = MainWindow()
    missing = tmp_dir / "nonexistent.csv"
    expected_message = DataService.get_actionable_import_error(
        FileNotFoundError(f"Source file not found: {missing.resolve()}")
    )
    captured = {}

    def capture_critical(parent, title, message):
        captured["title"] = title
        captured["message"] = message

    try:
        with (
            patch(
                "PySide6.QtWidgets.QFileDialog.getOpenFileName",
                return_value=(str(missing), ""),
            ),
            patch("PySide6.QtWidgets.QMessageBox.critical", side_effect=capture_critical),
        ):
            window._handle_import_ohlcv_data()
    finally:
        window.close()

    assert captured["title"] == "Import Failed"
    assert captured["message"] == expected_message
    assert "File not found" in captured["message"]
    assert "check that the file exists" in captured["message"].lower()
    assert "An error occurred while importing" not in captured["message"]


# ---------------------------------------------------------------------------
# CandlestickChart Slicing Guardrail Tests
# ---------------------------------------------------------------------------

def test_candlestick_chart_slicing_guardrail(qapp) -> None:
    """Verify that CandlestickChart set_data automatically slices large DataFrames for UI responsiveness."""
    chart = CandlestickChart()
    
    dates = pd.date_range(start="2026-01-01", periods=2500, freq="min")
    large_df = pd.DataFrame({
        "datetime": dates,
        "open": np.random.rand(2500),
        "high": np.random.rand(2500),
        "low": np.random.rand(2500),
        "close": np.random.rand(2500),
        "volume": np.random.rand(2500)
    })
    
    # Load into chart
    chart.set_data(large_df, is_mock=False)
    
    if PYQTGRAPH_AVAILABLE:
        # Internal candlestick item should hold only the most recent 2000 rows
        rendered_df = chart.candlestick_item._df
        assert rendered_df is not None
        assert len(rendered_df) == 2000
        
        # Check it is the tail
        pd.testing.assert_frame_equal(rendered_df, large_df.tail(2000))
        
        # Title should mention performance details
        title = chart.plot_widget.plotItem.titleLabel.text
        assert "Displaying most recent 2,000" in title
        assert "2,500 rows" in title


# ---------------------------------------------------------------------------
# Import button busy guard (Task 080A-080F)
# ---------------------------------------------------------------------------


def test_import_button_disabled_during_import(qapp, tmp_dir):
    """Import button must be disabled before the data service call is made."""
    window = MainWindow()
    captured = {}
    original_import_file = DataService.import_file

    def _side_effect(*args, **kwargs):
        captured["enabled"] = window.btn_import_data.isEnabled()
        captured["text"] = window.btn_import_data.text()
        return original_import_file(DataService(), *args, **kwargs)

    csv_file = tmp_dir / "sample_ok.csv"
    _write_valid_ohlcv_csv(csv_file)

    try:
        with (
            patch(
                "PySide6.QtWidgets.QFileDialog.getOpenFileName",
                return_value=(str(csv_file), ""),
            ),
            patch(
                "app.ui.main_window.DataService.import_file",
                side_effect=_side_effect,
            ),
            patch("PySide6.QtWidgets.QMessageBox.information"),
            patch("PySide6.QtWidgets.QMessageBox.critical") as mock_critical,
        ):
            window._handle_import_ohlcv_data()
    finally:
        window.close()

    assert captured.get("enabled") is False, "Import button must be disabled when importing"
    assert "Importing" in captured.get("text", ""), "Button text should change to 'Importing...'"
    mock_critical.assert_not_called()


def test_import_success_resets_validation_state(qapp, tmp_dir):
    """After successful import, validation state must be cleared even if prior validation existed."""
    from app.services.validation_pipeline_service import PipelineResult

    window = MainWindow()
    csv_file = tmp_dir / "sample_ok.csv"
    _write_valid_ohlcv_csv(csv_file)

    stale_dataset = pd.DataFrame({"Close": [1.0]})
    stale_meta = object()
    stale_quality = object()
    window._loaded_dataset = stale_dataset
    window._active_dataset_meta = stale_meta
    window._active_dataset_quality = stale_quality

    # Simulate prior successful validation state.
    window.latest_validation_result = PipelineResult(
        baseline_metrics={"total_pnl": 100},
        elimination_result={"passed": True},
    )
    window.export_action.setEnabled(True)
    window.export_action.setToolTip("Export the latest validation report.")
    window.validation_status_label.setText("Validation completed.")
    window.validation_status_label.show()

    try:
        with _patch_import_success(csv_file):
            window._handle_import_ohlcv_data()
    finally:
        window.close()

    # Button restored.
    assert window.btn_import_data.isEnabled(), "Import button must be enabled after success"
    assert window.btn_import_data.text() == "Import OHLCV Data File"

    # Dataset state replaced (not None — import succeeded).
    assert window._loaded_dataset is not None, "Loaded dataset must be set after success"
    assert window._active_dataset_meta is not None, "Active dataset meta must be set"
    assert window._active_dataset_quality is not None, "Active dataset quality must be set"
    assert window._loaded_dataset is not stale_dataset
    assert window._active_dataset_meta is not stale_meta
    assert window._active_dataset_quality is not stale_quality

    # Validation state reset (via _reset_validation_state).
    assert window.latest_validation_result is None, "Validation result must be cleared"
    assert not window.export_action.isEnabled(), "Export must be disabled after new import"
    assert "run validation" in window.export_action.toolTip().lower(), (
        "Export tooltip must explain why disabled"
    )
    assert window.validation_status_label.isHidden(), "Status label must be hidden"
    assert window.validation_status_label.text() == "", "Status text must be empty"


def test_import_failure_clears_all_state(qapp, tmp_dir):
    """After import failure, button, dataset state, and validation state must all reset."""
    from app.services.validation_pipeline_service import PipelineResult

    window = MainWindow()
    missing = tmp_dir / "nonexistent.csv"

    # Simulate prior loaded dataset state.
    window._loaded_dataset = pd.DataFrame({"close": [100.0]})
    window._active_dataset_meta = object()
    window._active_dataset_quality = object()

    # Simulate prior successful validation state.
    window.latest_validation_result = PipelineResult(
        baseline_metrics={"total_pnl": 100},
        elimination_result={"passed": True},
    )
    window.validation_status_label.setText("Validation completed.")
    window.validation_status_label.show()
    window.export_action.setEnabled(True)
    window.export_action.setToolTip("Export the latest validation report.")

    try:
        with _patch_import_failure(missing):
            window._handle_import_ohlcv_data()
    finally:
        window.close()

    # Button state
    assert window.btn_import_data.isEnabled(), "Import button must be re-enabled after failure"
    assert window.btn_import_data.text() == "Import OHLCV Data File"

    # Dataset state cleared
    assert window._loaded_dataset is None, "Loaded dataset must be cleared after failure"
    assert window._active_dataset_meta is None, "Active dataset meta must be cleared"
    assert window._active_dataset_quality is None, "Active dataset quality must be cleared"

    # Validation state reset (via _reset_validation_state)
    assert window.latest_validation_result is None, "Validation result must be cleared"
    assert not window.export_action.isEnabled(), "Export must be disabled after failure"
    assert "run validation" in window.export_action.toolTip().lower(), (
        "Export tooltip should explain disabled state"
    )
    assert window.validation_status_label.isHidden(), "Status label must be hidden after failure"
    assert window.validation_status_label.text() == ""


# ---------------------------------------------------------------------------
# Data page stable objectName values (Task 081A-081F)
# ---------------------------------------------------------------------------


def test_import_button_has_object_name(qapp):
    """Import button must have a stable objectName."""
    window = MainWindow()
    try:
        assert window.btn_import_data.objectName() == "btnImportData"
    finally:
        window.close()


def test_data_status_label_has_object_name(qapp):
    """Data status label must have a stable objectName."""
    window = MainWindow()
    try:
        assert window.data_status_label.objectName() == "dataStatusLabel"
    finally:
        window.close()


def test_data_format_guide_label_has_object_name(qapp):
    """Data format guide label must have a stable objectName."""
    window = MainWindow()
    try:
        assert window.data_format_guide_label.objectName() == "dataFormatGuideLabel"
    finally:
        window.close()


# ---------------------------------------------------------------------------
# Import cancel state preservation (Task 083A-083F)
# ---------------------------------------------------------------------------


def test_import_cancel_preserves_existing_state(qapp):
    """Canceling the file dialog must not mutate any existing data/validation/export state."""
    from app.services.validation_pipeline_service import PipelineResult

    window = MainWindow()

    # Simulate prior successful state.
    window._loaded_dataset = "preloaded"
    window._active_dataset_meta = {"name": "test"}
    window._active_dataset_quality = {"passed": True}
    window.latest_validation_result = PipelineResult(
        baseline_metrics={"total_pnl": 100},
        elimination_result={"passed": True},
    )
    window.export_action.setEnabled(True)
    window.export_action.setToolTip("Export the latest validation report.")
    window.validation_status_label.setText("Validation completed.")
    window.validation_status_label.show()

    # Snapshot all state before cancel.
    snap_dataset = window._loaded_dataset
    snap_meta = window._active_dataset_meta
    snap_quality = window._active_dataset_quality
    snap_result = window.latest_validation_result
    snap_export_enabled = window.export_action.isEnabled()
    snap_export_tip = window.export_action.toolTip()
    snap_status_text = window.validation_status_label.text()
    snap_status_visible = not window.validation_status_label.isHidden()

    # Cancel the import dialog.
    with (
        patch(
            "PySide6.QtWidgets.QFileDialog.getOpenFileName",
            return_value=("", ""),
        ),
        patch("app.ui.main_window.DataService.import_file") as mock_import,
    ):
        window._handle_import_ohlcv_data()

    # Nothing changed.
    assert window._loaded_dataset is snap_dataset
    assert window._active_dataset_meta is snap_meta
    assert window._active_dataset_quality is snap_quality
    assert window.latest_validation_result is snap_result
    assert window.export_action.isEnabled() is snap_export_enabled
    assert window.export_action.toolTip() == snap_export_tip
    assert window.validation_status_label.text() == snap_status_text
    assert (not window.validation_status_label.isHidden()) is snap_status_visible
    mock_import.assert_not_called()
    window.close()


# ---------------------------------------------------------------------------
# Data status label transition tests (Task 085A-085F)
# ---------------------------------------------------------------------------


def test_data_status_label_after_successful_import(qapp, tmp_dir):
    """After successful import, status label must show dataset name and rows."""
    window = MainWindow()
    csv_file = tmp_dir / "sample_label.csv"
    _write_valid_ohlcv_csv(csv_file)

    try:
        with _patch_import_success(csv_file):
            window._handle_import_ohlcv_data()

        text = window.data_status_label.text()
        assert "Active Dataset" in text, f"Label should say Active Dataset, got: {text!r}"
        assert "Rows:" in text or "Rows" in text, f"Label should show row count, got: {text!r}"
        assert "sample_label" in text, f"Label should mention imported dataset, got: {text!r}"
        assert "None loaded" not in text, f"Label should not say None loaded, got: {text!r}"
    finally:
        window.close()


def test_data_status_label_after_import_failure(qapp, tmp_dir):
    """After import failure, status label must return to mock/no-data wording."""
    window = MainWindow()
    missing = tmp_dir / "nonexistent.csv"

    try:
        with _patch_import_failure(missing):
            window._handle_import_ohlcv_data()

        text = window.data_status_label.text()
        assert "None loaded" in text, f"Label should say None loaded, got: {text!r}"
        assert "mock" in text.lower(), f"Label should mention mock data, got: {text!r}"
    finally:
        window.close()


def test_data_status_label_preserved_on_cancel(qapp):
    """After canceling import dialog, status label must not change."""
    window = MainWindow()
    original_text = window.data_status_label.text()

    with _patch_file_dialog(""):
        window._handle_import_ohlcv_data()

    try:
        assert window.data_status_label.text() == original_text, (
            f"Label must not change on cancel, got: {window.data_status_label.text()!r}"
        )
    finally:
        window.close()


# ---------------------------------------------------------------------------
# Import button tooltip state tests (Task 087A-087F)
# ---------------------------------------------------------------------------


def test_import_button_has_default_tooltip(qapp):
    """Import button must have a default tooltip explaining CSV selection."""
    window = MainWindow()
    try:
        tip = window.btn_import_data.toolTip()
        assert tip, "Tooltip must not be empty"
        assert "csv" in tip.lower() or "file" in tip.lower(), (
            f"Tooltip should mention CSV/file, got: {tip!r}"
        )
    finally:
        window.close()


def test_import_button_tooltip_during_import(qapp, tmp_dir):
    """Import button tooltip must change to 'Importing...' while import runs."""
    window = MainWindow()
    captured = {}
    original_import_file = DataService.import_file

    def _side_effect(*args, **kwargs):
        captured["tooltip"] = window.btn_import_data.toolTip()
        return original_import_file(DataService(), *args, **kwargs)

    csv_file = tmp_dir / "sample_ok.csv"
    _write_valid_ohlcv_csv(csv_file)

    with (
        patch(
            "PySide6.QtWidgets.QFileDialog.getOpenFileName",
            return_value=(str(csv_file), ""),
        ),
        patch(
            "app.ui.main_window.DataService.import_file",
            side_effect=_side_effect,
        ),
        patch("PySide6.QtWidgets.QMessageBox.information"),
        patch("PySide6.QtWidgets.QMessageBox.critical") as mock_critical,
    ):
        window._handle_import_ohlcv_data()

    try:
        assert captured.get("tooltip", ""), "Tooltip must be set during import"
        assert "import" in captured["tooltip"].lower(), (
            f"Tooltip during import should mention importing, got: {captured['tooltip']!r}"
        )
        mock_critical.assert_not_called()
    finally:
        window.close()


def test_import_button_tooltip_restored_after_success(qapp, tmp_dir):
    """Import button tooltip must be restored after successful import."""
    window = MainWindow()
    csv_file = tmp_dir / "sample_ok.csv"
    _write_valid_ohlcv_csv(csv_file)

    with _patch_import_success(csv_file):
        window._handle_import_ohlcv_data()

    try:
        tip = window.btn_import_data.toolTip()
        assert tip, "Tooltip must not be empty after success"
        assert "csv" in tip.lower() or "file" in tip.lower(), (
            f"Tooltip should mention CSV/file after success, got: {tip!r}"
        )
    finally:
        window.close()


def test_import_button_tooltip_restored_after_failure(qapp, tmp_dir):
    """Import button tooltip must be restored after import failure."""
    window = MainWindow()
    missing = tmp_dir / "nonexistent.csv"

    with _patch_import_failure(missing):
        window._handle_import_ohlcv_data()

    try:
        tip = window.btn_import_data.toolTip()
        assert tip, "Tooltip must not be empty after failure"
        assert "csv" in tip.lower() or "file" in tip.lower(), (
            f"Tooltip should mention CSV/file after failure, got: {tip!r}"
        )
    finally:
        window.close()


def test_import_button_tooltip_restored_after_cancel(qapp):
    """Import button tooltip must stay at the default after cancel."""
    window = MainWindow()
    original_tip = window.btn_import_data.toolTip()

    with _patch_file_dialog(""):
        window._handle_import_ohlcv_data()

    try:
        assert window.btn_import_data.toolTip() == original_tip
    finally:
        window.close()


# ---------------------------------------------------------------------------
# Data quality evidence surface tests (Task 105A-105C)
# ---------------------------------------------------------------------------


class TestFormatQualityEvidence:
    """Unit tests for DataService.format_quality_evidence()."""

    def test_clean_quality(self):
        """Clean report must show 'Passed' with no issues."""
        report = DataQualityReport(passed=True)
        text = DataService.format_quality_evidence(report)
        assert "Passed" in text
        assert "error" not in text.lower()
        assert "warning" not in text.lower()

    def test_quality_with_warnings(self):
        """Report with warnings must list them."""
        report = DataQualityReport(
            passed=True,
            warnings=["Found 3 time gap(s) > 2 min", "Found 2 large jumps"],
        )
        text = DataService.format_quality_evidence(report)
        assert "Passed" in text
        assert "warning" in text.lower()
        assert "time gap" in text
        assert "large jump" in text

    def test_quality_with_errors(self):
        """Failed report must list errors."""
        report = DataQualityReport(
            passed=False,
            errors=["Found 5 row(s) where high < low", "Column 'volume' has 2 null value(s)"],
        )
        text = DataService.format_quality_evidence(report)
        assert "Failed" in text
        assert "error" in text.lower()
        assert "high < low" in text

    def test_quality_with_both(self):
        """Failed report with both errors and warnings must show both."""
        report = DataQualityReport(
            passed=False,
            errors=["Column 'volume' has nulls"],
            warnings=["Found 3 time gap(s)"],
        )
        text = DataService.format_quality_evidence(report)
        assert "Failed" in text
        assert "error" in text.lower()
        assert "warning" in text.lower()
        assert "nulls" in text
        assert "time gap" in text

    def test_quality_with_many_issues_truncated(self):
        """More than 3 errors/warnings must show count of remaining."""
        report = DataQualityReport(
            passed=False,
            errors=[f"Error {i}" for i in range(5)],
            warnings=[f"Warning {i}" for i in range(5)],
        )
        text = DataService.format_quality_evidence(report)
        assert "2 more" in text  # truncation indicator
        assert "and 2 more" in text


# ---------------------------------------------------------------------------
# Integration: quality tooltip on data status label after import
# ---------------------------------------------------------------------------


def test_quality_tooltip_on_clean_import(qapp, tmp_dir):
    """After clean import, status label tooltip must show quality passed."""
    window = MainWindow()
    csv_file = tmp_dir / "sample_clean.csv"
    _write_valid_ohlcv_csv(csv_file)

    with _patch_import_success(csv_file):
        window._handle_import_ohlcv_data()

    try:
        tip = window.data_status_label.toolTip()
        assert tip, "Tooltip must contain quality evidence on successful import"
        assert "Passed" in tip
        assert "Quality" in tip
    finally:
        window.close()


def test_quality_tooltip_on_warning_import(qapp, tmp_dir):
    """After import with warnings, tooltip must mention warnings."""
    window = MainWindow()
    csv_file = tmp_dir / "sample_gappy.csv"
    # Write a CSV with a time gap to trigger a warning.
    pd.DataFrame({
        "Date": ["2026/01/01", "2026/01/02"],
        "Time": ["09:00", "09:00"],
        "Open": [100.0, 101.0],
        "High": [101.0, 102.0],
        "Low": [99.0, 100.0],
        "Close": [100.5, 101.5],
        "TotalVolume": [1000, 1100],
    }).to_csv(csv_file, index=False)

    with _patch_import_success(csv_file):
        window._handle_import_ohlcv_data()

    try:
        tip = window.data_status_label.toolTip()
        # With default check_quality(..., outlier_pct_threshold=5.0), the
        # second bar's 1% close change is within threshold, but the gap
        # between two bars on different dates with expected 1min frequency
        # will trigger a time gap warning.
        assert tip, "Tooltip must exist"
        assert "Passed" in tip
        assert "warning" in tip.lower()
        assert "time gap" in tip.lower()
    finally:
        window.close()
