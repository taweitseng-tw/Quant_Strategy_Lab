# Quant Strategy Lab

Quant Strategy Lab 是一套本地端桌面型量化交易策略生成、回測、驗證、篩選與報告平台。

## Required Reading

所有模型或開發者在修改專案前，必須依序閱讀：

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`

## Current Milestone

v0.2 Alpha — validation expansion release-ready

The v0.2 alpha validation expansion adds:

- **IS/OOS stability gates** — profit factor degradation, drawdown ratio, average trade degradation checks.
- **Remove-best-N trades stress test** — engine, pipeline, widget/report display, and UI controls.
- **Bootstrap Monte Carlo** — trade resampling with 95% confidence intervals, pipeline wiring, display surfaces, and UI controls.
- **Walk-forward per-window equity** — storage, widget summary, and markdown/HTML report tables.
- **Opt-in IS baseline quality precheck** — early-return gate with widget/report visibility.

All features are tested at engine, pipeline, display, and acceptance-smoke levels.

> This software is for research and backtesting purposes only. Backtested performance does not guarantee future results. Not financial advice. No live trading.

## Important Rule

不要一開始就做實盤下單、券商 API、完整 GA / GP、完整 Walk-forward Matrix。

---

## English Quickstart

### Prerequisites

- Python 3.11 or later
- Windows (Linux/macOS are not yet supported)
- Git

### Setup

```powershell
# Clone the repository
git clone <repo-url>
cd <repo-folder>

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install the project with dev dependencies
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

### Launch the Desktop Application

```powershell
.\.venv\Scripts\python.exe app/main.py
```

A window titled **Quant Strategy Lab** opens with navigation on the left
(Dashboard, Data, Build, Backtest, Validate, Results, Report, Settings).

### Quick Happy Path

1. **Create a project** — Click `New Project` in the toolbar, enter a name,
   and select a directory.
2. **Import sample data** — Go to the `Data` page and click `Import OHLCV Data
   File`. Navigate to `sample_data/sample_txf.csv` or `sample_data/sample_ohlcv.csv`.
3. **Run validation** — Go to the `Validate` page and click the toolbar `Run`
   button. The pipeline runs a split / backtest / stress / Monte Carlo /
   walk-forward / elimination sequence in the background.
4. **Inspect results** — Go to the `Results` page. The ranking table shows
   strategy fitness scores. The `Strategy Detail` tab shows rule blocks. The
   `Trade List` tab shows individual trades.
5. **Export a report** — Click `Export Report` in the toolbar to generate a
   Markdown or HTML report.

### Run Tests

```powershell
# Desktop startup and sample data workflow
.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py -q

# Full local suite
.\.venv\Scripts\python.exe -m pytest
```

### Troubleshooting

| Problem | Likely Cause | Solution |
|---|---|---|
| `PySide6` import error | Missing Qt runtime | Run `python -m pip install -e .[dev]` from your venv |
| Offscreen platform plugin missing | Qt platform plugin not bundled | Run the app normally on Windows instead of headless mode |
| `pip install -e .[dev]` fails | Old pip or missing build tools | Run `python -m pip install --upgrade pip` first |
| Application window does not appear | Missing display or X server (Linux/WSL) | Windows is the primary target; offscreen mode (`QT_QPA_PLATFORM=offscreen`) works on Windows |
| Validation pipeline fails | Dataset quality check failed | Re-import the sample file or check the Data page quality report |

### Known Limits

- **Windows only.** No Linux or macOS support.
- **No packaged installer.** Requires Python venv. A PyInstaller `--onedir` build
  is available via `scripts/build_package.ps1`.
- **No auto-update.** Rebuild from source to update.
- **No live trading.** This software is for research and backtesting only.
- **Not financial advice.** Backtested performance does not guarantee future results.

### Disclaimer

This software is for research and backtesting purposes only.
Backtested performance does not guarantee future results.
Not financial advice. No live trading.
