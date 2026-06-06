# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 056I - Remove Best N Trades Feature Acceptance Smoke.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-06_task-056h-impl_remove-best-n-trades-stress-config-controls_codex-review.md`
8. `app/services/validation_pipeline_service.py`
9. `app/ui/main_window.py`
10. `app/widgets/validation_summary.py`
11. `reports/generator.py`
12. Existing remove-best-N related tests
13. This task file

## Context

The remove-best-N-trades stress feature now has:

- Engine implementation.
- Pipeline opt-in wiring.
- Serialized assumptions/warnings/threshold.
- Validation summary and report display.
- Validate page controls feeding `PipelineConfig`.

Before moving to another validation feature, add a narrow acceptance smoke that proves the feature chain remains coherent. This should be mostly test-only.

## Scope

### Do

- Add a focused acceptance smoke test file or extend the closest existing tests.
- Cover the remove-best-N feature chain at a high level:
  - `PipelineConfig(run_remove_best_n_trades_stress=True, remove_best_n_trades_n=2)` produces a `remove_best_n_trades` stress result.
  - The stress result includes `assumptions`, `warnings`, and `threshold`.
  - `ValidationSummary` renders the remove-best-N detail line from a representative validation result.
  - Markdown and HTML report generation render remove-best-N detail lines.
  - HTML report output escapes malicious stress detail values.
  - Validate page controls pass enabled/custom values into `PipelineConfig`.
- Keep this as acceptance coverage. Do not duplicate every unit assertion from lower-level tests.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-056i_remove-best-n-trades-feature-acceptance-smoke_deepseek.md`

### Do Not

- Do not change engine logic unless an acceptance test exposes a real bug.
- Do not change pipeline behavior unless an acceptance test exposes a real bug.
- Do not redesign UI controls.
- Do not change report format beyond fixing a real bug.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `tests/test_remove_best_n_trades_acceptance.py` or closest existing test files
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-056i_remove-best-n-trades-feature-acceptance-smoke_deepseek.md`

Read-only references:

- `tests/test_validation_pipeline_service.py`
- `tests/test_validation_summary.py`
- `tests/test_report_export.py`
- `tests/test_wfe_ui_wiring.py`

## Acceptance Criteria

1. Acceptance smoke verifies enabled pipeline output includes `remove_best_n_trades`.
2. Acceptance smoke verifies assumptions/warnings/threshold are available.
3. Acceptance smoke verifies ValidationSummary display includes remove-best-N details.
4. Acceptance smoke verifies Markdown and HTML reports include remove-best-N details.
5. Acceptance smoke verifies HTML escaping for stress detail values.
6. Acceptance smoke verifies UI controls pass enabled/custom values into `PipelineConfig`.
7. No production code changes unless a real bug is found and documented.
8. Focused acceptance tests pass.
9. Full suite passes.
10. `git diff --check` passes.

## Verification

Run exactly:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_remove_best_n_trades_acceptance.py -v
.venv\Scripts\python.exe -m pytest tests/test_validation_pipeline_service.py tests/test_validation_summary.py tests/test_report_export.py tests/test_wfe_ui_wiring.py -v
.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused acceptance tests pass.
- Related regression tests pass.
- Full suite passes without ignored tests.
- `git diff --check` passes.
- Agent status shows Task 056I completion report as the latest report.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
