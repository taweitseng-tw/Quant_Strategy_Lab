"""Tests for the TradeListWidget (Task 036B)."""

import pytest
import pandas as pd
from PySide6.QtWidgets import QApplication

from app.widgets.trade_list import TradeListWidget
from core.models.backtest_result import Trade

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_trade_list_widget_initialization(qapp):
    widget = TradeListWidget()
    assert widget.table.rowCount() == 0
    assert widget.current_page == 0
    assert widget.lbl_page_info.text() == "No trades"
    assert not widget.btn_prev.isEnabled()
    assert not widget.btn_next.isEnabled()

def test_trade_list_pagination(qapp):
    widget = TradeListWidget()
    
    # Create 55 mock trades
    mock_trades = []
    for i in range(55):
        mock_trades.append(Trade(
            entry_time=pd.Timestamp("2026-01-01"),
            exit_time=pd.Timestamp("2026-01-02"),
            direction="long" if i % 2 == 0 else "short",
            entry_price=100.0,
            exit_price=105.0 if i % 2 == 0 else 95.0,
            pnl=5.0,
            exit_reason="signal"
        ))
        
    widget.set_trades(mock_trades)
    
    # Page size defaults to 50
    assert widget.table.rowCount() == 50
    assert widget.current_page == 0
    assert not widget.btn_prev.isEnabled()
    assert widget.btn_next.isEnabled()
    assert "Page 1 of 2" in widget.lbl_page_info.text()
    
    # Go to next page
    widget.next_page()
    assert widget.current_page == 1
    assert widget.table.rowCount() == 5  # 55 - 50 = 5
    assert widget.btn_prev.isEnabled()
    assert not widget.btn_next.isEnabled()
    assert "Page 2 of 2" in widget.lbl_page_info.text()
    
    # Go back to previous page
    widget.prev_page()
    assert widget.current_page == 0
    assert widget.table.rowCount() == 50

def test_trade_list_page_size_change(qapp):
    widget = TradeListWidget()
    mock_trades = [
        Trade(
            entry_time=pd.Timestamp("2026-01-01"),
            exit_time=pd.Timestamp("2026-01-02"),
            direction="long",
            entry_price=100.0,
            exit_price=105.0,
            pnl=5.0,
            exit_reason="signal"
        ) for _ in range(60)
    ]
    widget.set_trades(mock_trades)
    
    # Default 50
    assert widget.table.rowCount() == 50
    assert widget.current_page == 0
    
    # Change to 25
    widget.combo_page_size.setCurrentText("25")
    assert widget.page_size == 25
    assert widget.table.rowCount() == 25
    assert "Page 1 of 3" in widget.lbl_page_info.text()
    
    # Change to 100
    widget.combo_page_size.setCurrentText("100")
    assert widget.page_size == 100
    assert widget.table.rowCount() == 60
    assert "Page 1 of 1" in widget.lbl_page_info.text()

def test_trade_list_dict_support(qapp):
    widget = TradeListWidget()
    mock_trade_dict = {
        "entry_time": pd.Timestamp("2026-01-01 10:00:00"),
        "exit_time": pd.Timestamp("2026-01-01 12:00:00"),
        "direction": "short",
        "entry_price": 200.0,
        "exit_price": 190.0,
        "pnl": 10.0,
        "exit_reason": "take_profit"
    }
    widget.set_trades([mock_trade_dict])
    
    assert widget.table.rowCount() == 1
    
    # Verify values inserted correctly
    assert "2026-01-01 10:00" in widget.table.item(0, 0).text()
    assert "2026-01-01 12:00" in widget.table.item(0, 1).text()
    assert widget.table.item(0, 2).text() == "SHORT"
    assert widget.table.item(0, 3).text() == "200.00"
    assert widget.table.item(0, 4).text() == "190.00"
    assert widget.table.item(0, 5).text() == "10.00"
    assert widget.table.item(0, 7).text() == "take_profit"


# ── Task 036B-Codex — Hardening tests ────────────────────────────────────


def test_zero_trades(qapp):
    """Empty trade list shows 'No trades' and disables both buttons."""
    widget = TradeListWidget()
    widget.set_trades([])
    assert widget.table.rowCount() == 0
    assert widget.lbl_page_info.text() == "No trades"
    assert not widget.btn_prev.isEnabled()
    assert not widget.btn_next.isEnabled()


