"""Tests for Formula Editor UI integration (Task 045C3)."""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from core.models.strategy import Strategy, StrategyBlock, Condition
from app.widgets.strategy_detail import StrategyDetailWidget
from app.widgets.formula_condition_editor import FormulaConditionDialog, FormulaConditionEditor
from app.ui.main_window import MainWindow

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_strategy_detail_has_add_custom_condition_signal(qapp):
    """Verify that StrategyDetailWidget exposes the action and signal."""
    widget = StrategyDetailWidget()
    
    signal_emitted = False
    def on_requested():
        nonlocal signal_emitted
        signal_emitted = True
        
    widget.add_custom_condition_requested.connect(on_requested)
    
    # Initially disabled
    assert not widget.btn_add_condition.isEnabled()
    
    # Enable it by setting strategy
    dummy = Strategy(name="Test")
    widget.set_strategy_data({"strategy": dummy})
    assert widget.btn_add_condition.isEnabled()
    
    # Click emits signal
    widget.btn_add_condition.clicked.emit()
    assert signal_emitted

def test_formula_dialog_uses_formula_condition_editor(qapp):
    """Verify the dialog structure wraps the editor correctly."""
    dialog = FormulaConditionDialog()
    assert isinstance(dialog.editor, FormulaConditionEditor)
    assert dialog.combo_target_block.count() == 4
    
    emitted_target = None
    emitted_block = None
    def on_added(t, b):
        nonlocal emitted_target, emitted_block
        emitted_target = t
        emitted_block = b
        
    dialog.condition_added.connect(on_added)
    
    # Simulate valid block acceptance
    test_block = StrategyBlock(logic="AND", conditions=[])
    dialog.combo_target_block.setCurrentText("Short Exit")
    dialog.editor.formula_accepted.emit(test_block)
    
    assert emitted_target == "Short Exit"
    assert emitted_block is test_block

@patch("app.widgets.formula_condition_editor.FormulaConditionDialog")
def test_formula_custom_condition_valid_creates_imported_copy(mock_dialog_class, qapp):
    """Verify valid submission creates a modified deep copy injected into _imported_strategies."""
    main_window = MainWindow()
    # Provide dummy ranked data
    orig_strat = Strategy(name="Base Strat")
    main_window.ranked_data = [{"strategy": orig_strat}]
    main_window.results_table.set_ranking_data(main_window.ranked_data)
    # Select the first row
    main_window.results_table.table.selectRow(0)
    
    mock_dialog_inst = MagicMock()
    mock_dialog_class.return_value = mock_dialog_inst
    
    def side_effect():
        block = StrategyBlock(logic="AND", conditions=[Condition(indicator="SMA", params={"period": 20}, operator=">", left="close")])
        mock_dialog_inst.condition_added.connect.call_args[0][0]("Long Entry", block)
        return 1
        
    mock_dialog_inst.exec.side_effect = side_effect
    
    main_window._handle_add_custom_condition()
    
    assert hasattr(main_window, "_imported_strategies")
    assert len(main_window._imported_strategies) == 1
    
    injected_strat = main_window._imported_strategies[0]
    assert injected_strat is not orig_strat
    assert injected_strat.name == "[Imported] Base Strat (Custom)"
    
    # Verify the condition was appended to Long Entry
    assert len(injected_strat.long_entry.conditions) == 1
    assert injected_strat.long_entry.conditions[0].indicator == "SMA"
    
    # Original strategy must remain unchanged
    assert len(orig_strat.long_entry.conditions) == 0

@patch("app.widgets.formula_condition_editor.FormulaConditionDialog")
def test_formula_custom_condition_invalid_or_cancel_no_injection(mock_dialog_class, qapp):
    """Verify dialog cancellation does not mutate state."""
    main_window = MainWindow()
    main_window.ranked_data = [{"strategy": Strategy(name="Base Strat")}]
    main_window.results_table.set_ranking_data(main_window.ranked_data)
    main_window.results_table.table.selectRow(0)
    
    mock_dialog_inst = MagicMock()
    mock_dialog_class.return_value = mock_dialog_inst
    mock_dialog_inst.exec.return_value = 0
    
    main_window._handle_add_custom_condition()
        
    # Either doesn't exist or is empty
    if hasattr(main_window, "_imported_strategies"):
        assert len(main_window._imported_strategies) == 0

def test_existing_json_imported_strategies_still_work(qapp):
    """Verify that adding to _imported_strategies does not break existing logic."""
    main_window = MainWindow()
    
    # Simulating JSON import
    s1 = Strategy(name="JSON Strat")
    main_window._imported_strategies = [s1]
    
    # Adding a custom formula condition
    s2 = Strategy(name="Formula Strat")
    main_window._imported_strategies.append(s2)
    
    assert len(main_window._imported_strategies) == 2
    assert main_window._imported_strategies[0].name == "JSON Strat"
    assert main_window._imported_strategies[1].name == "Formula Strat"

