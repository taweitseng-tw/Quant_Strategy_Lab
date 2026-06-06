# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 058D-Fix + 058E-Verify - Normalizer Warning Suppression and Zero-warning Verification.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-07_task-058b-fix_058c-design_widget-mc-hardening-and-normalizer-warning-triage_codex-review.md`
8. `docs/normalizer_datetime_warning_triage_058C.md`
9. This task file

## Context

Batch 058B-Fix + 058C-Design was accepted by Codex. The remaining known warning is emitted only by `tests/test_csv_importer.py::test_normalize_malformed_datetime_raises`, where malformed datetime input intentionally triggers pandas' format inference warning before QSL raises `NormalizerError`.

## Scope

### Do

- Complete two sequential tasks:
  - Task 058D-Fix - Suppress Known Normalizer Malformed Datetime Warning in Test
  - Task 058E-Verify - Zero-warning Verification Note
- For Task 058D-Fix:
  - Update `tests/test_csv_importer.py` only.
  - Suppress the specific pandas warning only for `test_normalize_malformed_datetime_raises`.
  - Keep the `NormalizerError` assertion intact.
  - Do not change `data_engine/normalizer.py`.
- For Task 058E-Verify:
  - Create `docs/zero_warning_verification_058E.md`.
  - Document the warning source, the test-level suppression, and the final verification result.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-058d-fix_058e-verify_normalizer-warning-suppression-and-zero-warning-verification_deepseek.md`

### Do Not

- Do not change production Python code.
- Do not change normalizer behavior.
- Do not broadly suppress all warnings.
- Do not create, delete, move, retarget, or push any git tag.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `tests/test_csv_importer.py`
- `docs/zero_warning_verification_058E.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-058d-fix_058e-verify_normalizer-warning-suppression-and-zero-warning-verification_deepseek.md`

## Acceptance Criteria

1. The malformed datetime test still asserts `NormalizerError`.
2. Only the specific pandas datetime inference warning is suppressed.
3. No production code changes are made.
4. Full suite reports zero warnings.
5. Zero-warning verification note exists.
6. Changelog and task board are updated.
7. Completion report is created.
8. Focused test, full suite, `git diff --check`, tag verification, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_csv_importer.py::test_normalize_malformed_datetime_raises -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
git show --no-patch --decorate --date=iso --format=fuller v0.2-alpha-validation-expansion
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Focused malformed datetime test passes.
- Full suite passes and reports no warnings.
- `git diff --check` passes.
- Tag remains unchanged and points to `1a9c533`.
- Agent status shows Batch 058D-Fix + 058E-Verify completion report as latest report.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
