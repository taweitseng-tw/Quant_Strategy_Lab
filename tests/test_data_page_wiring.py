"""Tests for DataService and CandlestickChart — Task 012 / Task 019A."""

from __future__ import annotations

import sys
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from app.services.data_service import DataService
from app.widgets.candlestick_chart import CandlestickChart, PYQTGRAPH_AVAILABLE


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
