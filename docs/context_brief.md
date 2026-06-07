# Quant Strategy Lab — Compact Context Brief

> For Reasonix / Codex handoffs. Does **not** replace full-context review for risky tasks.
> Last updated: 2026-06-07

## Project Goal

Local-first PySide6 desktop platform for quant strategy generation, backtesting, validation, filtering, visualization, and reporting. **Research and backtesting only. No live trading.**

## Current Milestone

**v0.2 Alpha — validation expansion.** Tagged: `v0.2-alpha-validation-expansion` → `1a9c533`.

## Architecture Layers (top to bottom)

```
UI Layer (app/) → Application/Service Layer (app/services/) → Engine Layer (data_engine/, strategy_engine/, backtest_engine/, validation_engine/) → Repository Layer (repository/) → SQLite + File Storage
```

Engine code must not import PySide6. UI must not contain trading/strategy/backtest logic.

## Non-Negotiable Rules

| Rule | Source |
|---|---|
| No future leak in backtest | SOUL §3.2, AGENTS §6.2 |
| No OOS optimization | SOUL §3.3 |
| Every strategy must have provenance | SOUL §3.4 |
| Engine and UI must stay separate | SOUL §3.5 |
| Small verified steps | SOUL §3.6 |
| No live trading, no broker API, no GA/GP expansion, no full WF matrix, no PDF polish, no multi-user | PRD §6.1 |

## Completed Capabilities (v0.2 Alpha)

| Category | Capabilities |
|---|---|
| **Data** | Import, normalize, resample OHLCV. Session filter. Instrument profiles. Data quality checks. |
| **Strategy** | Four-block template (LE/LX/SE/SX). Formula conditions. GA population engine. GP tree engine. MTF conditions. Volume conditions. |
| **Backtest** | Event-driven, bar-by-bar, single-instrument. Stop-loss / take-profit. Session-end exit. Execution delay. Indicator cache. |
| **Validation** | IS/Val/OOS split. 5 stress tests (commission, slippage, one-bar delay, parameter perturbation, remove-best-N). Monte Carlo (missed-trade, slippage, combined). **Bootstrap MC with 95% CI**. Walk-forward + matrix + WFE. **IS/OOS stability gates**. **IS baseline quality precheck**. Elimination rules engine. |
| **Reports** | Markdown, HTML, PDF exports. Validation evidence in all formats. |
| **UI** | PySide6 main window. Dashboard, Data, Build, Validate, Results, Report, Settings pages. ValidationSummary widget. |
| **Infrastructure** | Agent queue workflow. Agent status script. 1103 tests, zero warnings. |

## Open Capabilities (Deferred)

- Price noise stress test (PRD §12.3)
- MC worst-case equity curve (PRD §12.4, deferred to v0.3)
- WF plotted equity charts (PRD §12.5)
- Precheck UI toggle (pipeline-level only)

## Key Directories

| Directory | Purpose |
|---|---|
| `app/` | PySide6 UI and services |
| `core/` | Shared domain models |
| `data_engine/` | Import, normalize, resample |
| `strategy_engine/` | Strategy templates, rules, GP, fitness |
| `backtest_engine/` | Event-driven backtest, metrics |
| `validation_engine/` | Stress, MC, WF, elimination |
| `reports/` | Markdown, HTML, PDF, code exporters |
| `repository/` | SQLite access |
| `docs/` | PRD, architecture, task_board, changelog, agent_reports, review_notes |
| `tests/` | All test files |
| `scripts/` | `agent_status.ps1` |

## Current Review Focus (June 2026)

- v0.2 cleanup / hardening closeout (058 series).
- Zero-warning verification accepted after 058D/058E.
- Post-cleanup milestone decision (v0.3 features vs. v1.0 archive design).
