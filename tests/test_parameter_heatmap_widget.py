"""Tests for the ParameterHeatmapWidget (Task 036A)."""

import pytest
from PySide6.QtWidgets import QApplication
from app.widgets.parameter_heatmap import ParameterHeatmapWidget
from core.models.strategy import Strategy, StrategyBlock, Condition

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_parameter_heatmap_empty(qapp):
    widget = ParameterHeatmapWidget()
    widget.set_data([])
    assert widget.table.isHidden()
    assert not widget.lbl_empty.isHidden()
    assert widget.lbl_empty.text() == "No strategy data available"

def test_parameter_heatmap_with_data(qapp):
    widget = ParameterHeatmapWidget()
    
    strat1 = Strategy(
        name="Strat1",
        long_entry=StrategyBlock(conditions=[Condition(indicator="SMA", params={"period": 10}, operator=">")], logic="AND")
    )
    strat2 = Strategy(
        name="Strat2",
        long_entry=StrategyBlock(conditions=[Condition(indicator="SMA", params={"period": 20}, operator=">")], logic="AND")
    )
    
    data = [
        {"rank": 1, "strategy": strat1, "fitness": 1.5, "metrics": {"total_pnl": 1000.0, "profit_factor": 1.5}},
        {"rank": 2, "strategy": strat2, "fitness": 1.0, "metrics": {"total_pnl": 500.0, "profit_factor": 1.2}}
    ]
    
    widget.set_data(data)
    
    assert not widget.table.isHidden()
    assert widget.table.rowCount() == 2
    headers = [widget.table.horizontalHeaderItem(i).text() for i in range(widget.table.columnCount())]
    assert "LE.SMA.period" in headers
    assert "LE.SMA.threshold" not in headers
    
    # Check values
    assert widget.table.item(0, 1).text() == "Strat1"
    
    # Find LE.SMA.period column index
    period_idx = headers.index("LE.SMA.period")
    assert widget.table.item(0, period_idx).text() == "10"

def test_parameter_heatmap_threshold_indicators(qapp):
    widget = ParameterHeatmapWidget()

    strat = Strategy(
        name="ThresholdStrat",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="RSI", params={"period": 14}, operator="<", right=30.0)
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="ATR", params={"period": 10}, operator=">", right=2.5)
        ], logic="AND"),
    )

    widget.set_data([{"rank": 1, "strategy": strat, "fitness": 1.0, "metrics": {}}])
    headers = [widget.table.horizontalHeaderItem(i).text() for i in range(widget.table.columnCount())]

    assert "LE.RSI.period" in headers
    assert "LE.RSI.threshold" in headers
    assert "LX.ATR.period" in headers
    assert "LX.ATR.threshold" in headers

    rsi_threshold_idx = headers.index("LE.RSI.threshold")
    atr_threshold_idx = headers.index("LX.ATR.threshold")
    assert widget.table.item(0, rsi_threshold_idx).text() == "30"
    assert widget.table.item(0, atr_threshold_idx).text() == "2.50"

def test_parameter_heatmap_coloring(qapp):
    widget = ParameterHeatmapWidget()
    
    strat1 = Strategy("Strat1")
    strat2 = Strategy("Strat2")
    
    data = [
        {"rank": 1, "strategy": strat1, "fitness": 1.0, "metrics": {"total_pnl": -100.0}},
        {"rank": 2, "strategy": strat2, "fitness": 2.0, "metrics": {"total_pnl": 100.0}}
    ]
    
    widget.set_data(data)
    
    # strat1 fitness is 1.0 (min), strat2 is 2.0 (max)
    # Check that colors are applied (foreground is set)
    item1 = widget.table.item(0, 2) # Fitness row 0
    item2 = widget.table.item(1, 2) # Fitness row 1
    
    c1 = item1.foreground().color()
    c2 = item2.foreground().color()
    
    # c2 (higher fitness) should have more green and less red than c1
    assert c2.green() > c1.green()
    assert c2.red() < c1.red()

def test_parameter_heatmap_non_numeric_params(qapp):
    widget = ParameterHeatmapWidget()
    strat = Strategy(
        name="Strat1",
        long_entry=StrategyBlock(conditions=[Condition(indicator="CUSTOM", params={"mode": "fast", "val": 15}, operator=">")])
    )
    
    widget.set_data([{"strategy": strat}])
    
    headers = [widget.table.horizontalHeaderItem(i).text() for i in range(widget.table.columnCount())]
    assert "LE.CUSTOM.val" in headers
    assert "LE.CUSTOM.mode" not in headers  # Should be skipped because "fast" is a string

def test_parameter_heatmap_non_numeric_metrics_do_not_crash(qapp):
    widget = ParameterHeatmapWidget()
    strat = Strategy("MetricFallback")

    widget.set_data([{
        "strategy": strat,
        "fitness": "not-a-number",
        "metrics": {"total_pnl": None, "profit_factor": "bad"},
    }])

    assert widget.table.rowCount() == 1
    assert widget.table.item(0, 2).text() == "0.0000"
    assert widget.table.item(0, 3).text() == "0.00"
    assert widget.table.item(0, 4).text() == "0.00"

def test_widget_is_passive(qapp):
    import app.widgets.parameter_heatmap as mod
    source = open(mod.__file__, "r", encoding="utf-8").read()
    assert "backtest_engine" not in source
    assert "strategy_engine" not in source
    assert "validation_engine" not in source
