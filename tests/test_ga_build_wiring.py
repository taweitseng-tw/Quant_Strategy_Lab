"""Tests for GA Build page wiring — Tasks 031D / 031E.

Verifies that:
- GABuildPanel widget initializes and exposes the Run GA button.
- update_from_result populates the display correctly.
- GAWorker runs off-thread and emits success/failure signals.
- Double-click guard prevents concurrent GA runs.
- Quality-failed datasets abort before worker launch.
- No GA engine logic lives in widgets.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.models.dataset import DatasetMeta
from data_engine.quality_checker import DataQualityReport

# Skip entire module if display is unavailable (headless CI).
pytestmark = pytest.mark.skipif(
    sys.platform != "win32" and not os.environ.get("DISPLAY"),
    reason="Requires display or Windows",
)


def _make_df(n_bars: int = 150) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="1min")
    close = 100.0 + np.cumsum(rng.normal(0.01, 0.4, n_bars))
    close = np.maximum(close, 10.0)
    noise = rng.uniform(0.2, 1.0, n_bars)
    return pd.DataFrame({
        "datetime": times,
        "open":  close - noise * 0.3,
        "high":  close + noise,
        "low":   close - noise,
        "close": close,
        "volume": rng.integers(500, 5000, n_bars),
    })


# ---------------------------------------------------------------------------
# Widget-level tests (no MainWindow needed)
# ---------------------------------------------------------------------------


def test_ga_build_panel_init():
    """GABuildPanel must initialise with a Run GA button and status label."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.widgets.ga_build_panel import GABuildPanel
    panel = GABuildPanel()

    assert panel.btn_run_ga is not None
    assert panel.btn_run_ga.isEnabled()
    assert panel.status_label is not None
    assert "No search" in panel.status_label.text()


def test_ga_build_panel_update_from_result():
    """update_from_result must populate status and cards from a result object."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.widgets.ga_build_panel import GABuildPanel
    from core.models.strategy import Strategy, StrategyBlock, Condition

    panel = GABuildPanel()

    # Build a minimal result-like object matching GASearchResult fields.
    @dataclass
    class _MockResult:
        best_strategy: Strategy
        best_score: float
        generation_count: int
        final_population_size: int
        generation_best_scores: list = field(default_factory=list)
        generation_avg_scores: list = field(default_factory=list)
        config_snapshot: dict = field(default_factory=dict)

    strat = Strategy(
        name="test_ga_strat",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 15}, operator=">"),
        ]),
    )
    result = _MockResult(
        best_strategy=strat,
        best_score=0.4321,
        generation_count=3,
        final_population_size=8,
        generation_best_scores=[0.30, 0.38, 0.43],
        generation_avg_scores=[0.10, 0.15, 0.20],
    )

    panel.update_from_result(result, source_label="Mock fallback")

    # Status label should reflect completion.
    assert "0.4321" in panel.status_label.text()
    assert "✓" in panel.status_label.text()


def test_ga_build_panel_set_running_and_idle():
    """set_running disables button; set_idle re-enables it."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.widgets.ga_build_panel import GABuildPanel
    panel = GABuildPanel()

    panel.set_running()
    assert not panel.btn_run_ga.isEnabled()
    assert "Running" in panel.btn_run_ga.text()

    panel.set_idle()
    assert panel.btn_run_ga.isEnabled()
    assert "Run GA" in panel.btn_run_ga.text()


# ---------------------------------------------------------------------------
# GAWorker unit tests
# ---------------------------------------------------------------------------


def test_ga_worker_emits_success():
    """GAWorker must emit success signal with result and source_label."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.workers import GAWorker
    from app.services.ga_service import GASearchConfig, GASearchResult

    df = _make_df(150)
    cfg = GASearchConfig(population_size=4, max_generations=2, base_seed=7)

    received = {}

    def on_success(result, label):
        received["result"] = result
        received["label"] = label

    worker = GAWorker(df, cfg, "test_source")
    worker.success.connect(on_success)
    worker.start()
    worker.wait(10_000)  # 10s timeout for safety
    app.processEvents()  # flush queued cross-thread signals

    assert "result" in received
    assert isinstance(received["result"], GASearchResult)
    assert received["result"].generation_count == 2
    assert received["label"] == "test_source"


def test_ga_worker_emits_failure_on_bad_input():
    """GAWorker must emit failure signal when run_ga_search raises."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.workers import GAWorker
    from app.services.ga_service import GASearchConfig

    # Pass None as df — will cause a TypeError/AttributeError inside backtest.
    cfg = GASearchConfig(population_size=4, max_generations=2, base_seed=1)

    received = {}

    def on_failure(msg):
        received["error"] = msg

    def on_success(result, label):
        received["success"] = True

    worker = GAWorker(None, cfg, "bad_data")
    worker.failure.connect(on_failure)
    worker.success.connect(on_success)
    worker.start()
    worker.wait(10_000)
    app.processEvents()  # flush queued cross-thread signals

    assert "error" in received
    assert "success" not in received
    assert isinstance(received["error"], str)
    assert len(received["error"]) > 0


