"""Tests for Results page ↔ TradeListWidget integration (Task 036B-Codex / 036C)."""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from core.models.backtest_result import Trade


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
    main_window.trade_list.set_trades([])



def _make_trade(direction="long", pnl=5.0):
    return Trade(
        entry_time=pd.Timestamp("2026-01-01 09:00"),
        exit_time=pd.Timestamp("2026-01-01 10:00"),
        direction=direction,
        entry_price=100.0,
        exit_price=105.0 if pnl > 0 else 95.0,
        pnl=pnl,
        exit_reason="signal",
    )


def test_trade_list_exists_on_results_page(main_window):
    """TradeListWidget is wired into the Results page."""
    win = main_window
    assert hasattr(win, "trade_list"), "MainWindow must have a trade_list attribute"
    assert hasattr(win, "results_tabs"), "MainWindow must have a results_tabs tabwidget"


def test_strategy_selection_populates_trade_list(main_window):
    """Selecting a strategy in the ranking table populates the trade list."""
    win = main_window
    # Verify ranked_data has trades
    assert len(win.ranked_data) > 0, "Expected at least one ranked strategy"

    # Select first row in the results table
    win.results_table.table.selectRow(0)

    strat_item = win.ranked_data[0]
    expected_trades = strat_item.get("trades")
    if expected_trades:
        assert win.trade_list.table.rowCount() > 0, \
            "Trade list should have rows after selecting a strategy with trades"
    else:
        assert win.trade_list.table.rowCount() == 0


def test_selecting_different_strategy_replaces_trades(main_window):
    """Selecting a different strategy replaces the trade list data."""
    win = main_window
    if len(win.ranked_data) < 2:
        pytest.skip("Need at least 2 ranked strategies")

    # Select first strategy
    win.results_table.table.selectRow(0)
    first_row_count = win.trade_list.table.rowCount()

    # Select second strategy
    win.results_table.table.selectRow(1)
    # The trade list must reflect the second strategy's trades
    second_trades = win.ranked_data[1].get("trades")
    if second_trades:
        assert win.trade_list.table.rowCount() == len(second_trades)
    else:
        assert win.trade_list.table.rowCount() == 0


def test_ranked_data_carries_trades(main_window):
    """StrategyService ranked entries must carry 'trades' key from backtest."""
    win = main_window
    for entry in win.ranked_data:
        assert "trades" in entry, \
            f"Ranked entry missing 'trades' key: {list(entry.keys())}"


def test_trade_list_shows_trade_objects(main_window):
    """Trade list correctly renders Trade dataclass objects from backtest results."""
    win = main_window
    # Find an entry with at least one trade
    trade_entry = None
    for entry in win.ranked_data:
        trades = entry.get("trades")
        if trades and len(trades) > 0:
            trade_entry = entry
            break

    if trade_entry is None:
        pytest.skip("No ranked strategies produced trades")

    # Manually feed trades into widget
    win.trade_list.set_trades(trade_entry["trades"])
    assert win.trade_list.table.rowCount() == len(trade_entry["trades"])

    # Verify first row has valid data (not empty strings)
    first_trade = trade_entry["trades"][0]
    if isinstance(first_trade, Trade):
        pnl_text = win.trade_list.table.item(0, 5).text()
        assert pnl_text != "", "PnL cell must not be empty"
        assert float(pnl_text) == pytest.approx(first_trade.pnl, abs=0.01)


def test_strategy_with_no_trades_clears_list(main_window):
    """Selecting a strategy with no trades shows empty state."""
    win = main_window
    # Manually set trades then clear
    win.trade_list.set_trades([_make_trade()])
    assert win.trade_list.table.rowCount() == 1

    win.trade_list.set_trades([])
    assert win.trade_list.table.rowCount() == 0
    assert win.trade_list.lbl_page_info.text() == "No trades"


def test_widget_is_passive(qapp):
    """TradeListWidget must not import engine modules."""
    import app.widgets.trade_list as mod
    source = open(mod.__file__, "r", encoding="utf-8").read()
    # Must not import backtest/strategy/validation engines
    assert "backtest_engine" not in source
    assert "strategy_engine" not in source
    assert "validation_engine" not in source
    assert "run_backtest" not in source


# ── Task 036C — Real Results data-flow hardening tests ───────────────────


