"""Tests for GP Build page wiring — Task 031F.

Verifies that:
- GABuildPanel widget exposes the Run GP button.
- GPWorker runs off-thread and emits success/failure signals.
- Double-click guard prevents concurrent GP runs.
- No GP engine logic lives in widgets.
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

def test_gp_run_button_exists():
    """GABuildPanel must initialise with a Run GP button."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.widgets.ga_build_panel import GABuildPanel
    panel = GABuildPanel()

    assert panel.btn_run_gp is not None
    assert panel.btn_run_gp.isEnabled()
    assert "Run GP" in panel.btn_run_gp.text()

def test_gp_worker_success_updates_panel_and_state():
    """GPWorker emits success signal with result and source_label."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.workers import GPWorker
    from app.services.gp_service import GPSearchConfig, GPSearchResult

    df = _make_df(150)
    cfg = GPSearchConfig(population_size=4, max_generations=2, base_seed=7)

    received = {}

    def on_success(result, label):
        received["result"] = result
        received["label"] = label

    worker = GPWorker(df, cfg, "test_source")
    worker.success.connect(on_success)
    worker.start()
    worker.wait(10_000)
    app.processEvents()

    assert "result" in received
    assert isinstance(received["result"], GPSearchResult)
    assert received["result"].generation_count == 2
    assert received["label"] == "test_source"

def test_gp_worker_failure_updates_status():
    """GPWorker must emit failure signal when run_gp_search raises."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.workers import GPWorker
    from app.services.gp_service import GPSearchConfig

    # Pass None as df — will cause an exception
    cfg = GPSearchConfig(population_size=4, max_generations=2, base_seed=1)

    received = {}

    def on_failure(msg):
        received["error"] = msg

    worker = GPWorker(None, cfg, "bad_data")
    worker.failure.connect(on_failure)
    worker.start()
    worker.wait(10_000)
    app.processEvents()

    assert "error" in received
    assert isinstance(received["error"], str)
    assert len(received["error"]) > 0

def test_gp_double_click_guard():
    """Second _handle_run_gp call while worker is running must be rejected."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.ui.main_window import MainWindow

    window = MainWindow()

    class _FakeWorker:
        def isRunning(self):
            return True

    window._gp_worker = _FakeWorker()

    window._handle_run_gp()

    assert "already running" in window.log_panel.output.toPlainText()
    assert isinstance(window._gp_worker, _FakeWorker)

def test_gp_widget_has_no_engine_imports():
    """Widget file must not import gp engine."""
    source = Path("app/widgets/ga_build_panel.py").read_text(encoding="utf-8")
    assert "strategy_engine.gp" not in source

def test_main_window_does_not_import_gp_engine_directly():
    """MainWindow must not import gp_evolution directly."""
    source = Path("app/ui/main_window.py").read_text(encoding="utf-8")
    assert "import gp_evolution" not in source
    assert "strategy_engine.gp" not in source

def test_ga_build_wiring_still_works():
    """Verify we didn't break the original GA tests."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.widgets.ga_build_panel import GABuildPanel
    panel = GABuildPanel()
    assert panel.btn_run_ga.isEnabled()
    panel.set_running(is_gp=False)
    assert "GA search in progress" in panel.status_label.text()

def test_gp_and_ga_buttons_both_exist():
    """Build panel should have both GP and GA buttons side by side."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.widgets.ga_build_panel import GABuildPanel
    panel = GABuildPanel()
    assert panel.btn_run_ga is not None
    assert panel.btn_run_gp is not None
    assert "Run GA Search" in panel.btn_run_ga.text()
    assert "Run GP Search" in panel.btn_run_gp.text()

def test_gp_worker_success_stores_result_and_strategy(monkeypatch):
    """MainWindow _on_gp_success should store latest_gp_strategy without integrating to DB yet."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.ui.main_window import MainWindow
    from core.models.strategy import Strategy
    from app.services.gp_service import GPSearchResult
    
    window = MainWindow()
    
    # Fake GP result
    fake_strat = Strategy(name="fake_gp_strat")
    fake_res = GPSearchResult(
        best_strategy=fake_strat,
        best_score=1.23,
        generation_count=2,
        final_population_size=10,
        generation_best_scores=[],
        generation_avg_scores=[],
        config_snapshot={}
    )
    
    # Simulate worker success
    window._on_gp_success(fake_res, "test_source")
    
    # Check that state was updated
    assert hasattr(window, "_latest_gp_strategy")
    assert window._latest_gp_strategy.name == "[GP Best] fake_gp_strat"
    
    # Also verify it did NOT update the GA latest strategy
    assert not hasattr(window, "_latest_ga_strategy") or window._latest_ga_strategy is None
    
    # Verify status update
    assert "GP completed" in window.ga_build_panel.status_label.text()
    assert "1.2300" in window.ga_build_panel.status_label.text()