def test_set_trades_none_resets(qapp):
    """set_trades(None) must clear and show empty state like set_trades([])."""
    widget = TradeListWidget()
    trades = [Trade(
        entry_time=pd.Timestamp("2026-01-01"),
        exit_time=pd.Timestamp("2026-01-02"),
        direction="long", entry_price=100.0, exit_price=105.0,
        pnl=5.0, exit_reason="signal",
    )]
    widget.set_trades(trades)
    assert widget.table.rowCount() == 1

    widget.set_trades(None)
    assert widget.table.rowCount() == 0
    assert widget.lbl_page_info.text() == "No trades"
    assert widget.current_page == 0
    assert not widget.btn_prev.isEnabled()
    assert not widget.btn_next.isEnabled()


def test_exact_page_boundary(qapp):
    """Exactly page_size trades → 1 page, no next button."""
    widget = TradeListWidget()
    trades = [Trade(
        entry_time=pd.Timestamp("2026-01-01"),
        exit_time=pd.Timestamp("2026-01-02"),
        direction="long", entry_price=100.0, exit_price=105.0,
        pnl=5.0, exit_reason="signal",
    ) for _ in range(50)]
    widget.set_trades(trades)
    assert widget.table.rowCount() == 50
    assert "Page 1 of 1" in widget.lbl_page_info.text()
    assert not widget.btn_prev.isEnabled()
    assert not widget.btn_next.isEnabled()


def test_one_over_page_size(qapp):
    """page_size + 1 trades → 2 pages, second page has 1 row."""
    widget = TradeListWidget()
    trades = [Trade(
        entry_time=pd.Timestamp("2026-01-01"),
        exit_time=pd.Timestamp("2026-01-02"),
        direction="long", entry_price=100.0, exit_price=105.0,
        pnl=5.0, exit_reason="signal",
    ) for _ in range(51)]
    widget.set_trades(trades)
    assert "Page 1 of 2" in widget.lbl_page_info.text()
    assert widget.btn_next.isEnabled()

    widget.next_page()
    assert widget.table.rowCount() == 1
    assert "Page 2 of 2" in widget.lbl_page_info.text()
    assert not widget.btn_next.isEnabled()
    assert widget.btn_prev.isEnabled()


def test_page_size_change_from_later_page(qapp):
    """Changing page size while on page 2+ resets to page 0."""
    widget = TradeListWidget()
    trades = [Trade(
        entry_time=pd.Timestamp("2026-01-01"),
        exit_time=pd.Timestamp("2026-01-02"),
        direction="long", entry_price=100.0, exit_price=105.0,
        pnl=5.0, exit_reason="signal",
    ) for _ in range(60)]
    widget.set_trades(trades)

    # Navigate to page 2
    widget.next_page()
    assert widget.current_page == 1

    # Change page size → must reset to page 0
    widget.combo_page_size.setCurrentText("25")
    assert widget.current_page == 0
    assert widget.page_size == 25
    assert widget.table.rowCount() == 25
    assert "Page 1 of 3" in widget.lbl_page_info.text()


def test_prev_at_first_page_is_noop(qapp):
    """Pressing prev on page 0 does nothing."""
    widget = TradeListWidget()
    trades = [Trade(
        entry_time=pd.Timestamp("2026-01-01"),
        exit_time=pd.Timestamp("2026-01-02"),
        direction="long", entry_price=100.0, exit_price=105.0,
        pnl=5.0, exit_reason="signal",
    ) for _ in range(55)]
    widget.set_trades(trades)
    widget.prev_page()
    assert widget.current_page == 0


def test_next_at_last_page_is_noop(qapp):
    """Pressing next on the last page does nothing."""
    widget = TradeListWidget()
    trades = [Trade(
        entry_time=pd.Timestamp("2026-01-01"),
        exit_time=pd.Timestamp("2026-01-02"),
        direction="long", entry_price=100.0, exit_price=105.0,
        pnl=5.0, exit_reason="signal",
    ) for _ in range(55)]
    widget.set_trades(trades)
    widget.next_page()  # page 1
    assert widget.current_page == 1
    widget.next_page()  # should stay at 1
    assert widget.current_page == 1


