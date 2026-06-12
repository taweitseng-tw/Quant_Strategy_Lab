"""Tests for ValidationWorker — Tasks 541-546."""

from __future__ import annotations

import sys
import pandas as pd
import pytest
from PySide6.QtWidgets import QApplication

from app.services.validation_pipeline_service import PipelineConfig
from app.workers import ValidationWorker
from core.models.strategy import Strategy, StrategyBlock, Condition
from core.models.instrument import InstrumentProfile


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def _make_test_strategy() -> Strategy:
    return Strategy(
        name="test_strat",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator="<"),
        ], logic="AND"),
    )


def test_validation_worker_progress_signals(qapp):
    """ValidationWorker must emit progress_updated signals during execution."""
    df = pd.DataFrame({
        "datetime": pd.date_range("2026-01-01", periods=100, freq="1min"),
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000,
    })
    config = PipelineConfig(mc_iterations=5)
    captured = []

    def capture(stage: str):
        captured.append(stage)

    worker = ValidationWorker(df, _make_test_strategy(), config)
    worker.progress_updated.connect(capture)
    worker.run()

    assert len(captured) >= 2, f"Expected at least 2 progress signals, got {captured}"
    assert any("Splitting" in s for s in captured), f"Expected 'Splitting' stage, got {captured}"


def test_validation_worker_success_signal(qapp):
    """ValidationWorker must emit success with a PipelineResult on clean run."""
    df = pd.DataFrame({
        "datetime": pd.date_range("2026-01-01", periods=100, freq="1min"),
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000,
    })
    config = PipelineConfig(mc_iterations=5)
    result_container = []

    def capture(result):
        result_container.append(result)

    worker = ValidationWorker(df, _make_test_strategy(), config)
    worker.success.connect(capture)
    worker.run()

    assert len(result_container) == 1, f"Expected 1 success signal, got {len(result_container)}"
    result = result_container[0]
    assert result.baseline_metrics is not None
    assert "total_pnl" in result.baseline_metrics


def test_validation_worker_failure_signal(qapp):
    """ValidationWorker must emit failure on bad input."""
    config = PipelineConfig(mc_iterations=5)
    captured = []

    def capture(msg: str):
        captured.append(msg)

    worker = ValidationWorker(pd.DataFrame(), _make_test_strategy(), config)
    worker.failure.connect(capture)
    worker.run()

    assert len(captured) == 1, f"Expected 1 failure signal, got {captured}"
    assert len(captured[0]) > 0


def test_validation_worker_stores_data_source_and_mock_flag(qapp):
    """ValidationWorker must preserve data_source and is_mock for the success handler."""
    config = PipelineConfig(mc_iterations=5)
    worker = ValidationWorker(
        pd.DataFrame({
            "datetime": pd.date_range("2026-01-01", periods=100, freq="1min"),
            "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000,
        }),
        _make_test_strategy(),
        config,
        data_source="custom_source",
        is_mock=True,
    )
    worker.run()
    assert worker._data_source == "custom_source"
    assert worker._is_mock is True


def test_validation_worker_stop_before_run_emits_cancelled(qapp):
    """Calling stop() before run() must emit failure with a cancelled message."""
    df = pd.DataFrame({
        "datetime": pd.date_range("2026-01-01", periods=50, freq="1min"),
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000,
    })
    config = PipelineConfig(mc_iterations=5)
    captured = []

    def capture(msg: str):
        captured.append(msg)

    worker = ValidationWorker(df, _make_test_strategy(), config)
    worker.failure.connect(capture)
    worker.stop()  # set flag before run
    worker.run()

    assert len(captured) == 1, f"Expected 1 failure, got {captured}"
    assert "cancelled" in captured[0].lower(), f"Expected 'cancelled', got {captured[0]}"


def test_validation_worker_stop_not_set_does_not_cancel(qapp):
    """Without calling stop(), pipeline must complete normally."""
    df = pd.DataFrame({
        "datetime": pd.date_range("2026-01-01", periods=50, freq="1min"),
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000,
    })
    config = PipelineConfig(mc_iterations=5)
    success_captured = []
    failure_captured = []

    def on_success(result):
        success_captured.append(result)

    def on_failure(msg):
        failure_captured.append(msg)

    worker = ValidationWorker(df, _make_test_strategy(), config)
    worker.success.connect(on_success)
    worker.failure.connect(on_failure)
    worker.run()

    assert len(success_captured) == 1, f"Expected success, got {len(success_captured)}"
    assert len(failure_captured) == 0, f"Expected no failure, got {failure_captured}"


def test_validation_worker_stop_after_pipeline_suppresses_success(qapp, monkeypatch):
    """Stop requested after the pipeline returns must emit cancellation failure only."""
    df = pd.DataFrame({
        "datetime": pd.date_range("2026-01-01", periods=50, freq="1min"),
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000,
    })
    config = PipelineConfig(mc_iterations=5)
    success_captured = []
    failure_captured = []
    worker_holder = {}

    def fake_pipeline(*args, **kwargs):
        worker_holder["worker"].stop()
        return object()

    monkeypatch.setattr("app.workers.run_validation_pipeline", fake_pipeline)
    worker = ValidationWorker(df, _make_test_strategy(), config)
    worker_holder["worker"] = worker
    worker.success.connect(success_captured.append)
    worker.failure.connect(failure_captured.append)

    worker.run()

    assert success_captured == []
    assert len(failure_captured) == 1
    assert "cancelled" in failure_captured[0].lower()
