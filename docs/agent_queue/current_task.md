# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 060Q-Impl + 060R-Design - Archive Export Service Boundary and UI/Round-Trip Contract Design.

## Context Level

Level 3 for 060Q implementation and Level 2 for 060R design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `archive/builder.py`
9. `archive/exporter.py`
10. `archive/verifier.py`
11. `tests/test_archive_exporter.py`
12. `app/services/report_service.py`
13. `app/ui/main_window.py`
14. `docs/reproducibility_foundation_signoff_060P.md`
15. `docs/review_notes/2026-06-07_task-060o-impl_060p-signoff_coordinator-acceptance-tests-and-foundation-signoff_codex-review.md`
16. This task file

## Context

The reproducibility foundation is accepted after Codex tightened the coordinator acceptance tests. The next safe step is not full import UI. First create a narrow application/service boundary for archive export, then design the UI trigger and round-trip acceptance contract.

Keep UI widgets passive. Archive collection/export orchestration must live in `app/services` or `archive`, not in `app/ui/main_window.py`.

## Scope

### Task 060Q-Impl - Archive Export Service Boundary

Do:

- Add a small service module, suggested path `app/services/archive_export_service.py`.
- Implement an `ArchiveExportService` that wraps `ArchiveBuilder` + `ArchiveExporter`.
- The service should accept dependency-injected archive data source objects rather than querying UI state directly.
- Suggested public method:
  - `export_strategy_archive(strategy_uid, dataset_snapshot_path, output_dir, disclaimer_text, experiment_name=None) -> pathlib.Path`
- Keep the service free of PySide6 imports.
- Add focused tests, suggested path `tests/test_archive_export_service.py`, using a fake archive data source and a temp snapshot file.
- Test success writes a verifiable archive folder.
- Test missing validation/strategy/dataset failures propagate as typed archive errors or service-level errors without writing partial success claims.
- Update `app/services/__init__.py` only if that package already exports service classes in a similar style.
- Update `docs/changelog.md`.

Do not:

- Do not modify `ArchiveExporter` unless a test exposes a real bug.
- Do not wire a real UI button yet unless it is only passive/no-op and clearly not a full workflow.
- Do not add zip export.
- Do not add import UI.
- Do not read active strategy data directly from PySide widgets inside the service.

Acceptance criteria:

1. Archive export orchestration has a service-layer entry point.
2. The service has no UI imports.
3. Service tests prove successful export can be verified by `ArchiveVerifier`.
4. Failure tests prove missing required archive inputs do not look like successful exports.

Verification:

- Run:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_archive_export_service.py tests\test_archive_exporter.py tests\test_archive_builder.py -q`
  - `.\.venv\Scripts\python.exe -m pytest -q`
  - `git diff --check`
  - `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1`

### Task 060R-Design - UI Trigger and Round-Trip Acceptance Contract

Do:

- Create a design document, suggested path `docs/archive_export_ui_and_roundtrip_contract_060R.md`.
- Define the future UI trigger shape for Results page archive export:
  - where the button/action appears;
  - what data the UI passes into `ArchiveExportService`;
  - how missing active strategy/dataset/validation state is surfaced;
  - where archive folders are written under the project folder;
  - what success/failure log messages should say.
- Define a future round-trip acceptance test plan:
  1. export strategy archive;
  2. verify manifest;
  3. import through `ArchiveImportCoordinator`;
  4. assert imported strategy/dataset/audit state;
  5. assert no UI/engine boundary violation.
- Recommend the next two-task batch after 060Q/060R.

Do not:

- Do not implement full UI wiring in this design task.
- Do not implement import round-trip tests yet.
- Do not add broker/live trading scope.

## Completion Report

After completion, create:

`docs/agent_reports/2026-06-07_task-060q-impl_060r-design_archive-export-service-and-ui-roundtrip-contract_deepseek.md`

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
