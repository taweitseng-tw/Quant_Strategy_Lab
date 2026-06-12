"""Tests for active dataset selection and Run data-source clarity — Task 029A."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch
import pytest
import pandas as pd
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel

from app.ui.main_window import MainWindow
from app.workers import ImportWorker
from app.services.validation_pipeline_service import PipelineResult, run_validation_pipeline, PipelineConfig
from core.models.dataset import DatasetMeta
from core.models.strategy import Strategy, StrategyBlock, Condition
from data_engine.quality_checker import DataQualityReport
from reports import generate_markdown_report, generate_html_report
from backtest_engine.runner import run_backtest


def _sync_import_start(worker):
    """Patched ImportWorker.start that runs the worker synchronously."""
    worker.run()
    worker.finished.emit()


def _sync_validation_start(worker):
    """Patched ValidationWorker.start that runs the worker synchronously."""
    worker.run()
    worker.finished.emit()


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Initialize QApplication for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture(autouse=True)
def mock_ranked_strategies():
    """Mock get_ranked_strategies to prevent slow backtests during MainWindow init."""
    from unittest.mock import patch
    with patch("app.services.strategy_service.StrategyService.get_ranked_strategies", return_value=([], True)):
        yield


def test_pipeline_result_has_data_source():
    """Verify that PipelineResult contains the data_source field."""
    res = PipelineResult(data_source="Custom Data Source")
    assert res.data_source == "Custom Data Source"
    
    # Default should be empty string
    res_default = PipelineResult()
    assert res_default.data_source == ""


def test_run_validation_pipeline_stores_data_source():
    """Verify that run_validation_pipeline accepts and stores data_source."""
    rng = np.random.default_rng(42)
    times = pd.date_range("2024-01-02", periods=100, freq="1min")
    df = pd.DataFrame({
        "datetime": times,
        "open":  100.0 + rng.normal(0, 1, 100).cumsum(),
        "high":  102.0 + rng.normal(0, 1, 100).cumsum(),
        "low":   98.0 + rng.normal(0, 1, 100).cumsum(),
        "close": 101.0 + rng.normal(0, 1, 100).cumsum(),
        "volume": rng.integers(500, 5000, 100),
    })

    strategy = Strategy(
        name="test_run",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 5}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 5}, operator="<"),
        ], logic="AND"),
    )

    result = run_validation_pipeline(
        df, strategy,
        config=PipelineConfig(mc_iterations=5),
        data_source="Test Custom Source",
        commission=2.0,
    )

    assert result.data_source == "Test Custom Source"


def test_report_validation_evidence_includes_data_source():
    """Verify that Markdown and HTML reports include the data source when validation result is provided."""
    strategy = Strategy(
        name="test_strategy",
        long_entry=StrategyBlock(conditions=[], logic="AND"),
        long_exit=StrategyBlock(conditions=[], logic="AND"),
    )
    
    times = pd.date_range("2024-01-02", periods=10, freq="1min")
    df = pd.DataFrame({
        "datetime": times,
        "open":  [100.0] * 10,
        "high":  [101.0] * 10,
        "low":   [99.0] * 10,
        "close": [100.0] * 10,
        "volume": [1000] * 10,
    })
    
    backtest_res = run_backtest(
        strategy=strategy,
        df=df,
        initial_capital=100_000.0,
        commission=2.0,
        slippage_ticks=1.0,
        tick_size=0.1
    )
    
    validation_result = {
        "data_source": "Super Secret Dataset",
        "split_metadata": {"train_rows": 6, "validation_rows": 2, "oos_rows": 2},
        "baseline_metrics": {"total_pnl": 1500.0, "profit_factor": 1.5, "total_trades": 10},
        "stress_results": [],
        "monte_carlo_summary": None,
        "walk_forward_summary": None,
        "elimination_result": {"passed": True, "failed_rules": []}
    }
    
    # Check Markdown report
    md_content = generate_markdown_report(
        strategy=strategy,
        result=backtest_res,
        validation_result=validation_result
    )
    assert "Data Source" in md_content
    assert "Super Secret Dataset" in md_content
    
    # Check HTML report
    html_content = generate_html_report(
        strategy=strategy,
        result=backtest_res,
        validation_result=validation_result
    )
    assert "Data Source:" in html_content
    assert "Super Secret Dataset" in html_content


def test_main_window_mock_fallback_active_state(qapp):
    """Verify MainWindow behavior when no dataset is active (mock fallback)."""
    window = MainWindow()
    
    # Initial state
    assert window._loaded_dataset is None
    assert window._active_dataset_meta is None
    assert window._active_dataset_quality is None
    assert "None loaded" in window.data_status_label.text()
    
    # Run pipeline with no loaded dataset (should trigger mock fallback)
    from app.workers import ValidationWorker
    with patch.object(ValidationWorker, "start", _sync_validation_start):
        window._handle_run()
    
    assert window.latest_validation_result is not None
    assert window.latest_validation_result.data_source == "Mock fallback"
    
    # Validate dashboard source label should show "Mock fallback"
    # Find the Data Source card in validation_summary layout
    card_found = False
    for i in range(window.validation_summary._layout.count()):
        item = window.validation_summary._layout.itemAt(i)
        if item and item.widget():
            card = item.widget()
            title_lbl = card.findChild(QLabel)
            if title_lbl and title_lbl.text() == "Data Source":
                body_lbls = card.findChildren(QLabel)
                body_text = body_lbls[1].text() if len(body_lbls) > 1 else ""
                assert "Mock fallback" in body_text
                card_found = True
                break
    assert card_found, "Data Source card not found in validation summary dashboard"


def test_main_window_active_dataset_run(qapp):
    """Verify MainWindow behavior when a dataset is active."""
    window = MainWindow()
    
    # Manually populate active dataset (simulating import)
    dates = pd.date_range(start="2026-01-01", periods=100, freq="1min")
    dummy_df = pd.DataFrame({
        "datetime": dates,
        "open": np.random.rand(100) + 100.0,
        "high": np.random.rand(100) + 101.0,
        "low": np.random.rand(100) + 99.0,
        "close": np.random.rand(100) + 100.0,
        "volume": np.random.randint(100, 1000, 100)
    })
    
    dummy_meta = DatasetMeta(
        name="real_txf_test",
        symbol="TXF",
        timeframe="1min",
        row_count=100,
        start_datetime="2026-01-01 00:00:00",
        end_datetime="2026-01-01 01:40:00"
    )
    
    dummy_quality = DataQualityReport(
        passed=True,
        errors=[],
        warnings=[]
    )
    
    window._loaded_dataset = dummy_df
    window._active_dataset_meta = dummy_meta
    window._active_dataset_quality = dummy_quality
    
    # Simulate UI label update that happens in import
    window.data_status_label.setText(
        f"✓ Active Dataset: {dummy_meta.name} | Rows: {dummy_meta.row_count} | "
        f"Range: {dummy_meta.start_datetime} to {dummy_meta.end_datetime} | Quality: Passed"
    )
    
    # Run pipeline with active dataset
    from app.workers import ValidationWorker
    with patch.object(ValidationWorker, "start", _sync_validation_start):
        window._handle_run()
    
    assert window.latest_validation_result is not None
    assert window.latest_validation_result.data_source == "real_txf_test"
    
    # Validate dashboard source label should show "real_txf_test"
    card_found = False
    for i in range(window.validation_summary._layout.count()):
        item = window.validation_summary._layout.itemAt(i)
        if item and item.widget():
            card = item.widget()
            title_lbl = card.findChild(QLabel)
            if title_lbl and title_lbl.text() == "Data Source":
                body_lbls = card.findChildren(QLabel)
                body_text = body_lbls[1].text() if len(body_lbls) > 1 else ""
                assert "real_txf_test" in body_text
                card_found = True
                break
    assert card_found, "Data Source card not found in validation summary dashboard"


def test_html_report_escapes_malicious_string():
    """Verify that HTML report escapes malicious data_source strings like <script>alert(1)</script>."""
    strategy = Strategy(
        name="test_strategy",
        long_entry=StrategyBlock(conditions=[], logic="AND"),
        long_exit=StrategyBlock(conditions=[], logic="AND"),
    )
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-02", periods=10, freq="1min"),
        "open":  [100.0] * 10,
        "high":  [101.0] * 10,
        "low":   [99.0] * 10,
        "close": [100.0] * 10,
        "volume": [1000] * 10,
    })
    backtest_res = run_backtest(
        strategy=strategy,
        df=df,
        initial_capital=100_000.0,
        commission=2.0,
        slippage_ticks=1.0,
        tick_size=0.1
    )
    validation_result = {
        "data_source": "<script>alert(1)</script>",
        "split_metadata": {"train_rows": 6, "validation_rows": 2, "oos_rows": 2},
        "baseline_metrics": {"total_pnl": 1500.0, "profit_factor": 1.5, "total_trades": 10},
        "stress_results": [],
        "monte_carlo_summary": None,
        "walk_forward_summary": None,
        "elimination_result": {"passed": True, "failed_rules": []}
    }
    
    html_content = generate_html_report(
        strategy=strategy,
        result=backtest_res,
        validation_result=validation_result
    )
    assert "<script>alert(1)</script>" not in html_content
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_content


def test_report_export_works_without_validation():
    """Verify that report export works normally when no validation_result exists."""
    strategy = Strategy(
        name="test_strategy",
        long_entry=StrategyBlock(conditions=[], logic="AND"),
        long_exit=StrategyBlock(conditions=[], logic="AND"),
    )
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-02", periods=10, freq="1min"),
        "open":  [100.0] * 10,
        "high":  [101.0] * 10,
        "low":   [99.0] * 10,
        "close": [100.0] * 10,
        "volume": [1000] * 10,
    })
    backtest_res = run_backtest(
        strategy=strategy,
        df=df,
        initial_capital=100_000.0,
        commission=2.0,
        slippage_ticks=1.0,
        tick_size=0.1
    )
    
    md_content = generate_markdown_report(strategy, backtest_res, validation_result=None)
    assert "Validation Evidence" in md_content
    assert "No validation evidence was included in this report." in md_content
    
    html_content = generate_html_report(strategy, backtest_res, validation_result=None)
    assert "Validation Evidence" in html_content
    assert "No validation evidence was included in this report." in html_content


def test_report_export_works_validation_without_datasource():
    """Verify that report export works when validation_result has no data_source field."""
    strategy = Strategy(
        name="test_strategy",
        long_entry=StrategyBlock(conditions=[], logic="AND"),
        long_exit=StrategyBlock(conditions=[], logic="AND"),
    )
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-02", periods=10, freq="1min"),
        "open":  [100.0] * 10,
        "high":  [101.0] * 10,
        "low":   [99.0] * 10,
        "close": [100.0] * 10,
        "volume": [1000] * 10,
    })
    backtest_res = run_backtest(
        strategy=strategy,
        df=df,
        initial_capital=100_000.0,
        commission=2.0,
        slippage_ticks=1.0,
        tick_size=0.1
    )
    
    validation_result = {
        "split_metadata": {"train_rows": 6, "validation_rows": 2, "oos_rows": 2},
        "baseline_metrics": {"total_pnl": 1500.0, "profit_factor": 1.5, "total_trades": 10},
        "stress_results": [],
        "monte_carlo_summary": None,
        "walk_forward_summary": None,
        "elimination_result": {"passed": True, "failed_rules": []}
    }
    
    md_content = generate_markdown_report(strategy, backtest_res, validation_result=validation_result)
    assert "Data Source" not in md_content
    
    html_content = generate_html_report(strategy, backtest_res, validation_result=validation_result)
    assert "Data Source" not in html_content


def test_failed_import_clears_active_dataset(qapp):
    """Verify that failed imports clear any existing stale active dataset and reset labels."""
    window = MainWindow()
    
    # 1. First set active dataset state
    window._loaded_dataset = pd.DataFrame()
    window._active_dataset_meta = DatasetMeta(name="stale")
    window._active_dataset_quality = DataQualityReport(passed=True)
    window.data_status_label.setText("Active Dataset: stale")
    
    # 2. Trigger import (we mock getOpenFileName to return a file, but service throws)
    from unittest.mock import patch
    with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName", return_value=("dummy.csv", "All Files")):
        with patch("PySide6.QtWidgets.QMessageBox.critical") as mock_crit, \
             patch("app.workers.DataService.import_file", side_effect=ValueError("Mock import failure")), \
             patch.object(ImportWorker, "start", _sync_import_start):
            window._handle_import_ohlcv_data()
            
            # Assert stale state was reset to None
            assert window._loaded_dataset is None
            assert window._active_dataset_meta is None
            assert window._active_dataset_quality is None
            assert "None loaded" in window.data_status_label.text()
            mock_crit.assert_called_once()


def test_new_open_project_clears_active_dataset(qapp):
    """Verify that creating/opening a new/existing project resets any active dataset state."""
    window = MainWindow()
    
    # Set active dataset state
    window._loaded_dataset = pd.DataFrame()
    window._active_dataset_meta = DatasetMeta(name="to_clear")
    window._active_dataset_quality = DataQualityReport(passed=True)
    
    # Mock project_service to return a dummy project metadata
    from core.models.project import ProjectMeta
    from unittest.mock import MagicMock
    class MockProjectService:
        def __init__(self):
            self.repository = MagicMock()
        def create_project(self, *args, **kwargs):
            return ProjectMeta(name="dummy", root_path=Path("dummy_path"))
        def open_project(self, *args, **kwargs):
            return ProjectMeta(name="dummy", root_path=Path("dummy_path"))
        def is_project_active(self):
            return True
            
    window.project_service = MockProjectService()
    
    # Trigger New Project (mocking user inputs and dialogs)
    from unittest.mock import patch
    with patch("PySide6.QtWidgets.QInputDialog.getText", return_value=("new_proj", True)):
        with patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory", return_value="dummy_root"):
            with patch("PySide6.QtWidgets.QMessageBox.information"):
                window._handle_new_project()
                
                # Active dataset should be reset
                assert window._loaded_dataset is None
                assert window._active_dataset_meta is None
                assert window._active_dataset_quality is None
                assert "None loaded" in window.data_status_label.text()

    # Re-set active dataset state
    window._loaded_dataset = pd.DataFrame()
    window._active_dataset_meta = DatasetMeta(name="to_clear")
    window._active_dataset_quality = DataQualityReport(passed=True)

    # Trigger Open Project
    with patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory", return_value="dummy_root"):
        with patch("PySide6.QtWidgets.QMessageBox.information"):
            window._handle_open_project()
            
            # Active dataset should be reset
            assert window._loaded_dataset is None
            assert window._active_dataset_meta is None
            assert window._active_dataset_quality is None
            assert "None loaded" in window.data_status_label.text()


def test_quality_failed_active_dataset_aborts_run(qapp):
    """Verify that quality-failed active dataset blocks validation pipeline run with warning."""
    window = MainWindow()
    
    window._loaded_dataset = pd.DataFrame()
    window._active_dataset_meta = DatasetMeta(name="bad_data")
    window._active_dataset_quality = DataQualityReport(passed=False, errors=["high < low"])
    
    # Run validation pipeline
    from unittest.mock import patch
    with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
        window._handle_run()
        
        # Aborted, latest_validation_result remains None
        assert window.latest_validation_result is None
        mock_warn.assert_called_once()
        # ERROR message logged in panel
        assert "Validation pipeline aborted" in window.log_panel.output.toPlainText()


def test_validation_failure_handler_keeps_export_disabled(qapp):
    """Worker failure handler must preserve disabled export gating and log error."""
    window = MainWindow()

    window._on_validation_failure("synthetic failure")

    assert window.export_action.isEnabled() is False
    assert "Validation failed" in window.export_action.toolTip()
    assert "synthetic failure" in window.inspector_label.text()
    assert "Validation pipeline failed: synthetic failure" in window.log_panel.output.toPlainText()


def test_stale_run_guard_logs_warning(qapp):
    """Starting validation while a worker is running must log a warning."""
    window = MainWindow()
    from app.workers import ValidationWorker

    # Patch start so the worker never really runs — it stays "running".
    original_start = ValidationWorker.start

    def _noop_start(worker):
        pass  # worker never starts, never finishes

    with patch.object(ValidationWorker, "start", _noop_start):
        window._handle_run()
    # Now _validation_worker exists but isRunning() is False since start() was a no-op.
    # We need to simulate a running worker.  Patch isRunning instead.
    with patch.object(type(window._validation_worker), "isRunning", return_value=True):
        window._handle_run()
    # A warning must be logged.
    assert "already running" in window.log_panel.output.toPlainText().lower()


def test_stop_validation_requests_cancel_and_preserves_safe_ui_state(qapp):
    """Stop handler must request cancellation and keep export disabled."""
    window = MainWindow()
    sentinel_result = object()
    window.latest_validation_result = sentinel_result
    window._set_validation_running()

    class FakeWorker:
        def __init__(self):
            self.stopped = False

        def isRunning(self):
            return True

        def stop(self):
            self.stopped = True

    fake_worker = FakeWorker()
    window._validation_worker = fake_worker

    window._handle_stop_validation()

    assert fake_worker.stopped is True
    assert window.run_action.isEnabled() is False
    assert window.stop_action.isEnabled() is False
    assert window.export_action.isEnabled() is False
    assert window.latest_validation_result is sentinel_result
    assert window.validation_status_label.text() == "Cancelling..."
    assert "cancellation requested" in window.log_panel.output.toPlainText().lower()
