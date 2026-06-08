# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 061A-Impl + 061B-Design - Raw Archive Repository Providers and Full UI Export Wiring Design.

## Context Level

Level 2 for 061A implementation.

Level 3 for 061B design because it touches UI-service boundary and milestone acceptance sequencing.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `repository/strategy_repo.py`
9. `repository/dataset_repo.py`
10. `app/services/archive_project_data_source.py`
11. `app/services/archive_export_service.py`
12. `app/ui/main_window.py`
13. `tests/test_archive_project_data_source.py`
14. `tests/test_archive_roundtrip_acceptance.py`
15. `docs/archive_full_ui_export_boundary_design_060Y.md`
16. `docs/reproducibility_milestone_acceptance_060Z.md`
17. `docs/review_notes/2026-06-08_task-060y-design_060z-signoff_full-ui-export-boundary-and-reproducibility-acceptance_codex-review.md`
18. This task file

## Context

060Y/060Z accepted the reproducibility foundation at the engine, adapter, service, and round-trip acceptance layers. Full UI archive export is not accepted yet.

The immediate blocker is that `ProjectArchiveDataSource` expects row-like strategy dictionaries with `strategy_json`, but `StrategyRepository.list_all()` returns `Strategy` objects. The UI must not query SQLite directly.

This batch should make the repository provider boundary real and testable, then design the final UI-service wiring. Do not close the milestone in this batch.

## Scope

### Task 061A-Impl - Raw Archive Repository Providers

Do:

- Add `StrategyRepository.list_all_raw()` returning `list[dict]`.
- The returned dicts must include at least:
  - `id`
  - `project_id`
  - `name`
  - `strategy_json`
  - `created_at`
  - `updated_at`
- Preserve existing `StrategyRepository.list_all()` behavior.
- Add `DatasetRepository.get_raw_by_id(dataset_id: int) -> dict | None`.
- The returned dataset dict must include `normalized_path` and all existing dataset metadata columns.
- Keep SQL access inside repository classes.
- Add focused repository tests for:
  - `list_all_raw()` returns raw dict rows ordered newest first, matching `list_all()` ordering.
  - `list_all_raw()` preserves raw `strategy_json` as a string.
  - `get_raw_by_id()` returns a dict for an existing dataset.
  - `get_raw_by_id()` returns `None` for a missing dataset.
- Update `docs/changelog.md` and `docs/task_board.md`.

Do not:

- Do not modify `MainWindow` in 061A.
- Do not change strategy serialization semantics.
- Do not add direct SQLite access outside repository classes.
- Do not implement archive zip support or import UI.

### Task 061B-Design - Full UI Export Wiring Design

Do:

- Create `docs/archive_full_ui_export_wiring_design_061B.md`.
- Design the exact `MainWindow._handle_export_archive()` wiring for a future implementation.
- The design must specify:
  - how to instantiate/use `StrategyRepository.list_all_raw()`;
  - how to resolve dataset metadata using `DatasetRepository.get_raw_by_id()`;
  - how to resolve dataset snapshot path from `normalized_path` relative to the project root when needed;
  - how to provide validation results keyed by `strategy_uid`;
  - how `ProjectArchiveDataSource` should be constructed;
  - how `ArchiveExportService` should be called;
  - all user-facing error messages;
  - focused future tests for the UI-service wiring.
- Explicitly state that full UI export remains unimplemented until the next implementation task.

Do not:

- Do not implement the UI export wiring in this batch.
- Do not mark the reproducibility milestone fully closed.
- Do not claim live trading readiness or investment value.

## Acceptance Criteria

1. Repository raw provider methods are implemented without breaking existing model-returning methods.
2. Repository tests cover success and missing-row paths.
3. No UI file is modified.
4. 061B design gives enough detail for the next agent to implement UI export without inventing architecture.
5. Documentation clearly says full UI export is still pending implementation.

## Verification

Run:

- `.\.venv\Scripts\python.exe -m pytest tests\test_strategy_repo.py tests\test_dataset_repo.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests\test_archive_project_data_source.py tests\test_archive_roundtrip_acceptance.py -q`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1`

## Completion Report

After completion, create:

`docs/agent_reports/2026-06-08_task-061a-impl_061b-design_raw-archive-repository-providers-and-ui-export-wiring-design_deepseek.md`

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
