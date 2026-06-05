"""Tests for the FormulaConditionEditor widget."""

import sys
import pytest
from PySide6.QtWidgets import QApplication

from app.widgets.formula_condition_editor import FormulaConditionEditor
from core.models.strategy import StrategyBlock


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Fixture to initialize a QApplication instance for GUI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def formula_editor(qapp):
    """Fixture providing a FormulaConditionEditor instance."""
    widget = FormulaConditionEditor()
    return widget


def test_formula_condition_editor_instantiates(formula_editor):
    """Test that the widget instantiates headlessly."""
    assert formula_editor is not None
    assert formula_editor.le_formula.placeholderText() != ""
    assert not formula_editor.btn_apply.isEnabled()


def test_formula_condition_editor_empty_invalid(formula_editor):
    """Test that an empty formula is invalid."""
    formula_editor.clear()
    assert not formula_editor.btn_apply.isEnabled()
    assert "Enter a formula." in formula_editor.lbl_status.text()


def test_formula_condition_editor_valid_formula_enables_apply(formula_editor):
    """Test that a valid formula enables the Apply button."""
    formula_editor.set_formula("close > SMA(20)")
    assert formula_editor.btn_apply.isEnabled()
    assert "Valid formula" in formula_editor.lbl_status.text()


def test_formula_condition_editor_invalid_formula_disables_apply(formula_editor):
    """Test that an invalid formula disables the Apply button and shows an error."""
    formula_editor.set_formula("close > SMA(0)")
    assert not formula_editor.btn_apply.isEnabled()
    assert "Error" in formula_editor.lbl_status.text()
    
    formula_editor.set_formula("invalid garbage")
    assert not formula_editor.btn_apply.isEnabled()
    assert "Error" in formula_editor.lbl_status.text()


def test_formula_condition_editor_preview_shows_logic_and_count(formula_editor):
    """Test that the preview label shows logic and condition count."""
    formula_editor.set_formula("close > SMA(20) AND RSI(14) > 70")
    assert formula_editor.btn_apply.isEnabled()
    preview_text = formula_editor.lbl_preview.text()
    assert "2 condition(s)" in preview_text
    assert "AND" in preview_text


def test_formula_editor_valid_apply_emits_once(formula_editor):
    """Test that clicking apply with a valid formula emits the strategy block."""
    emitted = []
    formula_editor.formula_accepted.connect(lambda b: emitted.append(b))
    
    formula_editor.set_formula("RSI(14) > 70")
    formula_editor.btn_apply.click()
        
    assert len(emitted) == 1
    block = emitted[0]
    assert isinstance(block, StrategyBlock)
    assert len(block.conditions) == 1
    assert block.conditions[0].indicator == "RSI"


def test_formula_editor_invalid_apply_emits_zero(formula_editor):
    """Test that an invalid formula does not emit when apply is clicked."""
    emitted = []
    formula_editor.formula_accepted.connect(lambda b: emitted.append(b))
    
    formula_editor.set_formula("invalid garbage")
    formula_editor._on_apply_clicked()
    
    assert len(emitted) == 0


def test_formula_condition_editor_set_formula_updates_state(formula_editor):
    """Test that set_formula programmatic updates correctly trigger validation."""
    formula_editor.set_formula("close > SMA(20)")
    assert formula_editor.get_formula() == "close > SMA(20)"
    assert formula_editor.btn_apply.isEnabled()


def test_formula_editor_set_formula_valid_then_invalid_state_transition(formula_editor):
    """Test transitioning from valid state to invalid state updates UI appropriately."""
    formula_editor.set_formula("close > SMA(20)")
    assert formula_editor.btn_apply.isEnabled()
    assert "Valid" in formula_editor.lbl_status.text()
    
    formula_editor.set_formula("close > SMA(-5)")
    assert not formula_editor.btn_apply.isEnabled()
    assert "Error" in formula_editor.lbl_status.text()
    assert formula_editor._current_block is None


def test_formula_editor_clear_after_valid_formula_resets_state(formula_editor):
    """Test that clear resets the state to invalid and empty."""
    formula_editor.set_formula("close > SMA(20)")
    assert formula_editor.btn_apply.isEnabled()
    
    formula_editor.clear()
    assert formula_editor.get_formula() == ""
    assert not formula_editor.btn_apply.isEnabled()


def test_formula_editor_parser_error_message_visible(formula_editor):
    """Test that parser error messages are propagated to the status label."""
    formula_editor.set_formula("MACD(12,26,9) > ")
    assert not formula_editor.btn_apply.isEnabled()
    # The parser throws FormulaParseError for unsupported syntax
    assert "Error: Unsupported condition syntax" in formula_editor.lbl_status.text()


def test_formula_condition_editor_source_has_no_eval_exec():
    """Verify the widget source itself does not use eval or exec."""
    import ast
    from pathlib import Path
    
    import app.widgets.formula_condition_editor
    
    source_file = Path(app.widgets.formula_condition_editor.__file__)
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in ["eval", "exec", "compile"], f"Found forbidden {node.func.id}() call"


def test_formula_editor_source_has_no_mainwindow_or_strategyservice_import():
    """Verify that the widget file does not import validation_engine, MainWindow, or StrategyService."""
    with open("app/widgets/formula_condition_editor.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "MainWindow" not in content, "Widget must not import MainWindow."
    assert "StrategyService" not in content, "Widget must not import StrategyService."
    assert "validation_engine" not in content, "Widget must not import validation_engine."
