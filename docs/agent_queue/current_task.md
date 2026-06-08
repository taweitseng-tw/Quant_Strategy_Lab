# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 060S-Impl + 060T-Design - Export/Import Round-Trip Acceptance and UI Wiring Readiness.

## Context Level

Level 3 for 060S implementation and Level 2 for 060T design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `app/services/archive_export_service.py`
9. `archive/import_coordinator.py`
10. `archive/importer.py`
11. `archive/verifier.py`
12. `archive/stager.py`
13. `archive/manifest.py`
14. `repository/strategy_import_adapter.py`
15. `repository/dataset_import_adapter.py`
16. `repository/import_audit_repo.py`
17. `tests/test_archive_export_service.py`
18. `tests/test_archive_import_coordinator_acceptance.py`
19. `docs/archive_export_ui_and_roundtrip_contract_060R.md`
20. `docs/review_notes/2026-06-08_task-060q-impl_060r-design_archive-export-service-and-ui-roundtrip-contract_codex-review.md`
21. This task file

## Context

060Q added a service-layer `ArchiveExportService`. Codex tightened it by exporting it from `app.services` and adding tests for failure cause preservation, no success manifest on failed inputs, and no UI imports.

The next highest-value step is to prove the archive can make a backend round trip: export -> verify -> import -> assert repository state. Do this before wiring a visible UI button.

## Scope

### Task 060S-Impl - Export/Import Round-Trip Acceptance

Do:

- Add a focused acceptance test file, suggested path `tests/test_archive_roundtrip_acceptance.py`.
- Build a deterministic fake export data source that works with `ArchiveExportService`.
- Export an archive folder to a temp path.
- Verify the exported folder with `ArchiveManifest.read_from_folder()` + `ArchiveVerifier.verify_all()`.
- Import the exported folder into a fresh in-memory SQLite project using `ArchiveImportCoordinator`, real `StrategyRepoAdapter`, real `DatasetRepoAdapter`, real `AuditLogRepositoryAdapter`, and real `ArchiveStager` where practical.
- Assert:
  1. `ImportResult.success is True`;
  2. imported strategy row exists and has the same `strategy_uid`;
  3. imported dataset row exists with expected symbol/timeframe and snapshot hash when available;
  4. no failed `ImportAuditLog` rows were written;
  5. coordinator module remains free of UI/engine imports.
- Use a small adapter/helper inside the test only if exported archive metadata needs to be converted into existing import DTOs.
- Keep this as test/acceptance coverage. Do not broaden production import/export behavior unless a real bug is exposed.
- Update `docs/changelog.md`.

Do not:

- Do not add UI button wiring in this task.
- Do not add zip support.
- Do not add success audit behavior.
- Do not change archive file format unless the round-trip test exposes a real format mismatch, and if so keep the fix minimal.
- Do not import PySide6, backtest engine, or validation engine into archive coordinator/service modules.

Acceptance criteria:

1. A backend round-trip acceptance test proves exported archives can be verified and imported into a clean DB.
2. The test uses real SQLite-backed import adapters.
3. The test would fail if manifest hashes, snapshot staging, duplicate guards, or transaction commit are broken.

Verification:

- Run:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_archive_roundtrip_acceptance.py tests\test_archive_export_service.py tests\test_archive_import_coordinator_acceptance.py -q`
  - `.\.venv\Scripts\python.exe -m pytest -q`
  - `git diff --check`
  - `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1`

### Task 060T-Design - UI Wiring Readiness Contract

Do:

- Create a design document, suggested path `docs/archive_ui_wiring_readiness_contract_060T.md`.
- Define exactly what data source/adapter the future Results-page UI must pass into `ArchiveExportService`.
- Define how the UI discovers:
  - active project root;
  - selected strategy UID;
  - dataset snapshot path;
  - validation result presence/pass status;
  - destination archive folder.
- Define button enable/disable rules and log messages.
- Define a small future UI wiring test plan, but do not implement UI in this task.
- Recommend the next two-task batch after 060S/060T.

Do not:

- Do not implement full UI wiring.
- Do not add import UI.
- Do not add live trading, broker, zip, or portfolio scope.

## Completion Report

After completion, create:

`docs/agent_reports/2026-06-08_task-060s-impl_060t-design_archive-roundtrip-and-ui-readiness_deepseek.md`

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
