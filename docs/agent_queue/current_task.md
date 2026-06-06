# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 056F - Remove Best N Trades Pipeline Integration.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/remove_best_n_trades_stress_design_056E.md`
8. `docs/review_notes/2026-06-06_task-056e-impl-fix_remove-best-n-trades-deterministic-test-hardening_codex-review.md`
9. `validation_engine/stress_test.py`
10. `app/services/validation_pipeline_service.py`
11. `tests/test_validation_pipeline_service.py`
12. This task file

## Context

The remove-best-N-trades stress engine function is accepted. The next step is to wire it into the validation pipeline behind an explicit opt-in flag. It must remain off by default because the test is only meaningful when baseline trade count is sufficient.

## Scope

### Do

- In `app/services/validation_pipeline_service.py`:
  - Import `stress_remove_best_n_trades`.
  - Add `PipelineConfig` fields:
    - `run_remove_best_n_trades_stress: bool = False`
    - `remove_best_n_trades_n: int = 3`
    - `remove_best_n_trades_degradation_threshold: float = 0.30`
  - When `run_remove_best_n_trades_stress` is true, call `stress_remove_best_n_trades()` and append `_stress_to_dict(result)` to `stress_results`.
  - Keep default pipeline behavior unchanged when the flag is false.
- In `tests/test_validation_pipeline_service.py`:
  - Add a test showing default config does not include `remove_best_n_trades`.
  - Add a test showing opt-in config includes `remove_best_n_trades`.
  - Assert the resulting stress dict includes assumptions such as `n`, `removed_count`, and `pnl_loss_ratio`.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-056f_remove-best-n-trades-pipeline-integration_deepseek.md`

### Do Not

- Do not change `validation_engine/stress_test.py` unless an integration bug is discovered.
- Do not modify UI/report code.
- Do not add new elimination thresholds.
- Do not turn this stress test on by default.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `app/services/validation_pipeline_service.py`
- `tests/test_validation_pipeline_service.py`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-056f_remove-best-n-trades-pipeline-integration_deepseek.md`

## Acceptance Criteria

1. Default validation pipeline output is unchanged: no `remove_best_n_trades` stress result unless explicitly enabled.
2. Opt-in pipeline config appends exactly one `remove_best_n_trades` stress result.
3. The stress result is serialized through existing `_stress_to_dict()` shape.
4. The result includes `assumptions["pnl_loss_ratio"]`.
5. No UI/report/elimination behavior changes.
6. Focused pipeline tests pass.
7. Full suite passes.
8. `git diff --check` passes.

## Verification

Run exactly:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_validation_pipeline_service.py tests/test_stress_test.py -v
.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused tests pass.
- Full suite passes without ignored tests.
- `git diff --check` passes.
- Agent status shows Task 056F completion report as the latest report.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
