# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 061E - Reproducibility Milestone Closure and Final Changelog.

## Context Level

Level 3 because this is milestone acceptance/signoff.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `docs/reproducibility_milestone_closure_criteria_061D.md`
9. `docs/review_notes/2026-06-08_task-061c-impl_061d-design_full-ui-archive-export-wiring-and-milestone-closure-design_codex-review.md`
10. `app/ui/main_window.py`
11. `app/services/archive_export_service.py`
12. `app/services/archive_project_data_source.py`
13. `tests/test_wfe_ui_wiring.py`
14. `tests/test_archive_roundtrip_acceptance.py`
15. This task file

## Context

061C implemented full UI archive export wiring. Codex found and fixed critical issues in `DataService.import_file()` and validation UID handling, then verified:

- UI archive wiring tests: 19 passed.
- Data import/repository persistence tests: 37 passed.
- Archive adapter + service + round-trip tests: 18 passed.
- Full suite: 1256 passed.

The reproducibility milestone can be considered for closure only after a final signoff document confirms the closure criteria. This task is signoff/documentation only.

## Scope

### Task 061E - Reproducibility Milestone Closure and Final Changelog

Do:

- Create `docs/reproducibility_milestone_closure_061E.md`.
- Confirm each 061D closure criterion with evidence:
  - UI export button and handler wiring;
  - `ArchiveExportService.export_strategy_archive()` called on valid path;
  - failure guards for no selection, missing validation, failed validation, missing dataset metadata, and missing snapshot file;
  - archive backend verifier/round-trip coverage;
  - no UI direct SQLite queries;
  - no live trading or investment claims.
- Explicitly state what remains optional after closure:
  - zip archive export;
  - import UI;
  - success audit log writes;
  - batch/concurrent export.
- Update `docs/changelog.md` and `docs/task_board.md` to mark the reproducibility milestone closed only if all evidence is present.
- Keep this as documentation/signoff only.

Do not:

- Do not modify production code.
- Do not add new features.
- Do not broaden scope into live trading, broker API, portfolio backtest, zip export, or import UI.
- Do not claim strategy performance, investment value, or live-trading readiness.

## Acceptance Criteria

1. Closure document maps every criterion to concrete evidence.
2. Changelog and task board clearly distinguish closed reproducibility archive milestone from optional future polish.
3. No production code changes.
4. Verification commands pass.

## Verification

Run:

- `.\.venv\Scripts\python.exe -m pytest tests\test_wfe_ui_wiring.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests\test_archive_project_data_source.py tests\test_archive_export_service.py tests\test_archive_roundtrip_acceptance.py -q`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1`

## Completion Report

After completion, create:

`docs/agent_reports/2026-06-08_task-061e-signoff_reproducibility-milestone-closure-and-final-changelog_deepseek.md`

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