def test_ga_worker_finished_always_emitted():
    """finished signal must always fire regardless of success/failure."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.workers import GAWorker
    from app.services.ga_service import GASearchConfig

    df = _make_df(100)
    cfg = GASearchConfig(population_size=4, max_generations=2, base_seed=7)

    finished_calls = []

    worker = GAWorker(df, cfg, "test")
    worker.finished.connect(lambda: finished_calls.append(True))
    worker.start()
    worker.wait(10_000)
    app.processEvents()  # flush queued cross-thread signals

    assert len(finished_calls) == 1


def test_ga_worker_snapshots_dataframe_at_creation(monkeypatch):
    """Worker should not share a mutable DataFrame reference with the UI thread."""
    from app.workers import GAWorker
    from app.services.ga_service import GASearchConfig, GASearchResult
    from core.models.strategy import Strategy

    df = _make_df(20)
    original_open = float(df.loc[0, "open"])
    seen = {}

    def fake_run_ga_search(worker_df, *args, **kwargs):
        seen["same_object"] = worker_df is df
        seen["open"] = float(worker_df.loc[0, "open"])
        return GASearchResult(
            best_strategy=Strategy(name="snapshot_test"),
            best_score=0.0,
            generation_count=0,
            final_population_size=0,
        )

    monkeypatch.setattr("app.workers.run_ga_search", fake_run_ga_search)

    worker = GAWorker(df, GASearchConfig(population_size=4, max_generations=1), "snapshot")
    df.loc[0, "open"] = original_open + 9999.0
    worker.run()

    assert seen["same_object"] is False
    assert seen["open"] == original_open


# ---------------------------------------------------------------------------
# MainWindow integration tests
# ---------------------------------------------------------------------------


def test_ga_run_aborts_on_quality_failed_active_dataset(monkeypatch):
    """GA search must not run on an active dataset that failed quality checks."""
    from PySide6.QtWidgets import QApplication, QMessageBox

    app = QApplication.instance() or QApplication([])

    from app.ui.main_window import MainWindow

    window = MainWindow()
    window._loaded_dataset = _make_df(20)
    window._active_dataset_meta = DatasetMeta(name="bad_ga_data")
    window._active_dataset_quality = DataQualityReport(passed=False, errors=["high < low"])

    # Monkeypatch QMessageBox.warning to suppress dialog.
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.StandardButton.Ok)

    window._handle_run_ga()

    # Worker should not have been created.
    assert not hasattr(window, "_ga_worker") or window._ga_worker is None
    assert window.ga_build_panel.btn_run_ga.isEnabled()
    assert "failed quality checks" in window.ga_build_panel.status_label.text()
    assert "GA search aborted" in window.log_panel.output.toPlainText()


def test_ga_double_click_guard():
    """Second _handle_run_ga call while worker is running must be rejected."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from PySide6.QtCore import QThread

    from app.ui.main_window import MainWindow

    window = MainWindow()

    # Simulate a running worker by creating a mock that reports isRunning.
    class _FakeWorker:
        def isRunning(self):
            return True

    window._ga_worker = _FakeWorker()

    window._handle_run_ga()

    # Should log a warning and not start a new worker.
    assert "already running" in window.log_panel.output.toPlainText()
    # Original fake worker should still be in place (not replaced).
    assert isinstance(window._ga_worker, _FakeWorker)


# ---------------------------------------------------------------------------
# Service integration test (no GUI, just proves the service path works)
# ---------------------------------------------------------------------------


def test_ga_service_callable_from_service_layer():
    """run_ga_search must be callable and return a structured result."""
    from app.services.ga_service import GASearchConfig, GASearchResult, run_ga_search

    df = _make_df(150)
    cfg = GASearchConfig(population_size=4, max_generations=2, base_seed=7)
    result = run_ga_search(df, config=cfg)

    assert isinstance(result, GASearchResult)
    assert result.generation_count == 2
    assert result.final_population_size == 4


