"""Tests for the passive EliminationConfigWidget — Task 041B."""

import sys
import pytest
from PySide6.QtWidgets import QApplication

from app.widgets.elimination_config_widget import EliminationConfigWidget


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Fixture to initialize a QApplication instance for GUI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def widget(qapp):
    """Fixture to provide a clean EliminationConfigWidget instance."""
    w = EliminationConfigWidget()
    return w


def test_elimination_config_widget_instantiates(widget):
    """Test that the widget can be instantiated headlessly."""
    assert widget is not None
    assert widget.windowTitle() == ""


def test_elimination_config_widget_default_dict_shape(widget):
    """Test that get_config_dict returns all expected keys."""
    cfg = widget.get_config_dict()
    expected_keys = {
        "min_total_pnl",
        "min_profit_factor",
        "max_drawdown_pnl",
        "min_avg_trade",
        "min_trade_count",
        "min_win_rate",
        "min_oos_total_pnl",
        "min_oos_profit_factor",
        "min_stress_pass_rate",
        "min_monte_carlo_p05_pnl",
        "min_walk_forward_pass_rate",
        "require_optional",
    }
    assert set(cfg.keys()) == expected_keys
    
    # By default, inputs are disabled so all metric keys should be None
    assert cfg["min_total_pnl"] is None
    assert cfg["min_profit_factor"] is None
    assert cfg["require_optional"] is False


def test_elimination_config_widget_disabled_rule_returns_none(widget):
    """Test that an unchecked checkbox causes the field to return None."""
    # Ensure it's unchecked
    cb, spin = widget._inputs["min_total_pnl"]
    cb.setChecked(False)
    
    cfg = widget.get_config_dict()
    assert cfg["min_total_pnl"] is None


def test_elimination_config_widget_enabled_rule_returns_numeric(widget):
    """Test that a checked checkbox returns the spinbox's numeric value."""
    cb, spin = widget._inputs["min_total_pnl"]
    cb.setChecked(True)
    spin.setValue(1234.5)
    
    cfg = widget.get_config_dict()
    assert cfg["min_total_pnl"] == 1234.5


def test_elimination_config_widget_set_config_dict_updates_controls(widget):
    """Test that set_config_dict updates the checkboxes and spinboxes."""
    new_cfg = {
        "min_profit_factor": 1.5,
        "max_drawdown_pnl": 2000.0,
        "min_trade_count": None,  # explicit None
        "require_optional": True,
    }
    
    emitted = []
    widget.config_changed.connect(lambda d: emitted.append(d))
    
    widget.set_config_dict(new_cfg)
    
    cfg = widget.get_config_dict()
    
    assert cfg["min_profit_factor"] == 1.5
    assert cfg["max_drawdown_pnl"] == 2000.0
    assert cfg["min_trade_count"] is None
    assert cfg["require_optional"] is True
    
    # Check underlying Qt states
    pf_cb, pf_spin = widget._inputs["min_profit_factor"]
    assert pf_cb.isChecked() is True
    assert pf_spin.value() == 1.5
    
    tc_cb, tc_spin = widget._inputs["min_trade_count"]
    assert tc_cb.isChecked() is False
    
    assert len(emitted) == 1
    assert emitted[0]["min_profit_factor"] == 1.5


def test_elimination_config_widget_set_partial_dict_safe(widget):
    """Test that setting a partial dict leaves unmentioned keys alone."""
    widget.set_config_dict({"min_total_pnl": 100.0, "min_profit_factor": 1.2})
    
    widget.set_config_dict({"min_profit_factor": 2.0})
    
    cfg = widget.get_config_dict()
    # min_profit_factor was updated
    assert cfg["min_profit_factor"] == 2.0
    # min_total_pnl remains unchanged from the first call
    assert cfg["min_total_pnl"] == 100.0
    # min_win_rate (never set) remains None
    assert cfg["min_win_rate"] is None


def test_elimination_config_widget_clear_all(widget):
    """Test that Clear All sets everything to None."""
    # First set some values
    widget.set_config_dict({"min_total_pnl": 1000.0, "require_optional": True})
    
    emitted = []
    widget.config_changed.connect(lambda d: emitted.append(d))
    
    widget.btn_clear.click()
        
    cfg = widget.get_config_dict()
    
    # Everything should be None / False
    for k, v in cfg.items():
        if k == "require_optional":
            assert v is False
        else:
            assert v is None
            
    assert len(emitted) == 1


def test_elimination_config_widget_apply_defaults(widget):
    """Test that Apply Defaults loads the fallback conservative dictionary."""
    emitted = []
    widget.config_changed.connect(lambda d: emitted.append(d))
    
    widget.btn_defaults.click()
        
    cfg = widget.get_config_dict()
    
    assert cfg["min_trade_count"] == 5
    assert cfg["min_profit_factor"] == 0.5
    assert cfg["max_drawdown_pnl"] == 50000.0
    assert cfg["min_avg_trade"] == -500.0
    
    # Others remain None
    assert cfg["min_total_pnl"] is None
    
    assert len(emitted) == 1


def test_elimination_config_widget_emits_config_changed(widget):
    """Test that changing an input via UI emits config_changed with the new dict."""
    cb, spin = widget._inputs["min_win_rate"]
    
    emitted = []
    widget.config_changed.connect(lambda d: emitted.append(d))
    
    cb.setChecked(True)
        
    assert len(emitted) == 1
    assert emitted[0]["min_win_rate"] == 0.0  # default for spinbox when checked
    
    spin.setValue(0.55)
        
    assert len(emitted) == 2
    assert emitted[1]["min_win_rate"] == 0.55


def test_elimination_config_widget_has_no_validation_engine_import():
    """Verify that the widget file does not import validation_engine."""
    with open("app/widgets/elimination_config_widget.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "import validation_engine" not in content, "Widget must not import from validation_engine."
    assert "from validation_engine" not in content, "Widget must not import from validation_engine."
