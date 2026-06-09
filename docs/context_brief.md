# Quant Strategy Lab — Compact Context Brief

> For Reasonix / Codex handoffs. Does **not** replace full-context review for risky tasks.
> Last updated: 2026-06-09 (Codex review efficiency guardrails)

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
| **Validation** | IS/Val/OOS split. Stress tests including commission, slippage, one-bar delay, parameter perturbation, remove-best-N, and price-noise diagnostic. Monte Carlo (missed-trade, slippage, combined), bootstrap MC with 95% CI, and missed-trade MC worst-case trade-step equity evidence. Walk-forward + matrix + WFE. IS/OOS stability gates. IS baseline quality precheck. Elimination rules engine. |
| **Reports** | Markdown, HTML, PDF exports. Validation evidence includes price-noise details, WF equity tables, MC worst-case trade-step equity, and WFE. |
| **UI** | PySide6 main window. Dashboard, Data, Build, Validate, Results, Report, Settings pages. ValidationSummary widget with price-noise details, WF equity chart, MC worst-case equity chart, WFE line, and precheck controls. |
| **Infrastructure** | Agent queue workflow. Agent status script. Compact task board/changelog archives. Context-level reading protocol. |

## Open Capabilities / Current Gaps

- Next post-v0.2 engineering task is not yet selected. Do not reassign Task 065A or 065B; both are complete.
- MC worst-case equity is trade-step evidence for missed-trade MC, not bar-by-bar equity and not all MC runner types.
- Context/document hygiene remains active: handoff docs must avoid stale claims.
- Data import is not currently considered blocked; focused data workflow tests pass and Tasks 065A/065B completed format guidance, actionable error text, and import error smoke coverage.

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

- Reduce repeated context loading with context levels and targeted reading.
- For Level 1/2 tasks, start from this brief plus current task-board/changelog sections.
- For Level 3 tasks, use the full required reading order in `AGENTS.md`.
- Latest active next item in `docs/task_board.md`: Next item is None. A new post-v0.2 task must be selected before assigning implementation.

## Context Efficiency Rules

- Do not paste or reload full `docs/PRD.md`, full `docs/changelog.md`, or archive files for low-risk work.
- Use `rg` to find older decisions in `docs/archive/`, then read only matching sections.
- Keep handoff and review packets compact; store long evidence in `docs/agent_reports/` when needed.
- Codex reviews should start from changed files, focused diffs, verification output, and reviewer focus. Review one coherent bucket at a time when the worktree is mixed.
- Use focused tests before full suites unless the task touches broad engine behavior, release acceptance, no-future-leak assumptions, or architecture contracts.
- Token savings must never weaken tests, architecture boundaries, no-future-leak review, or milestone acceptance.
- Historical task-board Done items live in docs/archive/task_board_done_archive.md; older changelog entries live in docs/archive/changelog_archive.md. These are repository documentation artifacts, not local tool-state. Accepted untracked docs are grouped in docs/documentation_artifact_staging_plan_064H.md.
