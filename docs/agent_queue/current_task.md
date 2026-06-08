# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 061C-Impl + 061D-Design - Full UI Archive Export Wiring and Milestone Closure Design.

## Context Level

Level 3 for 061C because it touches UI-service wiring and archive export behavior.

Level 3 for 061D because it defines milestone closure criteria.

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
9. `app/services/archive_project_data_source.py`
10. `app/services/archive_export_service.py`
11. `app/services/data_service.py`
12. `app/services/strategy_persistence_service.py`
13. `repository/strategy_repo.py`
14. `repository/dataset_repo.py`
15. `tests/test_wfe_ui_wiring.py`
16. `tests/test_archive_project_data_source.py`
17. `tests/test_archive_export_service.py`
18. `docs/archive_full_ui_export_wiring_design_061B.md`
19. `docs/review_notes/2026-06-08_task-061a-impl_061b-design_raw-archive-repository-providers-and-ui-export-wiring-design_codex-review.md`
20. This task file

## Context

061A added `StrategyRepository.list_all_raw()` and `DatasetRepository.get_raw_by_id()`. 061B designed the final UI archive export wiring. Codex amended the design to remove an incorrect provider placeholder and clarified that repository access must stay behind service/repository boundaries.

Important current-state constraints:

- `DataService` currently stores `DatasetRepository` as `_dataset_repo`; add a narrow service-layer accessor if the UI needs it.
- `StrategyPersistenceService` currently stores `StrategyRepository` as `_repo`; add a narrow method or property if the UI needs raw export rows.
- `MainWindow._handle_export_archive()` currently performs guards only and logs that full wiring is pending.
- Do not query SQLite directly from `MainWindow`.
- Do not mark the milestone closed until the implemented UI export is verified and accepted.

## Scope

### Task 061C-Impl - Full UI Archive Export Wiring

Do:

- Add the smallest service-layer accessors needed for UI archive export:
  - Prefer `DataService.get_dataset_raw_by_id(dataset_id: int) -> dict | None` over exposing `_dataset_repo` directly.
  - Prefer `StrategyPersistenceService.list_all_raw() -> list[dict]` or another narrow service method over exposing `_repo` directly.
- Wire `MainWindow._handle_export_archive()` to:
  - preserve existing guard behavior and user messages;
  - resolve `strategy_uid` from the selected strategy/result without inventing missing data;
  - resolve `dataset_id` from validated strategy provenance or result payload;
  - resolve dataset metadata via `DatasetRepository.get_raw_by_id()` through service-layer access;
  - resolve `normalized_path` relative to the project root when needed;
  - verify the dataset snapshot file exists before export;
  - construct `ProjectArchiveDataSource` with `list_all_raw`, `get_raw_by_id`, and a UID-aware validation provider;
  - call `ArchiveExportService.export_strategy_archive()`;
  - show/log success and failure messages.
- Add focused tests, preferably in `tests/test_wfe_ui_wiring.py` or a dedicated UI wiring test file, for:
  - successful `_handle_export_archive()` calls `ArchiveExportService.export_strategy_archive()`;
  - missing dataset ID blocks export with a warning;
  - missing dataset metadata blocks export with a warning;
  - missing snapshot file blocks export with a warning;
  - mismatched validation UID blocks export and does not call the service.
- Update `docs/changelog.md` and `docs/task_board.md`.

Do not:

- Do not query SQLite directly from UI code.
- Do not add archive zip support.
- Do not add import UI.
- Do not weaken the existing validation-passed guard.
- Do not claim live trading readiness or investment value.

### Task 061D-Design - Milestone Closure Criteria

Do:

- Create `docs/reproducibility_milestone_closure_criteria_061D.md`.
- Define exact criteria for Codex to close the reproducibility milestone after 061C, including:
  - UI export happy path;
  - failure guards;
  - generated archive verification;
  - no UI direct SQLite access;
  - no live trading or investment claims;
  - required tests and smoke commands.
- List what remains optional after closure, such as zip export, import UI, and success audit writes.
- Recommend the next two-task batch only if 061C passes.

Do not:

- Do not declare the milestone closed in 061D.
- Do not broaden scope into zip export, import UI, broker/live trading, or portfolio features.

## Acceptance Criteria

1. `_handle_export_archive()` performs a real archive export through `ArchiveExportService`.
2. UI code does not perform direct SQL or repository connection access.
3. Export fails clearly when required strategy UID, dataset ID, dataset metadata, snapshot path, or validation UID is missing.
4. Tests prove the service is called only on the valid path.
5. Existing archive adapter, service, round-trip, and UI guard tests still pass.
6. 061D defines closure criteria without declaring closure.

## Verification

Run:

- `.\.venv\Scripts\python.exe -m pytest tests\test_wfe_ui_wiring.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests\test_archive_project_data_source.py tests\test_archive_export_service.py tests\test_archive_roundtrip_acceptance.py -q`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1`

## Completion Report

After completion, create:

`docs/agent_reports/2026-06-08_task-061c-impl_061d-design_full-ui-archive-export-wiring-and-milestone-closure-design_deepseek.md`

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
