# Task 045C2 — Formula Editor UI Integration Design

## 1. Overview
This document defines how the passive `FormulaConditionEditor` widget will be integrated into the Quant Strategy Lab application UI. The primary goal is to provide users a way to attach custom text-based conditions to strategies while strictly adhering to safety rules—preventing accidental mutation of ranked strategies or disruption of the `Results` page state.

## 2. Location & UI Integration
**Decision:** Modal Dialog triggered from the Results Page (`StrategyDetailWidget`).

**Justification:**
- `StrategyDetailWidget` already serves as the inspector for reading strategy logic.
- Adding an inline editor could accidentally imply direct, destructive editing of an existing ranked strategy.
- A modal explicitly signals an isolated action ("Add a custom condition to create a new variant").

**UI Elements to Add:**
1. **StrategyDetailWidget:**
   - Add a button `btn_add_condition` ("+ Add Custom Condition") next to the "Strategy Logic" section header.
   - The button should only be enabled if a strategy is currently selected and viewed.
2. **New Dialog (`FormulaConditionDialog`):**
   - A simple `QDialog`.
   - Contains a dropdown (`QComboBox`) for selecting the target logic block: `Long Entry`, `Long Exit`, `Short Entry`, `Short Exit`.
   - Contains the `FormulaConditionEditor` widget below the dropdown.
   - The dialog listens to the editor's `formula_accepted` signal.

## 3. Data Flow & State Management (The "Create-Copy" Pattern)
To satisfy the rule **"Do not mutate ranked strategies directly"**, the application will use a safe copy-and-import flow, heavily mirroring the existing JSON Import functionality.

**Step-by-Step Flow:**
1. User selects a strategy in the `RankingTable`. `StrategyDetailWidget` displays it.
2. User clicks "+ Add Custom Condition". `FormulaConditionDialog` opens.
3. User selects a target block (e.g., "Long Entry") and types a valid formula (e.g., `close > SMA(20)`).
4. User clicks "Apply" on the editor.
5. `FormulaConditionEditor` parses the text into a `StrategyBlock` (with 1 or more `Condition`s) and emits it.
6. `FormulaConditionDialog` catches this block and emits a custom signal: `condition_added(target_block_name, strategy_block)`.
7. `MainWindow` (which wires this dialog) catches the signal and performs the following:
   - Retrieves the currently selected `Strategy` from `self.ranked_data`.
   - **Deep copies** the strategy (`copy.deepcopy(strategy)`).
   - Appends the new conditions to the corresponding block in the copied strategy.
   - Modifies the strategy name (e.g., `[Imported] OriginalName (Custom)`).
   - Updates provenance to mark it as modified by the formula editor.
   - Appends the copied strategy to `self._imported_strategies`.
   - Calls `self._refresh_results_ranking()` to run a backtest on the new variant and re-rank the table.

## 4. Why this approach?
- **Zero Mutation:** The originally generated/ranked strategy is completely untouched.
- **Immediate Feedback:** The user immediately sees their new custom strategy evaluated and ranked against the others on the Results page.
- **Reusability:** It utilizes the existing `_imported_strategies` injection path built for Task 039.
- **Passivity:** `FormulaConditionEditor` remains completely unaware of `MainWindow` or `StrategyService`.

## 5. Required Test Plan (For Future Implementation)
When implementing this design, the following tests must be added to verify safety:

1. **`test_formula_dialog_emits_target_and_block`**:
   - Verify that the new `FormulaConditionDialog` correctly passes up the selected dropdown value and the `StrategyBlock`.

2. **`test_mainwindow_formula_import_creates_copy`**:
   - Mock the dialog acceptance in `MainWindow`.
   - Verify that the original strategy in `ranked_data` is NOT mutated.
   - Verify that `_imported_strategies` increases by 1.
   - Verify that the newly appended strategy has the new condition in the correct block.
   
3. **`test_mainwindow_formula_import_refreshes_ranking`**:
   - Verify that `_refresh_results_ranking()` is called, ensuring the new strategy is properly backtested and displayed.