def test_pnl_coloring_positive_negative_zero(qapp):
    """PnL coloring: positive=teal, negative=red, zero=default."""
    widget = TradeListWidget()
    trades = [
        Trade(entry_time=pd.Timestamp("2026-01-01"), exit_time=pd.Timestamp("2026-01-02"),
              direction="long", entry_price=100.0, exit_price=110.0, pnl=10.0, exit_reason="signal"),
        Trade(entry_time=pd.Timestamp("2026-01-01"), exit_time=pd.Timestamp("2026-01-02"),
              direction="short", entry_price=100.0, exit_price=90.0, pnl=-5.0, exit_reason="stop_loss"),
        Trade(entry_time=pd.Timestamp("2026-01-01"), exit_time=pd.Timestamp("2026-01-02"),
              direction="long", entry_price=100.0, exit_price=100.0, pnl=0.0, exit_reason="signal"),
    ]
    widget.set_trades(trades)
    assert widget.table.rowCount() == 3

    # Verify PnL text is not corrupted
    assert widget.table.item(0, 5).text() == "10.00"
    assert widget.table.item(1, 5).text() == "-5.00"
    assert widget.table.item(2, 5).text() == "0.00"

    # Verify color assignment (positive = #26a69a, negative = #ef5350)
    assert widget.table.item(0, 5).foreground().color().name() == "#26a69a"
    assert widget.table.item(1, 5).foreground().color().name() == "#ef5350"


def test_real_backtest_dict_shape(qapp):
    """Verify widget consumes real backtest-result dict shapes from StrategyService.

    The backtest runner produces Trade dataclass objects but StrategyService
    stores them in the ranked_data dict. The widget must handle both.
    """
    # Shape matching what StrategyService.get_ranked_strategies produces
    real_shape_dict = {
        "entry_time": pd.Timestamp("2026-03-15 09:30:00"),
        "exit_time": pd.Timestamp("2026-03-15 14:00:00"),
        "direction": "long",
        "entry_price": 18500.0,
        "exit_price": 18550.0,
        "quantity": 1,
        "pnl": 50.0,
        "exit_reason": "signal",
    }
    widget = TradeListWidget()
    widget.set_trades([real_shape_dict])
    assert widget.table.rowCount() == 1
    assert widget.table.item(0, 5).text() == "50.00"
    assert widget.table.item(0, 3).text() == "18500.00"

    # Extra keys must not cause crash
    extended_dict = dict(real_shape_dict)
    extended_dict["commission"] = 4.0
    extended_dict["slippage"] = 0.5
    widget.set_trades([extended_dict])
    assert widget.table.rowCount() == 1


def test_multiple_pages_navigation(qapp):
    """Navigate forward through multiple pages and back."""
    widget = TradeListWidget()
    widget.combo_page_size.setCurrentText("25")
    trades = [Trade(
        entry_time=pd.Timestamp("2026-01-01"),
        exit_time=pd.Timestamp("2026-01-02"),
        direction="long", entry_price=100.0, exit_price=105.0,
        pnl=5.0, exit_reason="signal",
    ) for _ in range(80)]
    widget.set_trades(trades)

    assert "Page 1 of 4" in widget.lbl_page_info.text()
    # Forward
    widget.next_page()
    assert "Page 2 of 4" in widget.lbl_page_info.text()
    widget.next_page()
    assert "Page 3 of 4" in widget.lbl_page_info.text()
    widget.next_page()
    assert "Page 4 of 4" in widget.lbl_page_info.text()
    assert widget.table.rowCount() == 5  # 80 - 3*25 = 5
    # Back
    widget.prev_page()
    assert "Page 3 of 4" in widget.lbl_page_info.text()
    widget.prev_page()
    assert "Page 2 of 4" in widget.lbl_page_info.text()
    widget.prev_page()
    assert "Page 1 of 4" in widget.lbl_page_info.text()


def test_total_count_in_label(qapp):
    """Page label must include total trade count."""
    widget = TradeListWidget()
    trades = [Trade(
        entry_time=pd.Timestamp("2026-01-01"),
        exit_time=pd.Timestamp("2026-01-02"),
        direction="long", entry_price=100.0, exit_price=105.0,
        pnl=5.0, exit_reason="signal",
    ) for _ in range(73)]
    widget.set_trades(trades)
    assert "Total: 73" in widget.lbl_page_info.text()


# ── Task 036D — UX polish tests ──────────────────────────────────────────


def test_summary_bar_empty_state(qapp):
    """Summary bar shows 'No trades' when trade list is empty."""
    widget = TradeListWidget()
    widget.set_trades([])
    assert "No trades" in widget.lbl_summary.text()


