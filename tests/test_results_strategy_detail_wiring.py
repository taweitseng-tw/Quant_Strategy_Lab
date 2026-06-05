"""Tests for Results page ↔ StrategyDetailWidget integration (Task 038A)."""

import pytest
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture(scope="module")
def main_window(qapp):
    return MainWindow()

@pytest.fixture(autouse=True)
def reset_main_window_state(main_window):
    """
    Ensure clean UI state between tests using the shared MainWindow.
    This prevents stale selection state from masking bugs where selectRow(0)
    fails to emit itemSelectionChanged because it was already selected.
    """
    main_window.results_table.table.clearSelection()
    if hasattr(main_window, "strategy_detail"):
        main_window.strategy_detail.set_strategy_data(None)

def test_strategy_detail_exists_on_results_page(main_window):
    """StrategyDetailWidget is wired into the Results page."""
    win = main_window
    assert hasattr(win, "strategy_detail"), "MainWindow must have a strategy_detail attribute"
    assert hasattr(win, "results_tabs"), "MainWindow must have a results_tabs tabwidget"

def test_strategy_selection_updates_detail_widget(main_window):
    """Selecting a strategy in the ranking table populates the detail widget."""
    win = main_window
    assert len(win.ranked_data) > 0, "Expected at least one ranked strategy"

    # Select first row in the results table
    win.results_table.table.selectRow(0)

    strat_item = win.ranked_data[0]
    expected_name = strat_item.get("strategy").name
    
    assert win.strategy_detail.lbl_name.text() == expected_name
    assert "Fitness: " in win.strategy_detail.lbl_fitness.text()
    assert win.strategy_detail.lbl_fitness.text() != "Fitness: -"

def test_selecting_different_strategy_updates_detail(main_window):
    """Selecting a different strategy replaces the detail data."""
    win = main_window
    if len(win.ranked_data) < 2:
        pytest.skip("Need at least 2 ranked strategies")

    # Select first strategy
    win.results_table.table.selectRow(0)
    first_name = win.strategy_detail.lbl_name.text()

    # Select second strategy
    win.results_table.table.selectRow(1)
    second_name = win.strategy_detail.lbl_name.text()
    
    assert win.strategy_detail.lbl_name.text() == win.ranked_data[1]["strategy"].name
    if win.ranked_data[0]["strategy"].name != win.ranked_data[1]["strategy"].name:
        assert first_name != second_name


def test_clearing_selection_clears_detail_widget(main_window):
    """Clearing table selection returns the detail widget to empty state."""
    win = main_window
    assert len(win.ranked_data) > 0

    win.results_table.table.selectRow(0)
    assert win.strategy_detail.lbl_name.text() == win.ranked_data[0]["strategy"].name

    win.results_table.table.clearSelection()
    win._handle_strategy_selection_changed()

    assert "No Strategy Selected" in win.strategy_detail.lbl_name.text()

def test_widget_is_passive(qapp):
    """StrategyDetailWidget must not import engine modules."""
    import app.widgets.strategy_detail as mod
    source = open(mod.__file__, "r", encoding="utf-8").read()
    # Must not import backtest/strategy/validation engines
    assert "backtest_engine" not in source
    assert "validation_engine" not in source
    assert "run_backtest" not in source


def test_strategy_detail_base_condition_display(qapp):
    """Base conditions are displayed without MTF suffixes."""
    from app.widgets.strategy_detail import StrategyDetailWidget
    from core.models.strategy import Strategy, StrategyBlock, Condition

    widget = StrategyDetailWidget()
    strat = Strategy(
        name="Test",
        long_entry=StrategyBlock([Condition("SMA", {"period": 20}, ">")])
    )
    
    html_output = widget._format_blocks(strat)
    assert "<b>SMA</b>(period=20)" in html_output
    assert "[TF:" not in html_output


def test_strategy_detail_mtf_all_supported_indicators_display(qapp):
    """All supported MTF indicators append [TF: Nm] and do not duplicate timeframe in params."""
    from app.widgets.strategy_detail import StrategyDetailWidget
    from core.models.strategy import Strategy, StrategyBlock, Condition

    widget = StrategyDetailWidget()
    
    # 1. SMA (Standard left side)
    strat_sma = Strategy(
        name="Test",
        long_entry=StrategyBlock([Condition("SMA", {"period": 20, "timeframe": 15}, ">", left="close")])
    )
    assert "[TF: 15m]" in widget._format_blocks(strat_sma)
    assert "<b>SMA</b>(period=20)" in widget._format_blocks(strat_sma)

    # 2. RSI (Threshold)
    strat_rsi = Strategy(
        name="Test",
        long_entry=StrategyBlock([Condition("RSI", {"period": 14, "timeframe": 5}, "<", right=30)])
    )
    assert "[TF: 5m]" in widget._format_blocks(strat_rsi)
    assert "<b>RSI</b>(period=14) <i>&lt;</i> 30" in widget._format_blocks(strat_rsi)

    # 3. MACD
    strat_macd = Strategy(
        name="Test",
        long_entry=StrategyBlock([Condition("MACD", {"fast": 12, "slow": 26, "signal": 9, "timeframe": 60}, ">")])
    )
    assert "[TF: 60m]" in widget._format_blocks(strat_macd)
    assert "<b>MACD</b>(fast=12, slow=26, signal=9) <i>&gt;</i> signal" in widget._format_blocks(strat_macd)

    # 4. ATR (Threshold)
    strat_atr = Strategy(
        name="Test",
        long_entry=StrategyBlock([Condition("ATR", {"period": 14, "timeframe": 15}, "<", right=2.5)])
    )
    assert "[TF: 15m]" in widget._format_blocks(strat_atr)
    assert "<b>ATR</b>(period=14) <i>&lt;</i> 2.5" in widget._format_blocks(strat_atr)

    # 5. VOLUME (Standard)
    strat_vol = Strategy(
        name="Test",
        long_entry=StrategyBlock([Condition("VOLUME", {"timeframe": 5}, ">", left="close")])
    )
    assert "[TF: 5m]" in widget._format_blocks(strat_vol)
    assert "<b>VOLUME</b>()" in widget._format_blocks(strat_vol)

    # 6. VOLUME_SMA (Standard)
    strat_volsma = Strategy(
        name="Test",
        long_entry=StrategyBlock([Condition("VOLUME_SMA", {"period": 20, "timeframe": 5}, ">", left="close")])
    )
    assert "[TF: 5m]" in widget._format_blocks(strat_volsma)
    assert "<b>VOLUME_SMA</b>(period=20)" in widget._format_blocks(strat_volsma)


def test_strategy_detail_mtf_malicious_html_escaped(qapp):
    """Malicious timeframe or params must be HTML escaped."""
    from app.widgets.strategy_detail import StrategyDetailWidget
    from core.models.strategy import Strategy, StrategyBlock, Condition

    widget = StrategyDetailWidget()
    strat = Strategy(
        name="Test",
        long_entry=StrategyBlock([
            Condition(
                indicator="SMA", 
                params={"period": "<script>alert(1)</script>", "timeframe": "<img src=x onerror=alert(1)>"}, 
                operator=">"
            )
        ])
    )
    
    html_output = widget._format_blocks(strat)
    assert "<script>" not in html_output
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_output
    assert "&lt;img src=x onerror=alert(1)&gt;" in html_output
    assert "[TF: &lt;img src=x onerror=alert(1)&gt;m]" in html_output
