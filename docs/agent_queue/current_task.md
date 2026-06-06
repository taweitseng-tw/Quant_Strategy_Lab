# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 058B-Fix + 058C-Design - Widget MC Worst-case Defensive Fix and Normalizer Warning Triage Design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-07_task-058a_v0.2-cleanup-hardening-audit_codex-review.md`
8. `docs/v0.2_cleanup_hardening_audit_058A.md`
9. This task file

## Context

Task 058A found 0 blockers and 1 recommended cleanup. The valid cleanup is a display hardening issue in `ValidationSummary`: Monte Carlo percentile data can render while `worst_case.total_pnl` is absent, causing a string fallback to be formatted with `:,.0f`.

## Scope

### Do

- Complete two sequential tasks:
  - Task 058B-Fix - Widget MC Worst-case Defensive Display Fix
  - Task 058C-Design - Normalizer Datetime Warning Triage Design
- For Task 058B-Fix:
  - Update `app/widgets/validation_summary.py` so Monte Carlo rendering does not crash when `monte_carlo_summary["worst_case"]` or `worst_case["total_pnl"]` is missing.
  - Preserve current display when valid worst-case PnL exists.
  - Use a clear `N/A` style fallback instead of numeric formatting on non-numeric values.
  - Add focused tests in `tests/test_validation_summary.py`.
- For Task 058C-Design:
  - Create `docs/normalizer_datetime_warning_triage_058C.md`.
  - Design-only; do not change `data_engine/normalizer.py`.
  - Explain the current pandas warning, why it is non-blocking, candidate fixes, risks, and one recommended future implementation path.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-058b-fix_058c-design_widget-mc-hardening-and-normalizer-warning-triage_deepseek.md`

### Do Not

- Do not change validation engine logic.
- Do not change Monte Carlo computation semantics.
- Do not change `data_engine/normalizer.py` in this batch.
- Do not create, delete, move, retarget, or push any git tag.
- Do not add broad ignore rules.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `app/widgets/validation_summary.py`
- `tests/test_validation_summary.py`
- `docs/normalizer_datetime_warning_triage_058C.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-058b-fix_058c-design_widget-mc-hardening-and-normalizer-warning-triage_deepseek.md`

## Acceptance Criteria

1. ValidationSummary does not crash when MC percentile data exists but worst-case data is missing.
2. Existing valid MC display behavior is preserved.
3. Focused widget tests cover missing `worst_case` and/or missing `total_pnl`.
4. 058C design file exists and does not modify normalizer code.
5. Changelog and task board are updated.
6. Completion report is created.
7. Focused tests, full suite, `git diff --check`, tag verification, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_summary.py -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
git show --no-patch --decorate --date=iso --format=fuller v0.2-alpha-validation-expansion
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused widget tests pass.
- Full suite passes with only known pre-existing warning.
- `git diff --check` passes.
- Tag remains unchanged and points to `1a9c533`.
- Agent status shows Batch 058B-Fix + 058C-Design completion report as latest report.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
