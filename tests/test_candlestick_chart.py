"""Tests for reusable CandlestickChart widget — Task 004B."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pytest
from PySide6.QtWidgets import QApplication

from app.widgets.candlestick_chart import CandlestickChart, CandlestickItem


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Fixture to initialize a QApplication instance for GUI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_candlestick_widget_initialization(qapp) -> None:
    """Verify that CandlestickChart can be initialized and auto-loads mock data."""
    chart = CandlestickChart()
    assert chart is not None
    assert chart.is_mock_data is True
    
    # If pyqtgraph is available, check elements
    if hasattr(chart, "plot_widget"):
        assert chart.plot_widget is not None
        assert chart.candlestick_item is not None
        assert chart.date_axis is not None


def test_candlestick_widget_set_data(qapp) -> None:
    """Verify that set_data accepts a normalized DataFrame and updates internal state."""
    chart = CandlestickChart()
    
    # Create a small normalized DataFrame
    dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(5)]
    df = pd.DataFrame({
        "datetime": dates,
        "open": [10.0, 11.0, 10.5, 12.0, 11.5],
        "high": [12.0, 13.0, 12.5, 14.0, 13.5],
        "low": [9.0, 10.0, 9.5, 11.0, 10.5],
        "close": [11.0, 10.5, 12.0, 11.5, 13.0],
        "volume": [1000, 1200, 1100, 1500, 1400],
    })
    
    chart.set_data(df, is_mock=False)
    assert chart.is_mock_data is False
    
    if hasattr(chart, "plot_widget"):
        assert chart.plot_widget is not None


def test_candlestick_widget_invalid_data_logged(qapp, caplog) -> None:
    """Verify that missing columns log an error and do not crash."""
    chart = CandlestickChart()
    
    # DataFrame missing required columns
    bad_df = pd.DataFrame({
        "datetime": [datetime.now()],
        "open": [10.0],
    })
    
    chart.set_data(bad_df)
    # The error should be logged, but it shouldn't raise exception
    assert any("missing columns" in record.message for record in caplog.records)