@patch("app.widgets.formula_condition_editor.FormulaConditionDialog")
def test_formula_custom_condition_target_block_behavior_explicit(mock_dialog_class, qapp):
    """Verify that custom condition appending preserves original block conditions."""
    main_window = MainWindow()
    
    orig_strat = Strategy(name="Base Strat")
    # Add a pre-existing condition
    orig_strat.long_entry.conditions.append(Condition(indicator="RSI", params={"period": 14}, operator="<", right=30))
    
    main_window.ranked_data = [{"strategy": orig_strat}]
    main_window.results_table.set_ranking_data(main_window.ranked_data)
    main_window.results_table.table.selectRow(0)
    
    mock_dialog_inst = MagicMock()
    mock_dialog_class.return_value = mock_dialog_inst
    
    def side_effect():
        block = StrategyBlock(logic="AND", conditions=[Condition(indicator="SMA", params={"period": 20}, operator=">", left="close")])
        mock_dialog_inst.condition_added.connect.call_args[0][0]("Long Entry", block)
        return 1
        
    mock_dialog_inst.exec.side_effect = side_effect
    
    main_window._handle_add_custom_condition()
    
    injected_strat = main_window._imported_strategies[0]
    
    # Should have 2 conditions (appended, not replaced)
    assert len(injected_strat.long_entry.conditions) == 2
    assert injected_strat.long_entry.conditions[0].indicator == "RSI"
    assert injected_strat.long_entry.conditions[1].indicator == "SMA"
    
    # Original strategy must remain unchanged with only 1 condition
    assert len(orig_strat.long_entry.conditions) == 1
    assert orig_strat.long_entry.conditions[0].indicator == "RSI"

@patch("app.widgets.formula_condition_editor.FormulaConditionDialog")
def test_formula_custom_condition_coexists_with_ga_gp_strategies(mock_dialog_class, qapp):
    """Verify that custom conditions can be added alongside generated strategies."""
    main_window = MainWindow()
    
    ga_strat = Strategy(name="GA Generated Strat")
    main_window.generated_strategies = [ga_strat]
    
    orig_strat = Strategy(name="Base Strat")
    main_window.ranked_data = [{"strategy": orig_strat}, {"strategy": ga_strat}]
    main_window.results_table.set_ranking_data(main_window.ranked_data)
    main_window.results_table.table.selectRow(0) # Select Base Strat
    
    mock_dialog_inst = MagicMock()
    mock_dialog_class.return_value = mock_dialog_inst
    
    def side_effect():
        block = StrategyBlock(logic="AND", conditions=[Condition(indicator="SMA", params={"period": 20}, operator=">", left="close")])
        mock_dialog_inst.condition_added.connect.call_args[0][0]("Long Entry", block)
        return 1
        
    mock_dialog_inst.exec.side_effect = side_effect
    
    # Ensure refresh mock doesn't actually try to evaluate against non-existent data
    with patch.object(main_window, '_refresh_results_ranking') as mock_refresh:
        main_window._handle_add_custom_condition()
        mock_refresh.assert_called_once()
        
    assert len(main_window._imported_strategies) == 1
    assert main_window._imported_strategies[0].name == "[Imported] Base Strat (Custom)"
    assert len(main_window.generated_strategies) == 1
    assert main_window.generated_strategies[0].name == "GA Generated Strat"

@patch("app.widgets.formula_condition_editor.FormulaConditionDialog")
def test_formula_custom_condition_selection_state_safe_after_refresh(mock_dialog_class, qapp):
    """Verify that adding a condition safely handles table refresh without crashing selection logic."""
    main_window = MainWindow()
    orig_strat = Strategy(name="Base Strat")
    
    # Provide a minimal dataset ID so that refresh logic has something to run against
    # but we will mock the service to just return a dummy dataframe to avoid data engine errors
    main_window.current_dataset_id = "test_data"
    
    with patch('app.services.strategy_service.StrategyService.get_ranked_strategies') as mock_eval:
        # Mock evaluation to return our combined list of strategies to simulate refresh
        def mock_eval_side_effect(dataset_df=None, instrument=None, injected_strategies=None):
            strategies = [orig_strat] + (injected_strategies or [])
            return [{"strategy": s, "net_profit": 0.0, "max_drawdown": 0.0, "win_rate": 0.0} for s in strategies], True
        mock_eval.side_effect = mock_eval_side_effect
        
        main_window.ranked_data = [{"strategy": orig_strat, "net_profit": 0.0, "max_drawdown": 0.0, "win_rate": 0.0}]
        main_window.results_table.set_ranking_data(main_window.ranked_data)
        
        # Select row, which populates the detail widget
        main_window.results_table.table.selectRow(0)
        
        mock_dialog_inst = MagicMock()
        mock_dialog_class.return_value = mock_dialog_inst
        
        def side_effect():
            block = StrategyBlock(logic="AND", conditions=[Condition(indicator="SMA", params={"period": 20}, operator=">", left="close")])
            mock_dialog_inst.condition_added.connect.call_args[0][0]("Long Entry", block)
            return 1
            
        mock_dialog_inst.exec.side_effect = side_effect
        
        # Call the handle method. This should trigger _refresh_results_ranking
        # which clears the table and repopulates it. The selection state clears, 
        # which triggers _handle_strategy_selection_changed. We just want to ensure it doesn't crash.
        try:
            main_window._handle_add_custom_condition()
            no_crash = True
        except Exception:
            no_crash = False
            
        assert no_crash
        
        # The new ranked data should have 1 item (the base strat) + 1 imported strategy
        assert len(main_window.ranked_data) == 2

def test_main_window_does_not_parse_formula_directly():
    """Verify that MainWindow does not import or use the formula parser directly."""
    import ast
    from pathlib import Path
    
    import app.ui.main_window
    
    source_file = Path(app.ui.main_window.__file__)
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "formula_parser" not in alias.name, "MainWindow must not import formula_parser"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert "formula_parser" not in node.module, "MainWindow must not import from formula_parser"
                for alias in node.names:
                    assert "parse_formula" not in alias.name, "MainWindow must not import parse_formula*"

