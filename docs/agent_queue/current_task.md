# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 053E - Session-End Exit Engine Implementation.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/backtest_execution_enhancement_triage_053D.md`
8. `docs/review_notes/2026-06-05_task-053d-fix_session-end-exit-triage-hardening_codex-review.md`
9. `backtest_engine/runner.py`
10. `core/models/strategy.py`
11. `core/serialization/strategy_serializer.py`
12. `repository/strategy_repo.py`
13. `app/services/report_service.py`
14. `tests/test_backtest_engine.py`
15. Relevant serializer/repository/import tests
16. This task file

## Scope

### Do

- Implement optional session-end exit behavior using configured session boundaries only.
- Add backward-compatible fields to `RiskManagement`, with defaults preserving current behavior:
  - `close_end_of_session: bool = False`
  - `session_end_time: str | None = None`
- Implement session-end exit in `backtest_engine/runner.py` without scanning/grouping the full dataset to discover final bars.
- Use the configured `session_end_time` and current `bar_datetime.time()` only.
- When enabled and an open position exists at or after session end, close it at the current bar close with normal exit-side slippage and commission.
- Preserve existing priority:
  - Intra-bar stop-loss / take-profit remains higher priority than session-end exit.
  - Existing rule-based signal exits remain next-bar-open behavior.
- Prevent new pending entry signals at or after the configured session end when `close_end_of_session` is enabled.
- Add assumptions output for session-end exit configuration.
- Update serializer/repository/import handling only as needed for backward-compatible `RiskManagement` fields.
- Add focused tests covering:
  - Default disabled behavior remains unchanged.
  - Long session-end exit.
  - Short session-end exit.
  - No future-row dependency.
  - Missing final bars / early close behavior.
  - Commission and slippage are applied to session-end exits.
  - Stop-loss / take-profit preempts session-end exit on the same bar.
  - No new pending entry at or after session end.
  - Backward-compatible serializer/repository/import behavior for missing new fields.
- Update `docs/changelog.md` and `docs/task_board.md`.
- Write one completion report in `docs/agent_reports/`.

### Do Not

- Do not implement full session templates.
- Do not implement dynamic slippage.
- Do not change same-bar ambiguity configuration.
- Do not implement one-bar delay stress tests.
- Do not change UI layout.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.
- Do not add dependencies.

## Files Likely Involved

- `core/models/strategy.py`
- `backtest_engine/runner.py`
- `core/serialization/strategy_serializer.py`
- `repository/strategy_repo.py`
- `app/services/report_service.py`
- `tests/test_backtest_engine.py`
- Relevant serializer/repository/import tests
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-05_task-053e_session-end-exit-engine_deepseek.md`

## Acceptance Criteria

1. Existing tests for default behavior still pass.
2. Session-end exit is opt-in and backward-compatible.
3. No implementation scans the full dataset to discover final session bars.
4. Session-end exits use current bar timestamp and configured `session_end_time`.
5. Stop-loss/take-profit priority remains conservative.
6. Focused tests cover long/short exits, missing final bars, no future-row dependency, costs, assumptions, and compatibility.
7. Agent report exists.

## Verification

Run:

```powershell
python -m pytest tests/test_backtest_engine.py tests/test_strategy_serializer.py tests/test_strategy_repo.py tests/test_strategy_json_import_service.py -v
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused tests pass.
- Version Control section shows dirty implementation/test/docs files only.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
