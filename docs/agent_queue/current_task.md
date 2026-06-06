# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 057A-057B - Validation Gap Design Batch.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-06_task-056n_milestone-direction-decision-brief_codex-review.md`
8. `docs/milestone_direction_056N.md`
9. `docs/v0.2_validation_expansion_readiness.md`
10. `docs/validation_expansion_series_acceptance_056L.md`
11. Latest 056-series review notes and agent reports
12. This task file

## Context

Task 056N recommended Direction A: complete the remaining validation gaps while the validation subsystem is mature and fresh. This is a two-task batch, but both tasks are design-only. Do not implement code in this batch.

## Scope

### Do

- Complete two sequential design-only tasks:
  - Task 057A-Design - Monte Carlo Bootstrap + Confidence Interval Design
  - Task 057B-Design - Walk-forward Per-window Equity Persistence Design
- For Task 057A, write:
  - `docs/monte_carlo_bootstrap_ci_design_057A.md`
  - Cover bootstrap method, deterministic seed behavior, confidence interval outputs, integration points, assumptions, edge cases, test plan, and non-goals.
- For Task 057B, write:
  - `docs/walk_forward_equity_persistence_design_057B.md`
  - Cover per-window equity data shape, serialization/report integration points, backward compatibility, memory/performance considerations, edge cases, test plan, and non-goals.
- The two designs must be independently reviewable. Task 057B must not depend on Task 057A being implemented.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-057ab_validation-gap-design-batch_deepseek.md`

### Do Not

- Do not change production code.
- Do not add tests.
- Do not implement new validation, backtest, strategy, data, UI, or report behavior.
- Do not modify `validation_engine/`, `app/`, `reports/`, or `tests/`.
- Do not implement Monte Carlo bootstrap.
- Do not implement walk-forward equity persistence.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `docs/monte_carlo_bootstrap_ci_design_057A.md`
- `docs/walk_forward_equity_persistence_design_057B.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-057ab_validation-gap-design-batch_deepseek.md`

## Acceptance Criteria

1. 057A design covers method, deterministic seed behavior, outputs, integration points, assumptions, edge cases, test plan, and non-goals.
2. 057B design covers data shape, serialization/report integration, backward compatibility, memory/performance, edge cases, test plan, and non-goals.
3. The two designs are independent and reviewable separately.
4. No production code or tests are changed.
5. Changelog and task board are updated.
6. Completion report is created.
7. `git diff --check` passes.

## Verification

Run:

```powershell
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- `git diff --check` passes.
- Agent status shows Batch 057A-057B completion report as the latest report.
- No production code or tests are changed.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
