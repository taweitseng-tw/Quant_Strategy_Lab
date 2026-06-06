# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 056E - Remove Best N Trades Stress Test Design Only.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `validation_engine/stress_test.py`
8. `app/services/validation_pipeline_service.py`
9. `validation_engine/elimination.py`
10. Relevant stress/validation tests found by search
11. This task file

## Context

The validation pipeline now has OOS stability gates and OOS display surfaces. The next validation expansion candidate is a "remove best N trades" stress test: a robustness check that asks whether a strategy survives after its best trades are removed from the trade list. This is useful for detecting strategies whose entire edge depends on one or two outlier trades.

This task is design only. Do not implement engine or pipeline changes yet.

## Scope

### Do

- Inspect current stress-test patterns in `validation_engine/stress_test.py`.
- Inspect how `app/services/validation_pipeline_service.py` collects stress results.
- Inspect current stress/elimination tests to understand result schemas and naming conventions.
- Design a minimal "Remove Best N Trades" stress test:
  - Function name.
  - Input shape.
  - Output shape.
  - How trades are sorted and removed.
  - Metrics to recompute or compare.
  - Deterministic behavior.
  - Empty/low-trade-count behavior.
  - How it should be integrated into the validation pipeline later.
- Decide whether the first implementation should be engine-only or pipeline-integrated.
- Write a design note:
  - `docs/remove_best_n_trades_stress_design_056E.md`
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-056e_remove-best-n-trades-stress-design_deepseek.md`

### Do Not

- Do not change production code.
- Do not change tests.
- Do not add the stress test yet.
- Do not modify pipeline behavior.
- Do not modify elimination thresholds.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `docs/remove_best_n_trades_stress_design_056E.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-056e_remove-best-n-trades-stress-design_deepseek.md`

Read-only inspection likely includes:

- `validation_engine/stress_test.py`
- `app/services/validation_pipeline_service.py`
- `tests/test_stress_test.py` or related stress tests found by `rg`
- `tests/test_validation_pipeline_service.py`

## Acceptance Criteria

1. The design follows existing stress-test result schemas and naming style.
2. The design defines conservative behavior for fewer trades than `n`.
3. The design avoids future leak and does not mutate original trade data.
4. The design proposes one small follow-up implementation task with exact files and tests.
5. No production code or tests are changed.
6. `docs/changelog.md` and `docs/task_board.md` are updated.
7. `git diff --check` passes.

## Verification

Run exactly:

```powershell
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- `git diff --check` passes.
- Agent status shows Task 056E completion report as the latest report.
- No production code or tests changed.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
