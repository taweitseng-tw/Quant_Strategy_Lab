# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 057A-Impl + 057C-Design - Monte Carlo Bootstrap Engine and Surface Design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-06_task-057a-fix_057b-impl_validation-gap-hardening-batch_codex-review.md`
8. `docs/monte_carlo_bootstrap_ci_design_057A.md`
9. `docs/walk_forward_equity_persistence_design_057B.md`
10. `docs/milestone_direction_056N.md`
11. `docs/v0.2_validation_expansion_readiness.md`
12. This task file

## Context

Batch 057A-Fix + 057B-Impl was accepted. Walk-forward equity persistence is now implemented. The Monte Carlo bootstrap design is hardened enough for an engine-only implementation. This batch pairs one engine-only implementation task with one design-only surface planning task.

## Scope

### Do

- Complete two sequential tasks:
  - Task 057A-Impl - Monte Carlo Bootstrap + Confidence Interval Engine Implementation
  - Task 057C-Design - Bootstrap Pipeline and Report Surface Design
- For Task 057A-Impl:
  - Implement `run_bootstrap_monte_carlo()` in `validation_engine/monte_carlo.py`.
  - Add additive `confidence_intervals: dict[str, dict[str, float]] | None = None` to `MonteCarloResult`.
  - Do not add `worst_case_equity`.
  - Use local deterministic RNG only (`random.Random(base_seed + i)` or equivalent); do not mutate global random state.
  - Resample trades with replacement and recompute metrics in the smallest reasonable way consistent with existing `BacktestResult`/metrics conventions.
  - Preserve existing MC function behavior and schema.
  - Add focused deterministic tests in `tests/test_monte_carlo.py`.
  - Tests must avoid unsafe assumptions that bootstrap always worsens metrics. If checking changed distribution, use deliberately heterogeneous synthetic trades and deterministic seed/iteration expectations.
- For Task 057C-Design:
  - Write `docs/bootstrap_pipeline_report_surface_design_057C.md`.
  - Design only; do not implement pipeline/report/UI changes.
  - Cover `PipelineConfig` flags, `PipelineResult` field shape, `_mc_to_dict()`/serialization strategy, validation summary/report display wording, default-off behavior, acceptance tests, and non-goals.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-057a-impl_057c-design_bootstrap-engine-and-surface-design_deepseek.md`

### Do Not

- Do not wire bootstrap into `run_validation_pipeline()` in this batch.
- Do not modify UI widgets or reports.
- Do not add report display code.
- Do not add UI controls.
- Do not add `worst_case_equity`.
- Do not change walk-forward production code in this batch.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `validation_engine/monte_carlo.py`
- `tests/test_monte_carlo.py`
- `docs/bootstrap_pipeline_report_surface_design_057C.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-057a-impl_057c-design_bootstrap-engine-and-surface-design_deepseek.md`

## Acceptance Criteria

1. Existing missed-trade/slippage/combined MC tests still pass unchanged.
2. `run_bootstrap_monte_carlo()` returns deterministic structured `MonteCarloResult`.
3. `confidence_intervals` are present for bootstrap and absent/None for existing MC functions.
4. Bootstrap implementation does not mutate baseline trades or global random state.
5. Zero-trade, single-trade, invalid-iteration, and invalid-confidence-level cases are tested.
6. 057C design covers pipeline/report surfaces without implementation.
7. Changelog and task board are updated.
8. Completion report is created.
9. Focused tests and `git diff --check` pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_monte_carlo.py -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused tests pass.
- `git diff --check` passes.
- Agent status shows Batch 057A-Impl + 057C-Design completion report as the latest report.
- Bootstrap is not wired into pipeline/UI/reports yet.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
