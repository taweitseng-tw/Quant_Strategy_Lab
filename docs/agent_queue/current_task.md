# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 060O-Impl + 060P-Signoff - Coordinator Acceptance Tests and Reproducibility Foundation Signoff.

## Context Level

Level 3 for both tasks.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `archive/import_coordinator.py`
9. `archive/importer.py`
10. `archive/verifier.py`
11. `archive/stager.py`
12. `archive/exporter.py`
13. `archive/manifest.py`
14. `repository/strategy_import_adapter.py`
15. `repository/dataset_import_adapter.py`
16. `repository/import_audit_repo.py`
17. `tests/test_archive_import_coordinator.py`
18. `docs/archive_import_coordinator_acceptance_tests_design_060N.md`
19. `docs/review_notes/2026-06-07_task-060m-impl_060n-design_archive-import-coordinator-and-acceptance-tests_codex-review.md`
20. This task file

## Context

060M introduced `ArchiveImportCoordinator`. Codex corrected the first pass after review: preflight duplicate checks must be read-only, success must insert a strategy only once, and audit write failures must set `ImportResult.audit_failed=True` without masking the original import error.

The next round must prove coordinator behavior with more realistic acceptance tests. Keep this focused on test coverage and signoff. Do not expand product scope.

## Scope

### Task 060O-Impl - Coordinator Acceptance Test Implementation

Create integration-style coordinator tests using real temporary archive/project folders and SQLite-backed repository adapters where practical.

Do:

- Add a focused acceptance test file, suggested path `tests/test_archive_import_coordinator_acceptance.py`.
- Implement realistic tests based on `docs/archive_import_coordinator_acceptance_tests_design_060N.md`:
  1. manifest/hash verification failure returns `ImportResult(success=False)` with no staging and no DB writes;
  2. duplicate strategy UID returns `skipped=True`, preserves the existing row, and performs no staging or DB insert;
  3. duplicate dataset snapshot hash fails import, writes failure audit, and rolls back the strategy row;
  4. final move failure returns `partial=True`, keeps committed DB rows, and preserves staged data for repair;
  5. audit adapter failure preserves the original import error and sets `audit_failed=True`;
  6. coordinator import boundary has no UI/engine dependency.
- Use real `sqlite3.Connection` and real repository adapters for DB behavior where possible.
- It is acceptable to use a tiny fake verifier/importer/stager only when the real component would make the test brittle or unrelated to the behavior being asserted.
- Keep all new tests deterministic and temp-directory scoped.
- Update `docs/changelog.md`.
- Update `docs/task_board.md` if the next proposed task changes.

Do not:

- Do not change UI, backtest, validation, strategy generation, or report surfaces.
- Do not add success audit behavior.
- Do not add overwrite/upsert/merge import semantics.
- Do not weaken coordinator rollback or partial-failure semantics.
- Do not use insert-and-rollback as a duplicate probe.

Acceptance criteria:

1. New acceptance tests fail on the pre-Codex double-insert/rollback-probe design.
2. Duplicate preflight paths do not stage files and do not insert strategy/dataset rows.
3. Dataset duplicate during DB write rolls back any strategy insert from the same transaction.
4. Final move failure is explicitly partial and does not roll back committed DB rows.
5. Audit write failure is visible through `audit_failed=True`.

Verification:

- Run:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_archive_import_coordinator.py tests\test_archive_import_coordinator_acceptance.py -q`
  - `.\.venv\Scripts\python.exe -m pytest -q`
  - `git diff --check`
  - `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1`

### Task 060P-Signoff - Reproducibility Foundation Signoff

Do:

- Create a short signoff/triage document, suggested path `docs/reproducibility_foundation_signoff_060P.md`.
- Summarize what is now covered across archive manifest, exporter/importer, stager, repository adapters, audit log, and coordinator.
- List remaining risks before moving beyond the reproducibility foundation.
- Recommend the next two-task batch after 060O/060P.

Do not:

- Do not declare the whole project complete.
- Do not mark live trading, broker integration, GA/GP expansion, or portfolio backtest as in scope.

## Completion Report

After completion, create:

`docs/agent_reports/2026-06-07_task-060o-impl_060p-signoff_coordinator-acceptance-tests-and-foundation-signoff_deepseek.md`

Use this packet:

```text
Completed:
Files changed:
Behavior changed:
Tests run:
Assumptions:
Known risks:
Reviewer focus:
```

Then stop.
