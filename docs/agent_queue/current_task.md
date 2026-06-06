# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 057A-Fix + 057B-Impl - Validation Gap Hardening Batch.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-06_task-057ab_validation-gap-design-batch_codex-review.md`
8. `docs/monte_carlo_bootstrap_ci_design_057A.md`
9. `docs/walk_forward_equity_persistence_design_057B.md`
10. `docs/milestone_direction_056N.md`
11. `docs/v0.2_validation_expansion_readiness.md`
12. This task file

## Context

Batch 057A-057B produced two design documents. Codex accepted the batch, but Task 057A needs design hardening before implementation. Task 057B is small and implementation-ready. This batch intentionally pairs one design-fix task with one narrow implementation task.

## Scope

### Do

- Complete two sequential tasks:
  - Task 057A-Fix - Monte Carlo Bootstrap + CI Design Hardening
  - Task 057B-Impl - Walk-forward Per-window Equity Persistence Implementation
- For Task 057A-Fix:
  - Update only `docs/monte_carlo_bootstrap_ci_design_057A.md`.
  - Remove v0.2 `worst_case_equity` output from the proposed schema if worst-case equity projection remains deferred.
  - Clarify that bootstrap output adds `confidence_intervals` only, unless a field is already implemented by this task's scope.
  - Replace unsafe test claims:
    - Do not assert bootstrap is always more conservative.
    - Do not assert one deterministic run proves confidence interval statistical coverage.
  - Specify local deterministic RNG (`random.Random(base_seed + i)` or equivalent), not global `random.seed(...)`.
  - Make the implementation plan small enough for a later engine-only task.
- For Task 057B-Impl:
  - Implement `WalkForwardWindow.equity_curve: list[float] | None = None`.
  - Add `store_equity: bool = False` to `walk_forward()`.
  - When enabled, populate each window from the test backtest equity curve as a plain list of floats.
  - Add `wf_store_equity: bool = False` to `PipelineConfig`.
  - Pass `wf_store_equity` into `walk_forward()` from `run_validation_pipeline()`.
  - Update `_wf_to_dict()` to include `windows` only when at least one window has `equity_curve is not None`.
  - Add focused tests for enabled/disabled behavior, pipeline config serialization, and backward compatibility.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-057a-fix_057b-impl_validation-gap-hardening-batch_deepseek.md`

### Do Not

- Do not implement Monte Carlo bootstrap in 057A-Fix.
- Do not change Monte Carlo production code in this batch.
- Do not modify UI widgets or reports.
- Do not add walk-forward equity charts.
- Do not add SQLite/Parquet persistence.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `docs/monte_carlo_bootstrap_ci_design_057A.md`
- `validation_engine/walk_forward.py`
- `app/services/validation_pipeline_service.py`
- `tests/test_walk_forward.py`
- `tests/test_validation_pipeline_service.py`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-057a-fix_057b-impl_validation-gap-hardening-batch_deepseek.md`

## Acceptance Criteria

1. 057A design no longer has conflicting v0.2/deferred output fields.
2. 057A test plan avoids statistically invalid assertions.
3. 057A specifies local deterministic RNG and a narrow later implementation path.
4. 057B keeps default behavior unchanged when `store_equity=False`.
5. 057B returns serialized window equity only when `wf_store_equity=True`.
6. Focused tests cover 057B enabled/disabled pipeline and engine behavior.
7. Changelog and task board are updated.
8. Completion report is created.
9. Focused tests and `git diff --check` pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_walk_forward.py tests/test_validation_pipeline_service.py -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused tests pass.
- `git diff --check` passes.
- Agent status shows Batch 057A-Fix + 057B-Impl completion report as the latest report.
- No Monte Carlo production code is changed.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
