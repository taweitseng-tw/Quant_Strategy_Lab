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
