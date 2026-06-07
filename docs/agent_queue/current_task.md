# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Flash or Gemini 3.5 Flash

## Current Task

Batch 060A-Design + 060B-Design - Archive Import Coordinator Architecture and Acceptance Test Contract Design.

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
8. `docs/archive_import_audit_migration_plan_059S.md`
9. `docs/archive_import_repository_adapter_test_contract_059T.md`
10. `docs/archive_import_write_coordinator_design_059X.md`
11. `docs/archive_import_filesystem_staging_design_059Z.md`
12. `docs/review_notes/2026-06-07_task-059y-impl_059z-design_fix_strategy-uid-duplicate-guard_codex-review.md`
13. This task file

## Context

The archive import path now has read-only preview, manifest verification, failure-only audit logging, UID-based duplicate-reject strategy insert, and filesystem staging design. The next step is not implementation. It is a stricter coordinator architecture and test contract so the future write coordinator does not mix UI, repository, file, and audit responsibilities.

## Scope

### Do

- Complete two design-only tasks:
  - Task 060A-Design - archive import coordinator architecture design.
  - Task 060B-Design - archive import coordinator acceptance test contract design.
- For Task 060A:
  - Create `docs/archive_import_coordinator_architecture_060A.md`.
  - Define the future coordinator's responsibilities, collaborators, transaction boundaries, rollback/cleanup policy, and failure audit behavior.
  - Explicitly describe how these existing pieces are sequenced:
    - `ArchiveImporter.build_preview()`
    - archive verifier / manifest hash checks
    - future filesystem staging adapter
    - `StrategyRepoAdapter.insert_strategy()`
    - future dataset/validation adapters
    - `AuditLogRepositoryAdapter.insert_failure_log()`
  - Include specific handling for:
    - duplicate strategy UID,
    - malformed legacy `strategy_json` encountered during UID scanning,
    - staged-file hash mismatch,
    - DB failure before commit,
    - final file move failure after DB commit,
    - failure audit write failure.
  - Clearly mark every implementation item as future work.
- For Task 060B:
  - Create `docs/archive_import_coordinator_acceptance_test_contract_060B.md`.
  - Define acceptance tests using spies/fakes only; do not implement tests.
  - Cover success path, duplicate UID failure path, filesystem staging failure path, DB insert failure path, final move failure path, failed audit logging path, and no-UI/no-CLI/no-engine boundary checks.
  - Define expected call ordering and expected no-call assertions.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-060a-design_060b-design_archive-import-coordinator-and-test-contract_gemini.md`

### Do Not

- Do not implement coordinator production code.
- Do not implement coordinator tests.
- Do not implement filesystem staging.
- Do not implement dataset repository writes.
- Do not implement validation repository writes.
- Do not add audit success writes.
- Do not change DB schema or migrations.
- Do not modify `repository/strategy_import_adapter.py` unless documenting a discovered design blocker requires a tiny comment-free correction, and only with explicit explanation in the report.
- Do not add dependencies.
- Do not touch UI, CLI, backtest engine, validation engine, or strategy generator.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Acceptance Criteria

1. Both deliverables are design-only Markdown files.
2. Coordinator architecture keeps UI/service/repository/filesystem/audit boundaries explicit.
3. Transaction and cleanup sequencing is precise enough to implement later without guessing.
4. Test contract includes success, rollback, cleanup, duplicate, and failure-audit cases.
5. Malformed legacy strategy JSON and final file move failure are explicitly handled as known design risks.
6. No production code or test code is added or changed unless a tiny documented typo fix is unavoidable.
7. Full suite, `git diff --check`, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1
git status --short
```

Expected:

- Full suite passes.
- `git diff --check` has no errors.
- Agent status shows the 060A/060B completion report as latest report.
- `git status --short` shows only docs/report files within this task scope.

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
