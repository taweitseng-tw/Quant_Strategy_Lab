# 2026-06-06 - Codex Review - Task 056A Next Validation Expansion Triage

## Verdict

Needs Fix.

## Score

7.4 / 10.

## Findings

1. P1 - Recommended Task 056B scope does not explain how OOS metrics enter the elimination path.
   - Files: `docs/next_validation_expansion_triage_056A.md`, `app/services/validation_pipeline_service.py`, `validation_engine/elimination.py`
   - Issue: The triage recommends adding IS/OOS stability rules mainly inside `validation_engine/elimination.py`, but `run_validation_pipeline()` currently calls `evaluate_elimination(baseline.metrics, elim_cfg)` with train/IS metrics only. It does not run an OOS backtest or pass `oos_metrics=...`.
   - Impact: A 056B implementation that only adds elimination rules would be technically correct in isolation but ineffective in the default validation pipeline.
   - Expected: The triage must define the data path for OOS metrics before implementation. Either Task 056B should include a narrow OOS backtest + pipeline wiring, or it should be explicitly split into two tasks.

2. P2 - Handoff references a likely nonexistent file.
   - File: `docs/agent_reports/2026-06-06_task-056a_next-validation-expansion-triage_deepseek.md`
   - Issue: The handoff prompt tells the next agent to read `core/models/validation.py`, but that file does not exist in the current repo. `EliminationConfig` lives in `validation_engine/elimination.py`.
   - Impact: The next execution agent may waste time or create a parallel model location.
   - Expected: Correct the handoff and triage note to reference `validation_engine/elimination.py`.

3. P2 - `current_task.md` was not updated to Task 056B.
   - File: `docs/agent_queue/current_task.md`
   - Issue: `docs/task_board.md` marks Task 056B as In Progress, but `current_task.md` still contains Task 056A.
   - Impact: The file-based workflow is inconsistent; Reasonix/DeepSeek reading `current_task.md` would repeat the completed triage.
   - Expected: Queue a corrected design-fix task now, then later queue 056B only after the triage is fixed.

## Positive Notes

- The recommended direction, IS/OOS stability, is strategically sound and aligns with PRD section 12.2 and the "OOS is Sacred" principle.
- The task stayed design-only: only docs/report/task board changed.
- `git diff --check` passes.

## Required Fix

- Revise the triage note to define whether 056B should:
  - include OOS backtest execution in `run_validation_pipeline()` and pass `oos_metrics` into `evaluate_elimination`, or
  - be split into `056B` OOS metrics plumbing and `056C` stability rule implementation.
- Correct all wrong file references.
- Update `docs/agent_queue/current_task.md` so the next task is a narrow 056A-Fix, not implementation.