# ---------------------------------------------------------------------------
# Architecture boundary checks
# ---------------------------------------------------------------------------


def test_ga_build_panel_has_no_engine_imports():
    """Widget file must not import strategy_engine or backtest_engine."""
    source = Path("app/widgets/ga_build_panel.py").read_text(encoding="utf-8")
    assert "strategy_engine" not in source
    assert "backtest_engine" not in source
    assert "validation_engine" not in source


def test_ga_build_panel_has_no_service_imports():
    """Widget file must not import app.services (service calls belong in main_window)."""
    source = Path("app/widgets/ga_build_panel.py").read_text(encoding="utf-8")
    assert "app.services" not in source
    assert "run_ga_search" not in source


def test_ga_worker_has_no_engine_internals():
    """Worker delegates to service layer — must not import GA engine directly."""
    source = Path("app/workers/__init__.py").read_text(encoding="utf-8")
    assert "strategy_engine.ga " not in source
    assert "strategy_engine.ga_fitness" not in source


# ---------------------------------------------------------------------------
# Task 050B: MTF UI Wiring Tests
# ---------------------------------------------------------------------------


def test_ga_build_panel_get_mtf_config_dict():
    """GABuildPanel.get_mtf_config_dict must return safe primitive defaults."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.widgets.ga_build_panel import GABuildPanel
    panel = GABuildPanel()
    
    # By default, checkbox is off
    cfg = panel.get_mtf_config_dict()
    assert cfg["allowed_timeframes"] == []
    assert cfg["mtf_probability"] == 0.0

    # Turn it on
    panel.chk_enable_mtf.setChecked(True)
    panel.le_allowed_timeframes.setText("15, 60")
    panel.spin_mtf_probability.setValue(0.3)
    
    cfg2 = panel.get_mtf_config_dict()
    assert cfg2["allowed_timeframes"] == [15, 60]
    assert cfg2["mtf_probability"] == 0.3


def test_ga_run_reads_mtf_config(monkeypatch):
    """MainWindow._handle_run_ga must read from ga_build_panel and forward to GASearchConfig."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.ui.main_window import MainWindow
    window = MainWindow()
    window._loaded_dataset = _make_df(20)
    
    seen_cfg = {}
    
    class FakeWorker:
        def __init__(self, df, cfg, source_label, instrument=None, parent=None, commission=2.0):
            seen_cfg["allowed_timeframes"] = cfg.allowed_timeframes
            seen_cfg["mtf_probability"] = cfg.mtf_probability
            self.success = type("MockSignal", (), {"connect": lambda self, x: None})()
            self.failure = type("MockSignal", (), {"connect": lambda self, x: None})()
            self.finished = type("MockSignal", (), {"connect": lambda self, x: None})()
        
        def start(self):
            pass

    monkeypatch.setattr("app.workers.GAWorker", FakeWorker)
    
    # Configure MTF
    window.ga_build_panel.chk_enable_mtf.setChecked(True)
    window.ga_build_panel.le_allowed_timeframes.setText("5,15")
    window.ga_build_panel.spin_mtf_probability.setValue(0.2)
    
    window._handle_run_ga()
    
    assert seen_cfg["allowed_timeframes"] == (5, 15)
    assert seen_cfg["mtf_probability"] == 0.2


def test_ga_build_panel_invalid_mtf_input():
    """GABuildPanel.get_mtf_config_dict must fail-safe on invalid input."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.widgets.ga_build_panel import GABuildPanel
    panel = GABuildPanel()
    
    panel.chk_enable_mtf.setChecked(True)
    panel.spin_mtf_probability.setValue(0.3)
    
    # Invalid tokens should cause fail-safe (enabled=False, allowed_timeframes=[])
    panel.le_allowed_timeframes.setText("15, abc, -5")
    cfg = panel.get_mtf_config_dict()
    assert cfg["enabled"] is False
    assert cfg["allowed_timeframes"] == []
    assert cfg["mtf_probability"] == 0.0

    # Negative tokens should cause fail-safe
    panel.le_allowed_timeframes.setText("5, -15")
    cfg = panel.get_mtf_config_dict()
    assert cfg["enabled"] is False
    assert cfg["allowed_timeframes"] == []

    # Float tokens should cause fail-safe
    panel.le_allowed_timeframes.setText("15, 3.14")
    cfg = panel.get_mtf_config_dict()
    assert cfg["enabled"] is False
    assert cfg["allowed_timeframes"] == []
