# Architecture

## Layer Diagram

```text
UI Layer
  ↓
Application / Service Layer
  ↓
Data / Strategy / Backtest / Validation Engines
  ↓
Repository Layer
  ↓
SQLite + File Storage
```

## Package Responsibilities

- `app/`: PySide6 desktop UI and reusable widgets.
- `core/`: shared domain models, schemas, and utilities.
- `data_engine/`: data import, normalization, resampling, session filters, and instrument profiles.
- `strategy_engine/`: strategy templates, rule blocks, parameter spaces, random/GP generation, formula parsing, and fitness logic.
- `backtest_engine/`: event-driven backtest, execution model, trade recording, multi-instrument scaling, and metrics.
- `validation_engine/`: IS / validation / OOS splits, stress tests, Monte Carlo, walk-forward matrices, and walk-forward efficiency (WFE).
- `repository/`: SQLite and file-storage access.
- `reports/`: Markdown, HTML, PDF, Excel, JSON, and pseudocode/Python/NinjaTrader exports.

## Data Flow

Imported OHLCV files should flow through the data engine for parsing, normalization, quality checks, and resampling before repository persistence or UI display.

## Strategy Flow

Strategies should be created from structured rule blocks and templates, then stored with provenance: seed, generator version, parameter ranges, dataset ID, instrument profile ID, build task ID, fitness config, and elimination config.

## Backtest Flow

Backtests should consume structured datasets, instrument profiles, strategy definitions, and execution assumptions, then produce structured trades, equity curve, drawdown curve, metrics, assumptions, and warnings.

## Validation Flow

Validation should evaluate strategies across IS / validation / OOS, stress tests, Monte Carlo, and walk-forward checks without mutating training results or optimizing on OOS data.

## Repository Rules

The repository layer owns database and file-storage reads/writes. UI widgets and engine modules should not write directly to SQLite tables.

## UI-Engine Boundary Rules

UI may call application/service APIs. Engine code must not import PySide6. Backtest, strategy generation, validation, and data processing logic must not live in UI widgets.

## Task 001 UI Shell Boundary

The initial PySide6 shell lives under `app/`:

- `app/main.py` starts the desktop application.
- `app/ui/main_window.py` owns the main window layout only.
- `app/widgets/log_panel.py` owns the bottom read-only log widget.

Task 001 placeholders do not import or execute data, strategy, backtest, validation, repository, or report logic. Future UI actions should call application/service APIs instead of placing engine logic inside widgets.
