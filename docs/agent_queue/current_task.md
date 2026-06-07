# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 060M-Impl + 060N-Design - ArchiveImportCoordinator First-Pass Implementation and Coordinator Acceptance Test Design.

## Context Level

Level 3 for 060M implementation, Level 3 for 060N design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `archive/importer.py`
9. `archive/verifier.py`
10. `archive/stager.py`
11. `repository/strategy_import_adapter.py`
12. `repository/dataset_import_adapter.py`
13. `repository/import_audit_repo.py`
14. `docs/archive_import_coordinator_first_pass_wiring_design_060L.md`
15. `docs/archive_import_coordinator_architecture_060A.md`
16. `docs/review_notes/2026-06-07_task-060k-impl_060l-design_archive-stager-and-coordinator-wiring_codex-review.md`
17. This task file

## Context

060K implemented `ArchiveStager`. 060L designed first-pass coordinator wiring. The next implementation should introduce a first-pass `ArchiveImportCoordinator` that orchestrates existing components without adding UI, engine, report, or success-audit behavior. Keep this slice small and test with fakes/spies.

## Scope

### Do

- Complete two sequential tasks:
  - Task 060M-Impl - implement first-pass `ArchiveImportCoordinator`.
  - Task 060N-Design - design coordinator acceptance tests for the next hardening slice.
- For Task 060M:
  - Create a small coordinator module, suggested path `archive/import_coordinator.py`.
  - Implement a minimal `ImportResult` dataclass with:
    - `success: bool`
    - `partial: bool = False`
    - `skipped: bool = False`
    - `strategy_id: int | None = None`
    - `dataset_id: int | None = None`
    - `error: str | None = None`
    - `audit_failed: bool = False`
  - Implement a first-pass coordinator class or function that wires existing collaborators in this order:
    1. archive preview / manifest load;
    2. archive verification;
    3. construct DTOs;
    4. stage dataset snapshot and verify hash;
    5. call `StrategyRepoAdapter.insert_strategy_no_commit(...)`;
    6. call `DatasetRepoAdapter.insert_dataset_no_commit(...)`;
    7. `conn.commit()`;
    8. final file move;
    9. temp cleanup on success.
  - Use dependency injection or constructor parameters so tests can pass fakes/spies for importer, verifier, stager, strategy adapter, dataset adapter, audit adapter, and connection.
  - Failure behavior:
    - duplicate strategy or dataset -> rollback if transaction started, cleanup temp if staged, write failure audit if possible, return skipped/failure result;
    - staging/hash failure -> cleanup temp, write failure audit if possible, no DB writes;
    - DB write/commit failure -> rollback connection, cleanup temp, write failure audit if possible;
    - final move failure after DB commit -> return `ImportResult(success=False, partial=True, ...)`, preserve staged file, write failure audit if possible, do not rollback DB rows;
    - audit write failure must not mask the original failure and should set `audit_failed=True`.
  - Add focused tests with fakes/spies for:
    - success path call order;
    - duplicate strategy skips staging and DB writes;
    - staging/hash failure cleans temp and writes audit;
    - DB write failure rolls back and cleans temp;
    - commit failure rolls back and cleans temp;
    - final move failure returns partial and preserves staged file;
    - audit failure does not mask original result;
    - no UI/engine imports.
- For Task 060N:
  - Create `docs/archive_import_coordinator_acceptance_tests_design_060N.md`.
  - Design only. Do not add a second production coordinator.
  - Define the next acceptance-test hardening slice for real archive fixtures and integration-style coordinator tests.
  - Include tests for manifest hash mismatch, duplicate dataset hash, duplicate strategy UID, final move partial state, audit failure isolation, and no UI/engine boundary.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-060m-impl_060n-design_archive-import-coordinator-and-acceptance-tests-design_deepseek.md`

### Do Not

- Do not build UI or CLI flows.
- Do not add report/export behavior.
- Do not add success audit writes unless already isolated and explicitly needed by a test; failure audit only is enough for this slice.
- Do not move, copy, or delete files outside pytest temporary directories during tests.
- Do not add dependencies.
- Do not change backtest, validation, strategy generator, or report exporters.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Acceptance Criteria

1. Coordinator is small and dependency-injectable for tests.
2. Success ordering is verified with fakes/spies.
3. Failure paths preserve architecture boundaries and cleanup rules.
4. Final move failure returns `partial=True` and does not delete DB rows or staged repair file.
5. Audit failure does not mask the original failure.
6. 060N is design-only.
7. Full suite, `git diff --check`, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1
git status --short
```

Expected:

- Full suite passes.
- `git diff --check` has no errors.
- Agent status shows the 060M/060N completion report as latest report.
- `git status --short` shows only files within this task scope.

## Completion Report Format

Use:

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
