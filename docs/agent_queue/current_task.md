# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 060Y-Design + 060Z-Signoff - Full UI Export Boundary Design and Reproducibility Milestone Acceptance.

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
8. `app/services/archive_project_data_source.py`
9. `app/services/archive_export_service.py`
10. `app/ui/main_window.py`
11. `repository/strategy_repo.py`
12. `repository/dataset_repo.py`
13. `tests/test_archive_project_data_source.py`
14. `tests/test_archive_roundtrip_acceptance.py`
15. `docs/archive_full_ui_export_delegation_design_060X.md`
16. `docs/review_notes/2026-06-08_task-060w-impl_060x-design_project-archive-data-source-and-ui-export-delegation_codex-review.md`
17. This task file

## Context

060W implemented `ProjectArchiveDataSource`. Codex tightened it for `PipelineResult` dataclass conversion, package export, and stronger UI-boundary tests.

Important blocker before full UI export implementation:

- Existing `StrategyRepository.list_all()` returns `Strategy` objects, not raw rows with `strategy_json`.
- `ProjectArchiveDataSource` currently expects a provider of row-like dicts containing `strategy_json`.
- Full UI export must not fake or silently invent strategy UID/dataset snapshot data.

Therefore this round is design/signoff only. Do not implement full UI export yet.

## Scope

### Task 060Y-Design - Full UI Export Boundary Design

Do:

- Create a design document, suggested path `docs/archive_full_ui_export_boundary_design_060Y.md`.
- Resolve the raw-row provider boundary required by `ProjectArchiveDataSource`.
- Compare at least two options:
  1. add a repository read method that returns raw archive export rows;
  2. add a dedicated archive repository adapter that queries SQLite directly;
  3. extend saved `Strategy`/provenance model only if justified.
- Recommend one option with reasons.
- Define exact data contracts for:
  - strategy UID lookup;
  - dataset ID and snapshot path lookup;
  - validation result lookup;
  - output folder path;
  - user-facing errors.
- Define focused future tests for the selected option.
- Explicitly state what remains out of scope.

Do not:

- Do not implement the selected option.
- Do not modify `MainWindow`.
- Do not add zip, import UI, broker/live trading, or portfolio scope.

### Task 060Z-Signoff - Reproducibility Milestone Acceptance

Do:

- Create a milestone acceptance document, suggested path `docs/reproducibility_milestone_acceptance_060Z.md`.
- Summarize the accepted archive/reproducibility chain:
  - manifest/verifier;
  - dataset snapshot;
  - builder/exporter;
  - importer/coordinator;
  - repository adapters;
  - audit;
  - export service;
  - round-trip acceptance;
  - guarded UI surface;
  - project archive data source adapter.
- List remaining gaps and classify them:
  - required before full UI export;
  - optional polish;
  - explicitly out of scope.
- Recommend the next two-task batch after 060Y/060Z.
- Update `docs/changelog.md` and `docs/task_board.md`.

Do not:

- Do not declare live trading readiness.
- Do not claim strategy performance or investment value.
- Do not mark full UI export complete.

## Verification

Run:

- `.\.venv\Scripts\python.exe -m pytest tests\test_archive_project_data_source.py tests\test_archive_roundtrip_acceptance.py -q`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1`

## Completion Report

After completion, create:

`docs/agent_reports/2026-06-08_task-060y-design_060z-signoff_full-ui-export-boundary-and-reproducibility-acceptance_deepseek.md`

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
