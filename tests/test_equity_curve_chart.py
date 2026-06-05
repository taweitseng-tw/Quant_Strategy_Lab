"""Tests for EquityCurveChart widget and Results page integration — Task 010."""

from __future__ import annotations

import sys
import numpy as np
import pandas as pd
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.services.strategy_service import StrategyService
from app.widgets.equity_curve_chart import EquityCurveChart, PYQTGRAPH_AVAILABLE
from app.widgets.ranking_table import RankingTable


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Fixture to initialize a QApplication instance for GUI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_equity_curve_chart_widget_initialization(qapp) -> None:
    """Verify that EquityCurveChart widget builds cleanly and starts with mock data."""
    chart = EquityCurveChart()
    assert chart.is_mock_data is True
    
    if PYQTGRAPH_AVAILABLE:
        assert chart.equity_plot is not None
        assert chart.drawdown_plot is not None
        # Check plots are successfully established
        assert chart.equity_plot.plotItem is not None
        assert chart.drawdown_plot.plotItem is not None
    else:
        assert chart.fallback_label is not None


def test_equity_curve_chart_widget_set_data(qapp) -> None:
    """Verify set_data handles valid equity/drawdown DataFrames correctly without crashing."""
    chart = EquityCurveChart()
    
    dates = pd.date_range(start="2026-01-01", periods=10, freq="D")
    eq_df = pd.DataFrame({
        "datetime": dates,
        "equity": np.linspace(100000.0, 105000.0, 10)
    })
    dd_df = pd.DataFrame({
        "datetime": dates,
        "drawdown": np.linspace(0.0, -1500.0, 10)
    })
    
    # Should run cleanly
    chart.set_data(eq_df, dd_df, is_mock=False)
    assert chart.is_mock_data is False
    
    if PYQTGRAPH_AVAILABLE:
        assert not chart.drawdown_plot.isHidden()
        
        # Test setting drawdown to None hides the drawdown plot panel gracefully
        chart.set_data(eq_df, None, is_mock=False)
        assert chart.drawdown_plot.isHidden()


def test_strategy_service_includes_curves() -> None:
    """Verify StrategyService backtests contain the equity and drawdown curve DataFrames."""
    service = StrategyService()
    ranked, is_mock = service.get_ranked_strategies()
    
    assert len(ranked) == 10
    for item in ranked:
        assert "equity_curve" in item
        assert "drawdown_curve" in item
        assert "trades" in item
        assert "warnings" in item
        
        eq_df = item["equity_curve"]
        dd_df = item["drawdown_curve"]
        
        assert isinstance(eq_df, pd.DataFrame)
        assert isinstance(dd_df, pd.DataFrame)
        assert "datetime" in eq_df.columns
        assert "equity" in eq_df.columns
        assert "datetime" in dd_df.columns
        assert "drawdown" in dd_df.columns


def test_selection_changed_updates_chart_data(qapp) -> None:
    """Verify selecting a strategy in the table pulls out curves and updates the chart correctly."""
    service = StrategyService()
    ranked_data, is_mock = service.get_ranked_strategies()
    
    table = RankingTable()
    chart = EquityCurveChart()
    
    table.set_ranking_data(ranked_data, is_mock=is_mock)
    assert table.table.rowCount() == 10
    
    # Select a specific row (e.g. index 2, third ranked strategy)
    table.table.selectRow(2)
    
    # Verify selected strategy data extraction
    selected_ranges = table.table.selectedRanges()
    assert len(selected_ranges) == 1
    row = selected_ranges[0].topRow()
    assert row == 2
    
    strat_item = ranked_data[row]
    equity_df = strat_item["equity_curve"]
    drawdown_df = strat_item["drawdown_curve"]
    
    # Set data on the chart
    chart.set_data(equity_df, drawdown_df, is_mock=is_mock)
    assert chart.is_mock_data is is_mock
