# Desktop Evaluator Walkthrough - Tasks 271-276

Developer-evaluator walkthrough. This document does not claim production
readiness. It is a manual companion to the startup and sample-data smoke tests.

## Prerequisites

- Python 3.11+ virtual environment with project dependencies installed.
- Repository root is the working directory.
- No packaged installer is accepted yet; launch from the command line.
- This is research and backtesting software only. It is not financial advice.

## Step 1 - Launch The Application

```powershell
.\.venv\Scripts\python.exe app\main.py
```

Expected evidence:
- A desktop window opens with title `Quant Strategy Lab`.
- Default window size is 1280x800.
- Toolbar actions include `New Project`, `Open Project`, `Save`, `Run`,
  `Pause`, `Stop`, and `Export Report`.
- Left navigation pages from source are `Dashboard`, `Data`, `Build`,
  `Backtest`, `Validate`, `Results`, `Report`, and `Settings`.

Supporting tests:
- `test_app_main_imports_and_callable`
- `test_offscreen_main_window_construct_and_close`
- `test_subprocess_desktop_entrypoint_exits_cleanly`

## Step 2 - Create Or Open A Project

Use the toolbar:
- `New Project`
- `Open Project`

Expected evidence:
- A project folder is selected or created.
- The app keeps an active project service state.
- Project files should include `project.json`, `project.sqlite`, and `config/`
  after project creation.

Supporting test:
- `test_project_service_create_and_open_lifecycle`

## Step 3 - Import Sample OHLCV Data

Navigate to the `Data` page.

Use the verified button:
- `Import OHLCV Data File`

Suggested sample files:
- `sample_data/sample_ohlcv.csv`
- `sample_data/sample_txf.csv`

Expected evidence:
- Dataset status label updates with active dataset details.
- Data quality status is shown.
- Normalized columns are `datetime`, `open`, `high`, `low`, `close`, `volume`.
- Candlestick chart receives the normalized data.

Supporting tests:
- `test_sample_ohlcv_import_produces_normalized_data`
- `test_sample_txf_import_produces_normalized_data`

## Step 4 - Build Or Select A Strategy

Navigate to the `Build` page.

Verified source evidence:
- The Build page contains a `GABuildPanel`.
- GA/GP run buttons exist. Their visible labels include play icons, so verify
  the exact rendered text in the UI.

Expected evidence:
- GA or GP search progress appears in the Build panel.
- Generated strategies can appear in the `Results` page ranking table.

Supporting test:
- `test_full_research_pipeline_e2e`

## Step 5 - Run Backtest Or Validation

Navigate to the `Validate` page or use the toolbar `Run` action.

Expected evidence:
- Validation summary populates with split, stress, Monte Carlo, walk-forward,
  and elimination evidence when a valid strategy and dataset are available.
- Report export remains disabled until validation evidence is available.

Supporting tests:
- `test_full_research_pipeline_e2e`
- `test_sample_ohlcv_backtest_produces_structured_output`
- `test_sample_txf_backtest_produces_structured_output`

## Step 6 - Inspect Results

Navigate to the `Results` page.

Verified tabs:
- `Strategy Detail`
- `Equity Curve`
- `Trade List`
- `Parameter Heatmap`

Verified result actions:
- `Preview JSON Import`
- `Export Archive`
- `Export JSON`
- `Export Code`

Expected evidence:
- Ranking table contains evaluated strategies.
- Strategy detail panel shows selected strategy information.
- Equity curve and trade list are populated after a backtest.

Supporting test:
- `test_sample_ohlcv_backtest_produces_structured_output`

## Step 7 - Export Report

Use the toolbar action:
- `Export Report`

Expected evidence:
- A report is generated after validation/backtest evidence is available.
- Report content includes strategy name, total net profit, profit factor, total
  trades, and the required research-only financial safety notice.

Supporting test:
- `test_sample_workflow_produces_markdown_report`

## Quick Smoke Commands

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_sample_data_workflow_smoke.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_data_page_wiring.py tests/test_quality_checker.py tests/test_candlestick_chart.py -q
```

Expected:
- Startup smoke: 5 passed.
- Sample-data workflow smoke: 7 passed.
- Import UX and quality checker command is included for focused verification of import worker progress, quality warning details, session-aware gap detection, and chart slicing.

## Known Limits

- No live trading or broker API.
- No packaged installer yet.
- No visual regression suite yet.
- The sample OHLCV file is intentionally small.
- UI labels with icon prefixes should be visually verified in the running app.
- Hold artifacts are outside release scope unless explicitly accepted:
  `AGENT_LOOP_README.md`, `scripts/agent_loop.ps1`, and `tools/`.
