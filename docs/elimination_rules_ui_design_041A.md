# Custom Elimination Rules UI Design (Task 041A)

## 1. Goal
Design an interactive UI panel for users to configure Strategy Elimination thresholds (`EliminationConfig`) without modifying the underlying validation engine or allowing UI widgets to directly import engine data structures.

## 2. UI Layout and Passive Widget Design
A new passive widget, `EliminationConfigWidget`, will be created. It will focus purely on presenting configuration fields and emitting changes.

### Threshold Grouping
The fields from `EliminationConfig` will be split into two logical groups in the UI:
1. **Core Backtest Rules**
   - Minimum Total PnL (`min_total_pnl`)
   - Minimum Profit Factor (`min_profit_factor`)
   - Maximum Drawdown PnL (`max_drawdown_pnl`)
   - Minimum Avg Trade (`min_avg_trade`)
   - Minimum Trade Count (`min_trade_count`)
   - Minimum Win Rate (`min_win_rate`)
2. **Advanced / Validation Rules** (Optional)
   - Minimum OOS Total PnL (`min_oos_total_pnl`)
   - Minimum OOS Profit Factor (`min_oos_profit_factor`)
   - Minimum Stress Pass Rate (`min_stress_pass_rate`)
   - Minimum Monte Carlo 5% PnL (`min_monte_carlo_p05_pnl`)
   - Minimum Walk-Forward Pass Rate (`min_walk_forward_pass_rate`)
   - *Checkbox:* "Require optional validation data" (`require_optional`)

### Handling Disabled/None States
Since `EliminationConfig` uses `None` to indicate a disabled threshold, the UI will pair a `QCheckBox` (enable/disable) with a `QDoubleSpinBox` or `QSpinBox` (value) for each rule.
- If the checkbox is **unchecked**, the spinbox is disabled, and the resulting value is `None`.
- If the checkbox is **checked**, the spinbox is enabled, and the resulting value is the numeric input.

### Validation Rules for Inputs
- `min_trade_count`: Integer, Range: `[0, 10000]`.
- PnL metrics (`min_total_pnl`, `min_avg_trade`, etc.): Float, Range: `[-1000000.0, 1000000.0]`.
- `min_profit_factor`: Float, Range: `[0.0, 100.0]`.
- Rate metrics (`min_win_rate`, `min_stress_pass_rate`, `min_walk_forward_pass_rate`): Float, Range: `[0.0, 1.0]`, step `0.05`.
- `max_drawdown_pnl`: Float, Range: `[0.0, 1000000.0]`.

## 3. Service-Layer Update Flow (No Engine Coupling)
To maintain the strict separation of concerns, the widget will not import `EliminationConfig` from `validation_engine/elimination.py`.

1. **Widget Emits Dictionary:**
   Whenever a value or checkbox changes, `EliminationConfigWidget` constructs a standard Python `dict` mapping the snake_case parameter names to their current values (or `None`). It emits a PySide6 Signal:
   `config_changed = QtCore.Signal(dict)`

2. **MainWindow Orchestration:**
   `MainWindow` listens to `config_changed(config_dict)` from the widget.

3. **StrategyService Update:**
   We will add a new method to `StrategyService`: `update_elimination_config(config_dict: dict)`.
   When `MainWindow` receives the dict, it passes it to `StrategyService.update_elimination_config(config_dict)`.
   The `StrategyService` is responsible for importing `EliminationConfig`, unpacking the dictionary (`EliminationConfig(**config_dict)`), and assigning it to `self.elimination_config`.

This keeps the UI widget 100% passive and completely decoupled from engine domain models.

## 4. Default, Reset, and Clear All Actions
The widget will include a toolbar or button row with the following actions:
- **Apply Defaults:** Emits the `config_changed` signal using a hardcoded dictionary that matches `StrategyService.DEFAULT_ELIMINATION_CONFIG` (e.g., `{"min_trade_count": 5, "min_profit_factor": 0.5, "max_drawdown_pnl": 50000.0, "min_avg_trade": -500.0}`).
- **Clear All:** Unchecks every rule checkbox. The resulting dictionary contains entirely `None` values (except `require_optional=False`). This effectively disables all elimination filters.
- **Revert / Reset:** Reverts the UI to match the last applied configuration (passed down from `MainWindow` via a `set_config(config_dict)` method).

## 5. Test Plan
The following tests will be written during the implementation phase:

**UI Widget Tests (`tests/test_elimination_widget.py`):**
1. `test_elimination_widget_emits_dict_on_change`: Verifies checking a box and typing a value emits a correctly structured dictionary.
2. `test_elimination_widget_clear_all_emits_nones`: Verifies the "Clear All" action unchecks all boxes and emits a dict with `None` values.
3. `test_elimination_widget_apply_defaults`: Verifies the default button sets the predefined dictionary correctly.
4. `test_elimination_widget_set_config_updates_ui`: Verifies that passing a `dict` into the widget correctly toggles checkboxes and sets spinbox values.

**Service Integration Tests (`tests/test_strategy_service_elimination.py`):**
1. `test_strategy_service_update_elimination_config_from_dict`: Verifies that `update_elimination_config({"min_trade_count": 10})` correctly instantiates an `EliminationConfig` object inside the service.
2. `test_strategy_service_ignores_invalid_keys_in_dict`: Ensures safe handling if the UI passes unknown keys.
