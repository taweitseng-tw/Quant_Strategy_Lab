# Desktop Workflow and Chart/Table Reliability Design - Tasks 517-522

Design document. No production code changed in this design round.

Date: 2026-06-11

---

## 1. Desktop Workflow Audit

The desktop application (PySide6) operates on a layered architecture: the GUI (`main_window.py`) communicates with services (`DataService`, `StrategyService`, `ProjectService`, `InstrumentService`), which interact with engines and repositories.

The typical desktop workflow consists of:
1. **Launch**: Application boots. If no active project is found, the main window loads standard mock data in the candlestick chart and ranking table for immediate visual feedback.
2. **Project Creation/Open**: User creates a new project or opens an existing one. This sets paths in database managers and instrument services, and resets the active dataset status to "None loaded".
3. **Dataset Import**: User triggers an import of an OHLCV CSV/TXT file. A background `ImportWorker` thread parses, normalizes, and validates the file. Upon success, the DataFrame is loaded into memory, and the candlestick chart is updated.
4. **Validation Pipeline Run**: The user runs the validation pipeline, which executes split-sample testing, backtests, Monte Carlo stress tests, and walk-forward efficiency checks.
5. **Strategy Results & Charting**: The strategy service ranks strategies and displays them in the results table. Selecting a strategy updates the subordinate widgets (equity curve chart, trade list, strategy detail).

---

## 2. Identified Reliability Gaps

### 2.1 Chart/Table Reset State Leak (High Priority)
- **Gaps**:
  - When a user closes a project, opens a new project, or when a dataset import fails, the UI state resets (status label shows "None loaded"), but the `CandlestickChart` widget (`self.data_chart`) is **not** cleared. It continues to display the previously loaded dataset's chart.
  - This visual mismatch masks the active data state and leaks historical charts across projects.
- **Risk**: User confusion and potential misattribution of strategy backtests to wrong datasets.

### 2.2 Table Memory & Performance Bloat (Large Data)
- **Gaps**:
  - The `CandlestickChart` has a tail-2000 slice guard to prevent pyqtgraph rendering lag.
  - The `RankingTable` has **no limit** on row population. If a user imports a strategy list or runs a generation task that yields 5,000+ strategies, the main window will attempt to construct 5,000+ rows of `QTableWidgetItem` objects (with color brushes, custom fonts, alignments, and tooltips) synchronously on the Qt Main Thread.
- **Risk**: Blocking the main event loop, causing long freezes (several seconds), unresponsive window warnings, or application OOM crashes.

### 2.3 Exception Safety on Empty/Missing Datasets
- **Gaps**:
  - If a dataset fails parsing/normalizing, `self._loaded_dataset` is set to `None`. However, downstream functions like `_refresh_results_ranking` or `_handle_run` may access fields of `self._loaded_dataset` without strict null guards.
- **Risk**: Null pointer exceptions causing abrupt crashes when attempting strategy backtests.

---

## 3. UI-Service Boundary Risks

### 3.1 Synchronous Main Thread Blocks (Validation Pipeline)
- **Gaps**:
  - The `ImportWorker` correctly runs in a background `QThread`.
  - However, the validation pipeline (`run_validation_pipeline` inside `_handle_run`) runs **synchronously on the Qt Main Thread**. A full validation run with Monte Carlo, WFE, and price-noise stress settings can take long enough to visibly block the interface.
- **Risk**: The entire desktop interface freezes during validation. The user cannot cancel, window updates stop, and the OS may flag the app as crashed.
- **Mitigation (Architecture-Safe)**: While full multi-threading refactoring for validation is out of scope for a quick implementation slice, we must add a busy cursor and disable interactive elements during execution, and prepare a worker design for the next milestone.

### 3.2 Direct Database/Service Calls without Try-Except Boundaries
- **Gaps**:
  - UI callbacks perform direct database queries via services, such as loading persisted best strategies, without consistent safety try-except boundaries.
- **Risk**: Any database locking or disk write failure during these UI actions crashes the application.

---

## 4. Proposed Hardening Decisions (Tasks 523-528)

### 4.1 Implement `clear()` in Candlestick Chart and Reuse Existing Equity Clear
- Add a `clear()` method to `CandlestickChart`.
- Keep the existing `EquityCurveChart.clear()` method and only extend it if tests show a missing reset state.
- Calling `CandlestickChart.clear()` must clear the `CandlestickItem`, reset `is_mock_data`, clear the pyqtgraph plot item, and update titles to an empty state.
- Call `self.data_chart.clear()` during:
  - Project creation (`_handle_new_project`)
  - Project open (`_handle_open_project`)
  - Import failures (`_on_import_failure`)

### 4.2 Ranking Table Row Limit Guardrail
- Impose a strict maximum row limit of **500 rows** in `RankingTable.set_ranking_data`.
- If the ranked list exceeds 500 entries, truncate it to the top 500 (sorted by fitness) and append a status label suffix: `(Displaying top 500 of [N] strategies)`.
- This keeps synchronous table rendering bounded. Do not claim a fixed render-time target without local measurement.

### 4.3 Busy Indicators for Validation Pipeline
- Wrap `_handle_run` with cursor override: `QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)`.
- Use a try-finally block to ensure `QApplication.restoreOverrideCursor()` is always called, preventing permanent UI lockups on exceptions.

---

## 5. Proposed Scope for Tasks 523-528

### 5.1 Files to Modify
- `app/widgets/candlestick_chart.py`: Add `clear()` method and check for empty data.
- `app/widgets/ranking_table.py`: Implement the 500-row limit guardrail.
- `app/ui/main_window.py`: Integrate `clear()` calls, cursor overrides, and narrow service exception guards.
- `docs/task_board.md` and `docs/changelog.md`

### 5.2 Required Tests
- `test_candlestick_widget_clear`: asserts that calling `clear()` resets chart data and is_mock flags.
- `test_ranking_table_row_limit`: asserts that population with 1,000 rows limits rendering to exactly 500 rows and updates the status label.
- `test_project_change_clears_data_chart`: asserts that new/open project reset paths clear the candlestick chart.
- `test_handle_run_restores_wait_cursor_on_exception`: asserts the wait cursor is restored via `finally` when validation raises.
