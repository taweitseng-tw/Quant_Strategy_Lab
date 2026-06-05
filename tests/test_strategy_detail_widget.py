"""Tests for the StrategyDetailWidget."""

import pytest
from PySide6.QtWidgets import QApplication
from app.widgets.strategy_detail import StrategyDetailWidget
from core.models.strategy import Strategy, StrategyBlock, Condition

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_empty_state(qapp):
    widget = StrategyDetailWidget()
    assert "No Strategy Selected" in widget.lbl_name.text()
    assert "Fitness: -" in widget.lbl_fitness.text()
    assert widget.txt_blocks.toPlainText() == ""

def test_populate_with_strategy(qapp):
    strat = Strategy(
        name="Test Strat",
        long_entry=StrategyBlock(conditions=[Condition(indicator="SMA", params={"period": 10}, operator=">")])
    )
    ranked_entry = {
        "strategy": strat,
        "fitness": 1.234,
        "metrics": {"total_pnl": 500.5, "profit_factor": 1.5, "total_trades": 10},
        "provenance": {"generator_version": "v-test", "random_seed": 42, "source_type": "random"},
    }
    
    widget = StrategyDetailWidget()
    widget.set_strategy_data(ranked_entry)
    
    assert widget.lbl_name.text() == "Test Strat"
    assert "1.234" in widget.lbl_fitness.text()
    assert "500.5" in widget.lbl_pnl.text()
    assert "1.5" in widget.lbl_pf.text()
    assert "10" in widget.lbl_trades.text()
    
    html = widget.txt_blocks.toHtml()
    assert "Long Entry" in html
    assert "SMA" in html
    assert "period=10" in html
    assert "0.0" not in html
    assert "Source: v-test" in widget.lbl_provenance.text()
    assert "Seed: 42" in widget.lbl_provenance.text()

def test_eliminated_state(qapp):
    strat = Strategy(name="Eliminated Strat")
    ranked_entry = {
        "strategy": strat,
        "elimination_status": "eliminated",
        "elimination_passed": False,
        "elimination_failed_rules": ["min_trades"]
    }
    
    widget = StrategyDetailWidget()
    widget.set_strategy_data(ranked_entry)
    assert "ELIMINATED" in widget.lbl_status.text()
    assert "min_trades" in widget.lbl_status.text()


def test_threshold_conditions_are_displayed_without_fake_sma_threshold(qapp):
    strat = Strategy(
        name="Threshold Strat",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="RSI", params={"period": 14}, operator="<", right=30.0),
        ]),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 20}, operator=">"),
        ]),
    )

    widget = StrategyDetailWidget()
    widget.set_strategy_data({"strategy": strat, "metrics": {}})
    text = widget.txt_blocks.toPlainText()

    assert "RSI(period=14) < 30.0" in text
    assert "close > SMA(period=20)" in text
    assert "SMA(period=20) > 0.0" not in text


def test_empty_blocks_do_not_crash(qapp):
    widget = StrategyDetailWidget()
    widget.set_strategy_data({"strategy": Strategy(name="Empty Blocks")})

    assert "Empty Blocks" in widget.lbl_name.text()
    assert "<No conditions>" in widget.txt_blocks.toPlainText()
