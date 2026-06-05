# Task 037A — Test Suite and UI Smoke Performance Audit

## 1. Slowest Tests Identified
Based on `pytest --durations=0`, the slowest tests in the suite are:
- `test_ga_e2e_flow.py::test_ga_e2e_flow` (~1.70s)
- `test_export_persistence_acceptance.py::test_export_persistence_smoke` (~1.61s)
- `test_active_dataset.py::test_main_window_mock_fallback_active_state` (~1.30s)
- `test_project_wiring.py::test_main_window_open_project_flow` (~1.10s)
- `test_active_dataset.py::test_new_open_project_clears_active_dataset` (~1.06s)
- Tests in `test_ga_fitness.py` and `test_ga_service.py` (~0.60s to 0.94s)

## 2. Repeated Expensive MainWindow Construction
**Identification:** `MainWindow()` is instantiated repeatedly across multiple GUI test modules, leading to accumulating delays.
- `tests/test_results_trade_list_wiring.py` (10 instances, ~0.4s – 0.6s each)
- `tests/test_project_wiring.py` (4 instances)
- `tests/test_active_dataset.py` (5 instances)
- `tests/test_python_export_ui_wiring.py` (4 instances)

**Root Cause:** During `MainWindow.__init__()`, it builds the "Results" page and automatically triggers `_refresh_results_ranking()`. If no real dataset is loaded, this method asks `StrategyService.get_ranked_strategies()` to generate mock data and run multiple mock backtests to populate the ranking table. Consequently, tests that just need an empty UI shell end up running 10+ mock backtests every time they construct a window.

## 3. GUI Tests that can be Safely Isolated or Optimized
1. **Mocking Initial Backtests:** Tests that immediately overwrite `window.ranked_data` (like those in `test_python_export_ui_wiring.py`) or simply check for UI widget presence don't need the real mock backtest results. These can be sped up by patching `StrategyService.get_ranked_strategies` to return `([], True)`.
2. **Fixture Reuse:** Modules like `test_results_trade_list_wiring.py` that do not mutate core engine state could share a `module`-scoped `MainWindow` fixture for read-only tests, isolating mutations to a few test boundaries.

## 4. Tiny Safe Test-Speed Fixes Implemented
- **Patch Applied:** I applied a tiny safe fix to `tests/test_python_export_ui_wiring.py`. Since every test in this file manually sets `window.ranked_data` anyway, the initial `StrategyService` backtest run was completely wasted effort. `StrategyService.get_ranked_strategies` is now patched out during `MainWindow` initialization in these specific tests, safely shaving off redundant test time without altering engine behavior or risking UI state leakage.
- Other modules were left untouched to prevent UI state pollution (as per the instruction to only implement safe, obvious fixes).

*No changes were made to strategy/backtest behavior, and no dependencies were added.*

## 5. Test Hygiene Rules (Task 037C)

To maintain a fast and reliable GUI test suite, adhere to the following rules:

1. **Safe to mock `StrategyService.get_ranked_strategies`:**
   - When a GUI test module focuses purely on project persistence (e.g., `test_project_wiring.py`), active dataset updates (e.g., `test_active_dataset.py`), or when the test manually overwrites `window.ranked_data` before asserting. This avoids the heavy mock backtest initialization loop in `MainWindow.__init__`.
2. **NOT safe to mock `StrategyService.get_ranked_strategies`:**
   - When testing the actual data flow from the StrategyService into the ranking table, equity curve, parameter heatmap, or trade list (e.g., `test_results_trade_list_wiring.py` or `test_results_heatmap_wiring.py`). These tests rely on the real mock backtest data to verify the UI.
3. **Resetting shared `MainWindow` fixtures:**
   - If a test module shares a `MainWindow` fixture, it must include an `autouse=True` fixture that explicitly resets any mutated UI state (e.g., `clearSelection()` or clearing table items). This guarantees isolated, deterministic test boundaries without repeatedly paying the window constructor cost.
4. **No skipping for speed:**
   - Tests must never bypass meaningful integration assertions simply to make the suite run faster. Determinism and correctness always take precedence over test speed.