def test_strategy_a_shows_strategy_a_trades(main_window):
    """Selecting strategy A shows exactly strategy A's trades with matching PnLs."""
    win = main_window
    assert len(win.ranked_data) > 0

    # Select first strategy (strategy A)
    win.results_table.table.selectRow(0)
    trades_a = win.ranked_data[0].get("trades", [])

    # Verify the widget shows exactly the right trades
    assert win.trade_list.table.rowCount() == len(trades_a)

    # Verify PnL identity for each visible trade (up to page size)
    for i, trade in enumerate(trades_a[:win.trade_list.page_size]):
        expected_pnl = trade.pnl if isinstance(trade, Trade) else trade.get("pnl", 0)
        displayed_pnl = float(win.trade_list.table.item(i, 5).text())
        assert displayed_pnl == pytest.approx(expected_pnl, abs=0.01), \
            f"Trade {i}: displayed PnL {displayed_pnl} != expected {expected_pnl}"


def test_strategy_b_replaces_with_strategy_b_trades(main_window):
    """Selecting strategy B replaces with strategy B's exact trades."""
    win = main_window
    if len(win.ranked_data) < 2:
        pytest.skip("Need at least 2 ranked strategies")

    # Select strategy A first, then B
    win.results_table.table.selectRow(0)
    trades_a = win.ranked_data[0].get("trades", [])

    win.results_table.table.selectRow(1)
    trades_b = win.ranked_data[1].get("trades", [])

    # Widget must now show B's trades
    assert win.trade_list.table.rowCount() == len(trades_b)

    # If B has trades, verify PnL identity
    for i, trade in enumerate(trades_b[:win.trade_list.page_size]):
        expected_pnl = trade.pnl if isinstance(trade, Trade) else trade.get("pnl", 0)
        displayed_pnl = float(win.trade_list.table.item(i, 5).text())
        assert displayed_pnl == pytest.approx(expected_pnl, abs=0.01)


def test_all_trades_are_trade_objects(main_window):
    """Backtest results should produce Trade dataclass objects, not raw dicts."""
    win = main_window
    for i, entry in enumerate(win.ranked_data):
        trades = entry.get("trades", [])
        for j, trade in enumerate(trades):
            assert isinstance(trade, Trade), \
                f"Strategy {i}, trade {j}: expected Trade, got {type(trade).__name__}"


def test_ga_injected_strategy_updates_trade_list(qapp):
    """GA-injected best strategy carries trades and updates the trade list when selected."""
    import copy
    from core.models.strategy import Strategy, StrategyBlock, Condition

    win = MainWindow()

    # Simulate a GA strategy injection
    ga_strategy = Strategy(
        name="[GA Best] test_ga_strat",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 10}, operator=">")],
            logic="AND",
        ),
        long_exit=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 10}, operator="<")],
            logic="AND",
        ),
    )
    win._latest_ga_strategy = copy.deepcopy(ga_strategy)

    # Re-generate ranked data with injected GA strategy
    win._refresh_results_ranking()

    # Find the GA strategy in ranked_data
    ga_entry = None
    ga_row = None
    for idx, entry in enumerate(win.ranked_data):
        strat = entry.get("strategy")
        if strat and "[GA Best]" in strat.name:
            ga_entry = entry
            ga_row = idx
            break

    assert ga_entry is not None, "GA best strategy not found in ranked_data"
    assert "trades" in ga_entry, "GA entry must carry trades"

    # Select the GA row
    win.results_table.table.selectRow(ga_row)
    ga_trades = ga_entry.get("trades", [])
    assert win.trade_list.table.rowCount() == len(ga_trades)


def test_trades_carry_required_fields(main_window):
    """Each Trade from backtest must have all required fields for display."""
    win = main_window
    for entry in win.ranked_data:
        for trade in entry.get("trades", []):
            assert hasattr(trade, "entry_time") or "entry_time" in trade
            assert hasattr(trade, "exit_time") or "exit_time" in trade
            assert hasattr(trade, "direction") or "direction" in trade
            assert hasattr(trade, "entry_price") or "entry_price" in trade
            assert hasattr(trade, "exit_price") or "exit_price" in trade
            assert hasattr(trade, "pnl") or "pnl" in trade

