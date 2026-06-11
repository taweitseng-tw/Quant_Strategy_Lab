# Quant Strategy Lab — Compact Context Brief

> For Reasonix / Codex handoffs. Does **not** replace full-context review for risky tasks.
> Last updated: 2026-06-11 (v0.3.0-dev evaluator readiness closure)

## Project Goal

Local-first PySide6 desktop platform for quant strategy generation, backtesting, validation, filtering, visualization, and reporting. **Research and backtesting only. No live trading.**

## Current Milestone

**v0.3.0-dev — developer pre-release (Windows, local tag).** Tagged: `v0.3.0-dev` → `bd94e90`.

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
| **Validation** | IS/Val/OOS split. Stress tests including commission, slippage, one-bar delay, parameter perturbation, remove-best-N, and price-noise diagnostic. Monte Carlo (missed-trade, slippage, combined), bootstrap MC with 95% CI, and missed-trade MC worst-case trade-step equity evidence. Walk-forward + matrix + WFE. IS/OOS stability gates. IS baseline quality precheck. Elimination rules engine. |
| **Reports** | Markdown, HTML, PDF exports. Validation evidence includes price-noise details, WF equity tables, MC worst-case trade-step equity, and WFE. |
| **UI** | PySide6 main window. Dashboard, Data, Build, Validate, Results, Report, Settings pages. ValidationSummary widget with price-noise details, WF equity chart, MC worst-case equity chart, WFE line, and precheck controls. |
| **Infrastructure** | Agent queue workflow. Agent status script. Compact task board/changelog archives. Context-level reading protocol. |

## Open Capabilities / Current Gaps

- Large-file import UX hardening complete: background worker, progress stages, session-aware quality gap filtering, structured quality issues (Tasks 065A-065B + follow-up series 080A+).
- MC worst-case equity is trade-step evidence for missed-trade MC, not bar-by-bar equity and not all MC runner types.
- Context/document hygiene remains active: handoff docs must avoid stale claims.
- Data import is not currently considered blocked; focused data workflow tests pass.
- Release artifact zip exists at `release_artifacts/QuantStrategyLab-v0.3.0-dev-windows-onedir.zip` (`128,770,261` bytes / `122.8 MiB`, gitignored).
- Tag `v0.3.0-dev` is local only - not pushed to any remote.

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
| `docs/` | PRD, architecture, compact task_board/changelog, archives, agent_reports, review_notes |
| `tests/` | All test files |
| `scripts/` | `agent_status.ps1` |

## Current Review Focus (June 2026)

- v0.3.0-dev developer pre-release: desktop startup smoke, sample data workflow, archive preview contract, CI smoke pipeline, PyInstaller onedir packaging, large-file import UX with session-aware quality checks.
- Evaluator readiness closure: release zip exists (`128,770,261` bytes / `122.8 MiB`), tag is local, evaluator docs are updated, no upload/push performed.
- For Level 1/2 tasks, start from this brief plus current task-board/changelog sections.

## Context Efficiency Rules

- Do not paste or reload full `docs/PRD.md`, full `docs/changelog.md`, or archive files for low-risk work.
- Use `rg` to find older decisions in `docs/archive/`, then read only matching sections.
- Keep handoff and review packets compact; store long evidence in `docs/agent_reports/` when needed.
- Codex reviews should start from changed files, focused diffs, verification output, and reviewer focus.
- Use focused tests before full suites unless the task touches broad engine behavior, release acceptance, no-future-leak assumptions, or architecture contracts.
- Token savings must never weaken tests, architecture boundaries, no-future-leak review, or milestone acceptance.
