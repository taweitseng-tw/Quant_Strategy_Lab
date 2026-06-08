# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 060W-Impl + 060X-Design - ProjectArchiveDataSource Adapter Slice and Full UI Export Delegation Design.

## Context Level

Level 3 for 060W implementation and Level 2 for 060X design.

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
9. `app/ui/main_window.py`
10. `repository/strategy_repo.py`
11. `repository/dataset_repo.py`
12. `app/services/project_service.py`
13. `docs/archive_ui_data_source_adapter_design_060V.md`
14. `docs/review_notes/2026-06-08_task-060u-impl_060v-design_results-archive-export-guard-and-data-source-adapter_codex-review.md`
15. This task file

## Context

060U added a guarded Results-page "Export Archive" action surface. Codex fixed it so project root resolution uses `ProjectService` and validation guards support real `PipelineResult` dataclasses.

The next step is to implement the project data-source adapter needed by `ArchiveExportService`, without yet enabling full UI export from `MainWindow`.

## Scope

### Task 060W-Impl - ProjectArchiveDataSource Adapter Slice

Do:

- Add a service/repository adapter module, suggested path `app/services/archive_project_data_source.py`.
- Implement a small `ProjectArchiveDataSource` that satisfies the `ArchiveDataSource` protocol used by `ArchiveBuilder`.
- It should be dependency-injected and testable. Prefer constructor dependencies such as:
  - strategy repository or strategy rows provider;
  - dataset repository or dataset rows provider;
  - validation result provider.
- Implement:
  - `get_strategy(strategy_uid) -> dict | None`;
  - `get_dataset(dataset_id) -> dict | None`;
  - `get_validation_result(strategy_uid) -> dict | None`.
- UID lookup must use `strategy_uid` inside stored `strategy_json`, not display name.
- Validation lookup must preserve pass/fail status and be compatible with `PipelineResult` dataclasses or dicts.
- Add focused tests, suggested path `tests/test_archive_project_data_source.py`.
- Update `app/services/__init__.py` only if consistent with service package exports.
- Update `docs/changelog.md`.

Do not:

- Do not wire full UI export yet.
- Do not add import UI.
- Do not add zip support.
- Do not query PySide widgets from the adapter.
- Do not silently invent missing dataset IDs, strategy UIDs, or validation results.

Acceptance criteria:

1. Adapter finds strategy rows by `strategy_uid` embedded in `strategy_json`.
2. Adapter returns `None` for missing UID, malformed JSON, missing dataset, or missing validation.
3. Adapter has no PySide6/UI imports.
4. Tests cover happy path and at least three failure paths.

Verification:

- Run:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_archive_project_data_source.py tests\test_archive_export_service.py -q`
  - `.\.venv\Scripts\python.exe -m pytest -q`
  - `git diff --check`
  - `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1`

### Task 060X-Design - Full UI Export Delegation Design

Do:

- Create a design document, suggested path `docs/archive_full_ui_export_delegation_design_060X.md`.
- Define exactly how `MainWindow._handle_export_archive()` should delegate to:
  - selection resolver;
  - `ProjectArchiveDataSource`;
  - `ArchiveExportService`;
  - output path resolver.
- Define the success-path UI test plan using monkeypatch seams.
- Define failure handling and cleanup expectations.
- Recommend the next two-task batch after 060W/060X.

Do not:

- Do not implement full UI export in this design task.
- Do not add live trading, broker, zip, or portfolio scope.

## Completion Report

After completion, create:

`docs/agent_reports/2026-06-08_task-060w-impl_060x-design_project-archive-data-source-and-ui-export-delegation_deepseek.md`

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