def test_gp_failure_does_not_leave_running_state():
    """MainWindow _on_gp_failure updates status but does not leave UI blocked."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.ui.main_window import MainWindow
    window = MainWindow()
    
    window._on_gp_failure("Simulated GP Error")
    
    assert "failed: Simulated GP Error" in window.ga_build_panel.status_label.text()
    # It leaves it with the error message. It doesn't lock the buttons though, that happens via finished signal.
    # We simulate finished:
    window._on_gp_finished()
    assert window.ga_build_panel.btn_run_gp.isEnabled()
    assert window._gp_worker is None

def test_gp_and_ga_status_rendering_do_not_conflict():
    """GABuildPanel status shouldn't crash or permanently break when switching between GA and GP."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.widgets.ga_build_panel import GABuildPanel
    panel = GABuildPanel()
    
    panel.set_running(is_gp=True)
    assert "GP search" in panel.status_label.text()
    panel.set_idle()
    
    panel.set_running(is_gp=False)
    assert "GA search" in panel.status_label.text()
    panel.set_idle()

def test_build_panel_can_render_ga_and_gp_results():
    """GABuildPanel can render both GASearchResult and GPSearchResult identically."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.widgets.ga_build_panel import GABuildPanel
    from core.models.strategy import Strategy
    from app.services.gp_service import GPSearchResult
    from app.services.ga_service import GASearchResult
    
    panel = GABuildPanel()
    
    gp_res = GPSearchResult(
        best_strategy=Strategy(name="gp_test_strat"),
        best_score=0.5,
        generation_count=1,
        final_population_size=1,
        generation_best_scores=[],
        generation_avg_scores=[],
        config_snapshot={}
    )
    panel.update_from_result(gp_res, source_label="mock_gp")
    assert "GP completed" in panel.status_label.text()
    
    from PySide6.QtWidgets import QLabel
    labels = panel.findChildren(QLabel)
    assert any("gp_test_strat" in l.text() for l in labels)
    
    ga_res = GASearchResult(
        best_strategy=Strategy(name="ga_test_strat"),
        best_score=0.6,
        generation_count=1,
        final_population_size=1,
        generation_best_scores=[],
        generation_avg_scores=[],
        config_snapshot={}
    )
    panel.update_from_result(ga_res, source_label="mock_ga")
    assert "GA completed" in panel.status_label.text()
    
    labels = panel.findChildren(QLabel)
    assert any("ga_test_strat" in l.text() for l in labels)

def test_gp_main_window_forwards_mtf_config(monkeypatch):
    """Prove MainWindow._handle_run_gp forwards MTF config to GPSearchConfig."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.ui.main_window import MainWindow
    window = MainWindow()
    
    # Configure the build panel's MTF settings
    window.ga_build_panel.chk_enable_mtf.setChecked(True)
    window.ga_build_panel.le_allowed_timeframes.setText("5, 15")
    window.ga_build_panel.spin_mtf_probability.setValue(0.75)

    captured_cfg = {}
    
    class FakeGPWorker:
        def __init__(self, df, cfg, source_label, instrument=None, parent=None, commission=0.0):
            captured_cfg["cfg"] = cfg
            self.success = type("Signal", (), {"connect": lambda self, fn: None})()
            self.failure = type("Signal", (), {"connect": lambda self, fn: None})()
            self.finished = type("Signal", (), {"connect": lambda self, fn: None})()
            
        def start(self):
            pass

    import app.workers
    monkeypatch.setattr(app.workers, "GPWorker", FakeGPWorker)
    
    window._handle_run_gp()
    
    assert "cfg" in captured_cfg
    cfg = captured_cfg["cfg"]
    assert cfg.mtf_probability == 0.75
    assert set(cfg.allowed_timeframes) == {5, 15}