def test_summary_bar_values(qapp):
    """Summary bar shows correct total, net PnL, win/loss, avg trade."""
    widget = TradeListWidget()
    trades = [
        Trade(entry_time=pd.Timestamp("2026-01-01"), exit_time=pd.Timestamp("2026-01-02"),
              direction="long", entry_price=100.0, exit_price=110.0, pnl=10.0, exit_reason="signal"),
        Trade(entry_time=pd.Timestamp("2026-01-01"), exit_time=pd.Timestamp("2026-01-02"),
              direction="short", entry_price=100.0, exit_price=90.0, pnl=-4.0, exit_reason="stop_loss"),
        Trade(entry_time=pd.Timestamp("2026-01-01"), exit_time=pd.Timestamp("2026-01-02"),
              direction="long", entry_price=100.0, exit_price=100.0, pnl=0.0, exit_reason="signal"),
    ]
    widget.set_trades(trades)
    summary_text = widget.lbl_summary.text()

    # Total trades
    assert "3" in summary_text
    # Net PnL = 10 - 4 + 0 = 6.00
    assert "6.00" in summary_text
    # Wins = 1 (pnl > 0), Losses = 1 (pnl < 0), zero is neither
    assert "1/1" in summary_text
    # Avg trade = 6 / 3 = 2.00
    assert "2.00" in summary_text


def test_summary_bar_updates_on_set_trades(qapp):
    """Summary bar updates when new trades are set."""
    widget = TradeListWidget()
    trades_a = [
        Trade(entry_time=pd.Timestamp("2026-01-01"), exit_time=pd.Timestamp("2026-01-02"),
              direction="long", entry_price=100.0, exit_price=110.0, pnl=10.0, exit_reason="signal"),
    ]
    widget.set_trades(trades_a)
    assert "10.00" in widget.lbl_summary.text()

    trades_b = [
        Trade(entry_time=pd.Timestamp("2026-01-01"), exit_time=pd.Timestamp("2026-01-02"),
              direction="short", entry_price=100.0, exit_price=90.0, pnl=-5.0, exit_reason="stop_loss"),
    ]
    widget.set_trades(trades_b)
    assert "-5.00" in widget.lbl_summary.text()


def test_summary_bar_cleared_on_empty(qapp):
    """Setting empty trades after having some resets the summary."""
    widget = TradeListWidget()
    trades = [
        Trade(entry_time=pd.Timestamp("2026-01-01"), exit_time=pd.Timestamp("2026-01-02"),
              direction="long", entry_price=100.0, exit_price=110.0, pnl=10.0, exit_reason="signal"),
    ]
    widget.set_trades(trades)
    assert "10.00" in widget.lbl_summary.text()

    widget.set_trades(None)
    assert "No trades" in widget.lbl_summary.text()


def test_compute_summary_method(qapp):
    """_compute_summary returns correct dict values."""
    widget = TradeListWidget()
    widget.trades = [
        Trade(entry_time=pd.Timestamp("2026-01-01"), exit_time=pd.Timestamp("2026-01-02"),
              direction="long", entry_price=100.0, exit_price=110.0, pnl=20.0, exit_reason="signal"),
        Trade(entry_time=pd.Timestamp("2026-01-01"), exit_time=pd.Timestamp("2026-01-02"),
              direction="long", entry_price=100.0, exit_price=95.0, pnl=-10.0, exit_reason="stop_loss"),
    ]
    summary = widget._compute_summary()
    assert summary["total"] == 2
    assert summary["net_pnl"] == pytest.approx(10.0)
    assert summary["wins"] == 1
    assert summary["losses"] == 1
    assert summary["avg_trade"] == pytest.approx(5.0)


def test_compute_summary_empty(qapp):
    """_compute_summary returns zeros for empty trade list."""
    widget = TradeListWidget()
    widget.trades = []
    summary = widget._compute_summary()
    assert summary["total"] == 0
    assert summary["net_pnl"] == 0.0
    assert summary["wins"] == 0
    assert summary["losses"] == 0
    assert summary["avg_trade"] == 0.0


def test_button_tooltips(qapp):
    """Prev/Next buttons and page size combo have tooltips."""
    widget = TradeListWidget()
    assert widget.btn_prev.toolTip() != ""
    assert widget.btn_next.toolTip() != ""
    assert widget.combo_page_size.toolTip() != ""


def test_summary_bar_has_lbl_summary_attribute(qapp):
    """Widget exposes lbl_summary for summary display."""
    widget = TradeListWidget()
    assert hasattr(widget, "lbl_summary")

