# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 060U-Impl + 060V-Design - Results Archive Export Guard Wiring and Data-Source Adapter Design.

## Context Level

Level 2 for 060U implementation and Level 3 for 060V design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `app/ui/main_window.py`
9. `app/services/archive_export_service.py`
10. `app/services/__init__.py`
11. `tests/test_archive_roundtrip_acceptance.py`
12. `docs/archive_ui_wiring_readiness_contract_060T.md`
13. `docs/review_notes/2026-06-08_task-060s-impl_060t-design_archive-roundtrip-and-ui-readiness_codex-review.md`
14. This task file

## Context

060S proved backend export -> verify -> import round-trip. Codex tightened it to assert dataset `snapshot_hash` persistence and final moved CSV contents.

The next safe UI step is not full production archive export. Add narrow Results-page guard/button wiring and log behavior, while designing the real data-source adapter needed for full export later.

## Scope

### Task 060U-Impl - Results Archive Export Guard Wiring

Do:

- Add an "Export Archive" button on the Results page near existing export buttons.
- Keep the button/handler narrow and guard-first:
  - no selected strategy -> log or show a clear user-facing message;
  - missing project root -> log/message;
  - missing strategy UID / dataset snapshot path / validation pass status -> log/message;
  - only call `ArchiveExportService.export_strategy_archive()` when all required inputs are present.
- Add helper methods on `MainWindow` if needed, but keep archive orchestration out of the UI.
- If the current UI does not yet expose reliable strategy UID/dataset snapshot path, do not fake a successful export. Leave the handler guarded and explicit.
- Add focused UI wiring tests using existing UI test patterns. Suggested checks:
  1. Results page has an Export Archive button;
  2. clicking with no valid selection does not call `ArchiveExportService`;
  3. success path can be tested by monkeypatching a small resolver/service seam, not by building real archives in UI tests;
  4. service module still has no PySide6 imports.
- Update `docs/changelog.md`.

Do not:

- Do not implement full import UI.
- Do not move archive builder/exporter logic into `main_window.py`.
- Do not fabricate strategy UID, dataset path, or validation state to force a green export.
- Do not add zip support or success audit behavior.

Acceptance criteria:

1. UI has a visible/exportable Results-page archive action surface.
2. Guard failures are explicit and do not call the archive export service.
3. Any success-path UI test uses a seam/monkeypatch and proves delegation only.
4. No archive/core logic is placed in PySide widgets.

Verification:

- Run:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wfe_ui_wiring.py tests\test_archive_export_service.py -q`
  - If a new UI test file is added, include it explicitly.
  - `.\.venv\Scripts\python.exe -m pytest -q`
  - `git diff --check`
  - `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1`

### Task 060V-Design - Archive UI Data-Source Adapter Design

Do:

- Create a design document, suggested path `docs/archive_ui_data_source_adapter_design_060V.md`.
- Define the future adapter that will provide `ArchiveExportService` with real strategy/dataset/validation data from the project repositories.
- Specify exact inputs/outputs:
  - selected strategy UID;
  - dataset ID/path;
  - validation pass/fail result;
  - output archive folder;
  - disclaimer policy.
- Define failure modes and user-facing messages.
- Define the next two-task batch after 060U/060V.

Do not:

- Do not implement the adapter in this design task.
- Do not broaden to import UI, zip archives, live trading, or portfolio workflows.

## Completion Report

After completion, create:

`docs/agent_reports/2026-06-08_task-060u-impl_060v-design_results-archive-export-guard-and-data-source-adapter_deepseek.md`

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
