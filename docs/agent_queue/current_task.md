# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 056B - IS/OOS Stability Gate Implementation.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/next_validation_expansion_triage_056A.md`
8. `docs/review_notes/2026-06-06_task-056a-fix_oos-stability-data-path-correction_codex-review.md`
9. `app/services/validation_pipeline_service.py`
10. `validation_engine/elimination.py`
11. `tests/test_elimination.py`
12. `tests/test_validation_pipeline_service.py`
13. This task file

## Context

Task 056A-Fix corrected the OOS stability data path. The pipeline currently creates an OOS split, but does not run an OOS backtest and does not pass OOS metrics into `evaluate_elimination()`. `evaluate_elimination()` already accepts `oos_metrics`, but only checks two basic OOS thresholds. This task implements the narrow pipeline plumbing and stability rules together.

## Scope

### Do

- In `app/services/validation_pipeline_service.py`:
  - Run a narrow OOS backtest on `split.oos` when an OOS segment exists and has rows.
  - Pass `oos_metrics=oos_baseline.metrics` into `evaluate_elimination()`.
  - Preserve current behavior when OOS is missing or empty; do not crash.
  - Include enough OOS diagnostics in `PipelineResult` or `elimination_result` so later UI/report tasks can inspect them.
- In `validation_engine/elimination.py`:
  - Add `_compute_oos_stability(oos_metrics: dict, is_metrics: dict) -> dict`.
  - Add optional `EliminationConfig` fields:
    - `max_oos_pf_degradation: float | None = None`
    - `max_oos_drawdown_ratio: float | None = None`
    - `max_oos_avg_trade_degradation: float | None = None`
  - Wire rules into `evaluate_elimination()` only when `oos_metrics` is provided and the relevant config field is set.
  - Keep existing OOS threshold behavior backward-compatible.
- Add focused tests in:
  - `tests/test_elimination.py`
  - `tests/test_validation_pipeline_service.py`
- Update `docs/changelog.md` and `docs/task_board.md`.
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-056b_is-oos-stability-gate_deepseek.md`

### Do Not

- Do not change backtest engine behavior.
- Do not add new stress tests.
- Do not modify Monte Carlo or walk-forward logic.
- Do not add UI components.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `app/services/validation_pipeline_service.py`
- `validation_engine/elimination.py`
- `tests/test_elimination.py`
- `tests/test_validation_pipeline_service.py`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-056b_is-oos-stability-gate_deepseek.md`

## Acceptance Criteria

1. Pipeline runs an OOS backtest when OOS data exists.
2. Pipeline passes OOS metrics into `evaluate_elimination()`.
3. New stability rules fail/pass deterministically in focused tests.
4. Missing or empty OOS data does not crash the pipeline.
5. Existing elimination tests remain compatible.
6. Completion report exists.

## Verification

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_elimination.py tests/test_validation_pipeline_service.py -v
.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused tests pass.
- Full suite passes.
- `git diff --check` passes.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
