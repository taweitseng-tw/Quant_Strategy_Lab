# Changelog

## 2026-06-11 - Tasks 403-408: Elimination Rule Configuration Design and Contract

### Added
- `docs/elimination_rule_config_design_403_408.md`: Added a reviewed elimination configuration design covering existing engine, strategy service, ranking UI, validation pipeline, current gaps, next implementation slice, and deterministic test plan.

### Changed
- `docs/task_board.md`: Moved Tasks 403-408 to Done and clarified Tasks 409-414 as the OOS stability gate control implementation slice.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_elimination_config_widget.py tests/test_elimination.py tests/test_strategy_service_elimination_config.py -q` - 55 passed.
- `git diff --check` passed with CRLF notices only. No production code changed.

## 2026-06-11 - Tasks 397-402: Post-v0.3.0-dev Next Milestone Decision

### Added
- `docs/post_v0.3.0_next_milestone_decision_397_402.md`: Added a compact three-option next milestone decision and recommended Strategy Quality / Robustness Expansion.

### Changed
- `docs/task_board.md`: Current milestone moved to Strategy Quality / Robustness Expansion, Tasks 397-402 added to Done, and six concrete Next task batches were added.

### Verification
- Planning/docs-only change. No source code, binaries, upload, push, or tag operation was performed.
- `git diff --check` passed with CRLF notices only.

## 2026-06-11 - Tasks 391-396: Final v0.3.0-dev Acceptance Audit

### Added
- `docs/v0.3.0-dev_final_acceptance_audit_391_396.md`: Added final local developer pre-release acceptance audit with exact tag, zip, smoke test, not-tested, remaining-risk, and disclaimer evidence.

### Changed
- `docs/task_board.md`: Added Tasks 391-396 to Done and moved the current milestone to post-v0.3.0-dev next milestone selection.

### Verification
- `git show --no-patch --format=fuller v0.3.0-dev` confirmed tag object `ed34d2b5373c3fb8417839b9f06b67e2f706cebe` targets commit `bd94e90bd82839f8e47d21bbda5dc80cc04c8003`.
- `git check-ignore -v release_artifacts/QuantStrategyLab-v0.3.0-dev-windows-onedir.zip` confirmed the release zip is ignored by `release_artifacts/`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_data_page_wiring.py tests/test_quality_checker.py tests/test_candlestick_chart.py tests/test_archive_import_preview_contract_acceptance.py -q` - 98 passed in 10.86s.
- `git diff --check` passed with CRLF notices only. No binaries were modified, uploaded, pushed, or rebuilt.

## 2026-06-11 - Tasks 385-390: v0.3.0-dev Evaluator Readiness Closure

### Added
- `docs/v0.3.0-dev_evaluator_readiness_closure_385_390.md`: Added compact evaluator readiness evidence with release artifact status, smoke command, known limits, feedback questions, and research-only disclaimer.

### Changed
- `docs/release_notes_v0.3.0-dev.md`: Added local release artifact status and updated smoke verification to the current 98-test readiness command.
- `docs/desktop_evaluator_walkthrough_271_276.md`: Added import UX and quality checker smoke command coverage.
- `docs/context_brief.md`: Updated current milestone and release artifact state.
- `docs/task_board.md`: Added Tasks 385-390 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_data_page_wiring.py tests/test_quality_checker.py tests/test_candlestick_chart.py tests/test_archive_import_preview_contract_acceptance.py -q` - 98 passed.
- `git check-ignore -v release_artifacts/QuantStrategyLab-v0.3.0-dev-windows-onedir.zip` confirmed the zip is ignored by `release_artifacts/`.
- Local tag `v0.3.0-dev` confirmed present. No binaries were modified or uploaded.

## 2026-06-11 - Codex Review Fix: Large-File Import UX Hardening

### Added
- `ImportWorker` now supports background OHLCV imports without sharing the UI thread's project SQLite connection.
- Focused async import persistence smoke coverage was added for existing UI acceptance paths.
- Import worker progress stages now surface large-file import progress without blocking the UI thread.
- Import success messaging now includes row count, symbol, timeframe, date range, quality status, warning count, and chart subset note.
- `DataService.extract_warning_details()` adds actionable warning details for large close jumps and largest time gaps.
- `check_quality()` now accepts optional `session_start` / `session_end` parameters for conservative session-break gap classification.
- `docs/large_file_import_ux_acceptance.md`: Added a compact acceptance summary for the six-round import UX series.

### Changed
- `DataService.persist_metadata()` centralizes best-effort dataset metadata persistence on the UI/service side after background imports finish.
- Data page import wiring now persists imported dataset metadata after worker success while keeping chart rendering guarded to the most recent 2,000 rows.
- Data page quality tooltip now appends actionable warning detail lines when warnings exist.
- `docs/task_board.md`: Added the large-file import UX hardening review fix to Done.

### Fixed
- Structural quality-check failures now keep `issue_counts` consistent with structured issues.
- Blank session strings are treated like missing session bounds instead of raising during gap checks.
- Warning detail extraction now prefers checker-approved structured samples before falling back to DataFrame recalculation.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_data_page_wiring.py tests/test_candlestick_chart.py tests/test_sample_data_workflow_smoke.py tests/test_quality_checker.py tests/test_dataset_persistence_wiring.py tests/test_txf_import.py tests/test_export_persistence_acceptance.py tests/test_active_dataset.py -q` - 115 passed.

## 2026-06-11 - Tasks 379-384: v0.3.0-dev Evaluator Share Message

### Added
- `docs/v0.3.0-dev_evaluator_share_message_379_384.md`: Added an ASCII ready-to-paste evaluator share message for the local `v0.3.0-dev` Windows developer pre-release zip, including run steps, known limits, feedback prompts, and research-only disclaimer.

### Changed
- `docs/task_board.md`: Added Tasks 379-384 to Done.

### Verification
- `release_artifacts/QuantStrategyLab-v0.3.0-dev-windows-onedir.zip` exists locally and is gitignored.
- Zip size is `128,770,261` bytes / `122.8 MiB`.
- `git diff --check` passed.
- No upload, push, or remote configuration was executed.
## 2026-06-11 - Tasks 373-378: v0.3.0-dev External Sharing Decision

### Added
- `docs/v0.3.0-dev_external_sharing_decision_373_378.md`: Added an ASCII decision document comparing local-only, direct transfer, cloud storage, and future remote/release sharing paths for the local `v0.3.0-dev` zip.

### Changed
- `docs/task_board.md`: Added Tasks 373-378 to Done.

### Verification
- `release_artifacts/QuantStrategyLab-v0.3.0-dev-windows-onedir.zip` exists locally and is gitignored.
- Zip size is `128,770,261` bytes / `122.8 MiB`.
- `git diff --check` passed.
- No upload, push, or remote configuration was executed.
## 2026-06-10 - Tasks 367-372: Local Release Zip Evidence

### Added
- `docs/local_release_zip_evidence_367_372.md`: Added an ASCII evidence record for the local `v0.3.0-dev` zip archive, including build result, launch smoke result, zip path, exact zip size, ignore status, and cleanup state.

### Changed
- `docs/task_board.md`: Added Tasks 367-372 to Done.

### Verification
- `release_artifacts/QuantStrategyLab-v0.3.0-dev-windows-onedir.zip` exists locally and is gitignored.
- Zip size is `128,770,261` bytes / `122.8 MiB`.
- `git check-ignore` confirmed the zip is ignored.
- `git diff --check` passed.
- No push or upload was executed.
## 2026-06-10 - Tasks 361-366: Optional Local Release Zip Checklist

### Added
- `docs/local_release_zip_checklist_361_366.md`: Added an ASCII documentation-only checklist for manually building, zipping, verifying, and cleaning the local `v0.3.0-dev` Windows onedir package outside git.

### Changed
- `docs/task_board.md`: Added Tasks 361-366 to Done.

### Verification
- `git status --short` checked current dirty scope.
- `git diff --check` passed.
- No build, zip, push, upload, or generated artifact was created.
## 2026-06-10 - Tasks 355-360: Release Artifact Archive Plan

### Added
- `docs/release_artifact_archive_plan_355_360.md`: Added an ASCII archive plan comparing local-only, manual local zip, later remote tag push, and future release artifact upload paths for sharing the `v0.3.0-dev` package.

### Changed
- `.gitignore`: Added `release_artifacts/` so local zip archives stay out of source control.
- `docs/task_board.md`: Added Tasks 355-360 to Done and set Next to None.

### Verification
- `git status --short` checked current dirty scope.
- `git remote -v` showed no configured remote.
- `git diff --check` passed.
- No push, upload, zip archive, or build artifact was created.
## 2026-06-10 - Tasks 349-354: v0.3.0-dev Publish or Archive Decision

### Added
- `docs/v0.3.0-dev_publish_or_archive_decision_349_354.md`: Added an ASCII decision document recording the local `v0.3.0-dev` tag object, target commit, no-remote state, no-push decision, later push command, and remaining archive/publish risks.

### Changed
- `docs/task_board.md`: Added Tasks 349-354 to Done and set Tasks 355-360 as the next recommended task.

### Verification
- `git status --short` was clean before this decision change.
- `git rev-parse v0.3.0-dev` returned `ed34d2b5373c3fb8417839b9f06b67e2f706cebe`.
- `git rev-list -n 1 v0.3.0-dev` returned `bd94e90bd82839f8e47d21bbda5dc80cc04c8003`.
- `git remote -v` showed no configured remote.
- `git diff --check` passed.
- No push was executed.
## 2026-06-10 - Tasks 343-348: Create v0.3.0-dev Release Candidate Tag

### Added
- `docs/release_notes_v0.3.0-dev.md`: Added ASCII release notes for the `v0.3.0-dev` developer-oriented packaged release candidate.
- Local annotated git tag `v0.3.0-dev` created after the release notes commit.

### Changed
- `docs/task_board.md`: Added Tasks 343-348 to Done and set Tasks 349-354 as the next recommended task.

### Verification
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_package.ps1` - build succeeded and packaged exe launch smoke passed with exit code 0.
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q` - 16 passed.
- `git diff --check` passed.
- Tag is local only and was not pushed.
## 2026-06-10 - Tasks 337-342: Release Candidate Tag Checklist

### Added
- `docs/release_candidate_tag_checklist_337_342.md`: Added an ASCII pre-tag checklist for the recommended `v0.3.0-dev` developer release-candidate tag, including verification commands, observed results, release notes draft, known limits, and tag commands for later approval.

### Changed
- `docs/task_board.md`: Added Tasks 337-342 to Done and set Tasks 343-348 as the next recommended task.

### Verification
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_package.ps1` - build succeeded and packaged exe launch smoke passed with exit code 0.
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q` - 16 passed.
- `git diff --check` passed.
## 2026-06-10 - Tasks 331-336: Formal Release Readiness Packet

### Added
- `docs/formal_release_readiness_packet_331_336.md`: Added an ASCII release readiness packet separating developer-alpha readiness, packaged Windows release-candidate readiness, public release limits, verification evidence, hold artifact policy, and final tag checklist guidance.

### Changed
- `.gitignore`: Added precise ignore rules for local hold artifacts excluded from release scope.
- `docs/task_board.md`: Added Tasks 331-336 to Done and set Tasks 337-342 as the next recommended task.

### Verification
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_package.ps1` - build succeeded and packaged exe launch smoke passed with exit code 0.
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q` - 16 passed.
- `git diff --check` passed.
## 2026-06-10 - Tasks 325-330: Packaged App Quickstart

### Added
- `docs/packaged_app_quickstart_325_330.md`: Added an ASCII user-facing Windows onedir package quickstart covering build, launch, sample data location, troubleshooting, current limits, and research-only disclaimer.

### Changed
- `docs/task_board.md`: Added Tasks 325-330 to Done and set Tasks 331-336 as the next recommended task.

### Verification
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_package.ps1` - build succeeded and packaged exe launch smoke passed with exit code 0.
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q` - 16 passed.
- `git diff --check` passed.
## 2026-06-10 - Tasks 319-324: PyInstaller Build Script and Artifact Hygiene

### Added
- `scripts/build_package.ps1`: Added a Windows PyInstaller `--onedir` build script that prefers the local virtualenv Python and runs a packaged exe launch smoke.
- `docs/pyinstaller_artifact_hygiene_319_324.md`: Added an ASCII artifact hygiene report covering generated output ignore rules, script verification, and remaining packaging risks.

### Changed
- `.gitignore`: Added `*.spec` to ignore auto-generated PyInstaller spec files by default.
- `pyproject.toml`: Added `pyinstaller` to the dev optional dependency group only.
- `docs/task_board.md`: Added Tasks 319-324 to Done and set Tasks 325-330 as the next recommended task.

### Verification
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_package.ps1` - build succeeded and packaged exe launch smoke passed with exit code 0.
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q` - 16 passed.
- `git diff --check` passed.
## 2026-06-10 - Tasks 313-318: PyInstaller Onedir Build Spike

### Added
- `docs/pyinstaller_onedir_build_spike_313_318.md`: Added an ASCII build spike recording a successful PyInstaller `--onedir` build, packaged exe launch smoke with exit code 0, bundled sample CSV location, build size, and next artifact-hygiene task.

### Changed
- `docs/task_board.md`: Added Tasks 313-318 to Done and set Tasks 319-324 as the next recommended task.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q` - 16 passed.
- Packaged exe launch smoke with `QSL_EXIT_AFTER_MS=100` and `QT_QPA_PLATFORM=offscreen` exited with code 0.
- `git diff --check` passed.
## 2026-06-10 - Tasks 307-312: Packaging Path Spike

### Added
- `docs/packaging_path_spike_307_312.md`: Added an ASCII packaging decision spike comparing PyInstaller, Nuitka, and pip entrypoint options, recommending a first PyInstaller `--onedir` build spike for Windows desktop release validation.

### Changed
- `docs/task_board.md`: Added Tasks 307-312 to Done and set Tasks 313-318 as the next recommended task.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q` - 16 passed.
- `git diff --check` passed.
## 2026-06-10 - Tasks 301-306: Formal Release Blocker Triage

### Added
- `docs/formal_release_blocker_triage_301_306.md`: Added an ASCII formal-release blocker triage separating must-fix release blockers, post-release gaps, sufficient developer-alpha evidence, and the next packaging spike.

### Changed
- `docs/task_board.md`: Added Tasks 301-306 to Done and set Tasks 307-312 as the next recommended task.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q` - 16 passed.
- `git diff --check` passed.
## 2026-06-10 - Tasks 295-300: CI Smoke Workflow Implementation

### Added
- `.github/workflows/ci.yml`: Added a Windows Python 3.11 GitHub Actions smoke workflow for the current 16-test developer-alpha smoke set on `master` push and pull request events.

### Changed
- `docs/task_board.md`: Added Tasks 295-300 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q` - 16 passed.
- `git diff --check` passed.
## 2026-06-10 - Tasks 289-294: CI Smoke Pipeline Design

### Added
- `docs/ci_smoke_pipeline_design_289_294.md`: Added an ASCII CI smoke pipeline design for a Windows Python 3.11 GitHub Actions workflow targeting the current 16-test developer-alpha smoke set.

### Changed
- `docs/task_board.md`: Added Tasks 289-294 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q` - 16 passed.
- `git diff --check` passed.
## 2026-06-10 - Tasks 283-288: Developer Alpha Acceptance Packet

### Added
- `docs/developer_alpha_acceptance_packet_283_288.md`: Added an ASCII developer-alpha acceptance packet with PASS recommendation for developer alpha, NOT PASS recommendation for formal desktop release, concrete smoke evidence, and next formal-release tasks.

### Changed
- `docs/task_board.md`: Added Tasks 283-288 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q` - 16 passed.
- `git diff --check` passed.
## 2026-06-10 - Tasks 277-282: Hold Artifact Final Decision

### Added
- `docs/hold_artifact_decision_277_282.md`: Added an ASCII hold-artifact decision document that keeps local agent-loop artifacts untracked for developer alpha and excludes them from formal release by default.

### Changed
- `docs/task_board.md`: Added Tasks 277-282 to Done.

### Verification
- `git diff --check` passed.
## 2026-06-10 - Tasks 271-276: Desktop Evaluator Walkthrough

### Added
- `docs/desktop_evaluator_walkthrough_271_276.md`: Added an ASCII developer-evaluator walkthrough from launch through sample data import, strategy workflow, validation, results inspection, and report export.

### Changed
- `docs/task_board.md`: Added Tasks 271-276 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py -q` - 12 passed.
- `git diff --check` passed.
## 2026-06-10 - Tasks 265-270: Sample Data Workflow Smoke

### Added
- `tests/test_sample_data_workflow_smoke.py`: Added sample-data workflow smoke coverage for sample CSV existence, DataService normalization, backtest structured output, and markdown report generation using existing APIs.

### Changed
- `docs/task_board.md`: Added Tasks 265-270 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_sample_data_workflow_smoke.py -q` - 7 passed.
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py -q` - 12 passed.
- `git diff --check` passed.
## 2026-06-10 - Tasks 259-264: Alpha Readiness Gap Audit

### Added
- `docs/alpha_readiness_gap_audit_259_264.md`: Added an ASCII alpha readiness audit covering current runnable evidence, alpha blockers, formal release gaps, and the next three recommended engineering tasks.

### Changed
- `docs/task_board.md`: Added Tasks 259-264 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q` - 9 passed.
- `git diff --check` passed.
## 2026-06-10 - Tasks 253-258: Desktop Entrypoint Subprocess Smoke

### Added
- `tests/test_app_startup_smoke.py`: Added subprocess smoke coverage for `app/main.py` with `QT_QPA_PLATFORM=offscreen`, `QSL_EXIT_AFTER_MS=100`, timeout handling, captured output, and strict Qt platform-plugin skip detection.

### Changed
- `docs/task_board.md`: Added Tasks 253-258 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py -q` - 5 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 247-252: Desktop Startup Import Smoke

### Added
- `tests/test_app_startup_smoke.py`: Added headless startup smoke coverage for `app.main.main`, `MainWindow` import, project-root import path, and offscreen `MainWindow` construct/close without starting the event loop.

### Changed
- `docs/task_board.md`: Added Tasks 247-252 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py -q` - 4 passed.
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_import_preview_contract_acceptance.py tests/test_archive_importer.py tests/test_archive_import_preview_service.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 105 passed.
- `git diff --check` passed.
## 2026-06-10 - Tasks 241-246: Archive Import Preview Contract Negative Acceptance

### Added
- `tests/test_archive_import_preview_contract_acceptance.py`: Added negative and edge acceptance tests for invalid archive error cause preservation, no-config exact preview shape, and unknown restore action manual-review summary behavior.

### Changed
- `docs/task_board.md`: Added Tasks 241-246 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_import_preview_contract_acceptance.py tests/test_archive_importer.py tests/test_archive_import_preview_service.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 105 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 235-240: Archive Import Preview Contract Acceptance Snapshot

### Added
- `tests/test_archive_import_preview_contract_acceptance.py`: Added a full service-level acceptance snapshot for archive import preview schema, top-level keys, config keys, restore plan entry keys, restore plan summary keys, JSON compatibility, collision flags, and read-only behavior.

### Changed
- `docs/task_board.md`: Added Tasks 235-240 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_import_preview_contract_acceptance.py tests/test_archive_importer.py tests/test_archive_import_preview_service.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 102 passed.
- `git diff --check` passed.
## 2026-06-10 - Tasks 229-234: Archive Import Preview Schema Public Contract Hardening

### Added
- `archive/importer.py`: Promoted the archive import preview schema version to public `ARCHIVE_IMPORT_PREVIEW_SCHEMA_VERSION` and used it in preview serialization.
- `archive/__init__.py`: Exported `ARCHIVE_IMPORT_PREVIEW_SCHEMA_VERSION`.
- `tests/test_archive_importer.py`: Added public export consistency and archive-version distinction tests.
- `tests/test_archive_import_preview_service.py`: Added full preview contract coverage for schema version, collision flags, config comparison, restore plan evidence, and JSON compatibility.

### Changed
- `docs/task_board.md`: Added Tasks 229-234 to Done.

### Verification
- `\.venv\Scripts\python.exe -m pytest tests/test_archive_importer.py tests/test_archive_import_preview_service.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 101 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 223-228: Archive Import Preview Stable Schema Contract

### Added
- `archive/importer.py`: Added top-level `archive_import_preview_schema_version` to archive preview dict output.
- `tests/test_archive_importer.py`: Added schema marker tests for omitted config, config comparison, existing key preservation, and JSON compatibility.
- `tests/test_archive_import_preview_service.py`: Added service schema marker tests for omitted config, config comparison, top-level key preservation, JSON compatibility, and no-write behavior.

### Changed
- `docs/task_board.md`: Added Tasks 223-228 to Done.

### Verification
- `\.venv\Scripts\python.exe -m pytest tests/test_archive_importer.py tests/test_archive_import_preview_service.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 98 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 217-222: Archive Config Restore Plan UI-Readiness Flags

### Added
- `archive/importer.py`: Added `severity` and `requires_manual_review` fields to restore plan entries, plus `manual_review_required` summary evidence. Codex also hardened unknown action summary handling so unknown actions require manual review by default.
- `tests/test_archive_importer.py`: Added importer-level tests for flag mappings, unknown behavior, summary count, and serialization.
- `tests/test_archive_import_preview_service.py`: Added service-level tests for omitted config, all-match config, and mixed config flag behavior.

### Changed
- `docs/task_board.md`: Added Tasks 217-222 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_importer.py tests/test_archive_import_preview_service.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 91 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 211-216: Archive Config Restore Plan Service Summary Hardening

### Added
- `archive/importer.py`: Added `ConfigSnapshotRestorePlanSummary`, `summarize_config_restore_plan()`, and serialized `config_snapshot_restore_plan_summary` evidence.
- `archive/__init__.py`: Exported the restore plan summary and helper.
- `tests/test_archive_importer.py`: Added restore plan summary tests for empty, all actions, mixed, unknown, and dict integration cases.
- `tests/test_archive_import_preview_service.py`: Added service summary tests for omitted config, all-match config, and mixed config evidence.

### Changed
- `docs/task_board.md`: Added Tasks 211-216 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_importer.py tests/test_archive_import_preview_service.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 81 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 205-210: Archive Config Snapshot Read-only Restore Plan Preview

### Added
- `archive/importer.py`: Added `ConfigSnapshotRestorePlanEntry`, `build_config_restore_plan()`, and serialized `config_snapshot_restore_plan` evidence for read-only config restore preview actions.
- `archive/__init__.py`: Exported the restore plan entry and helper.
- `tests/test_archive_importer.py`: Added restore plan coverage for match, different, missing current, no archive evidence, mixed comparisons, and dict serialization.

### Changed
- `docs/task_board.md`: Added Tasks 205-210 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_importer.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py tests/test_archive_import_preview_service.py -q` - 73 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 199-204: Archive Import Preview Service Mixed Evidence Hardening

### Added
- `tests/test_archive_import_preview_service.py`: Added service hardening tests for mixed config evidence, no file writes, and error cause preservation.

### Changed
- `docs/task_board.md`: Added Tasks 199-204 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_import_preview_service.py tests/test_archive_importer.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 67 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 193-198: Archive Import Preview Service Collision Support

### Added
- `app/services/archive_import_preview_service.py`: Added optional collision detector pass-through to `ArchiveImportPreviewService.build_preview()`.
- `tests/test_archive_import_preview_service.py`: Added service collision tests for omitted detector, strategy collision, dataset collision, and both-false detector results.

### Changed
- `docs/task_board.md`: Added Tasks 193-198 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_import_preview_service.py tests/test_archive_importer.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 64 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 187-192: Archive Import Preview Service Facade

### Added
- `app/services/archive_import_preview_service.py`: Added a read-only application service facade that returns full `archive_preview_to_dict()` data.
- `tests/test_archive_import_preview_service.py`: Added service tests for omitted config, config comparison, invalid archive errors, no-archive evidence, JSON compatibility, and no PySide import.

### Changed
- `docs/task_board.md`: Added Tasks 187-192 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_import_preview_service.py tests/test_archive_importer.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 60 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 181-186: Archive Import Preview Full Dict Serialization

### Added
- `archive/importer.py`: Added `archive_preview_to_dict()` for JSON-compatible serialization of full `ArchiveImportPreview` metadata plus config evidence.
- `archive/__init__.py`: Exported `archive_preview_to_dict` through the archive package API.
- `tests/test_archive_importer.py`: Added full preview serialization coverage for omitted config, all-match config, collision flags, JSON compatibility, and copy isolation.

### Changed
- `docs/task_board.md`: Added Tasks 181-186 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_importer.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 55 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 175-180: Archive Import Preview Dict Serialization for Config Evidence

### Added
- `archive/importer.py`: Added `config_evidence_to_dict()` to serialize config snapshot files, evidence, comparisons, and summary from `ArchiveImportPreview`.
- `archive/__init__.py`: Exported `config_evidence_to_dict` through the archive package API.
- `tests/test_archive_importer.py`: Added serialization coverage for omitted config dir, all-match, mixed summary, no-archive-evidence, JSON compatibility, and copy isolation.

### Changed
- `docs/task_board.md`: Added Tasks 175-180 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_importer.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 51 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 169-174: Archive Config Comparison Summary Evidence

### Added
- `archive/importer.py`: Added immutable config snapshot comparison summary evidence and summary helper.
- `archive/__init__.py`: Exported `ConfigSnapshotComparisonSummary` and `summarize_config_comparisons` through the archive package API.
- `tests/test_archive_importer.py`: Added summary coverage for empty, all-match, mixed, omitted config dir, populated all-match, and mixed preview scenarios.

### Changed
- `docs/task_board.md`: Added Tasks 169-174 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_importer.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 46 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 163-168: Archive Import Preview Optional Config Comparison

### Added
- `archive/importer.py`: Added optional `project_config_dir` support to `ArchiveImporter.build_preview()` and immutable config snapshot comparison evidence on `ArchiveImportPreview`.
- `tests/test_archive_importer.py`: Added preview comparison coverage for omitted config directory, match, different, and missing current config cases.

### Changed
- `docs/task_board.md`: Added Tasks 163-168 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_importer.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 40 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 157-162: Archive Config Snapshot Read-only Compare Helper

### Added
- `archive/importer.py`: Added read-only config snapshot comparison evidence and helper for match/different/missing_current/no_archive_evidence statuses.
- `archive/__init__.py`: Exported `ConfigSnapshotComparison` and `compare_config_snapshots` through the archive package API.
- `tests/test_archive_importer.py`: Added comparison coverage for match, different, missing current config, no archive evidence, immutability, and no-write behavior.

### Changed
- `docs/task_board.md`: Added Tasks 157-162 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_importer.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 36 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 151-156: Archive Config Snapshot Immutable Hash Evidence

### Added
- `archive/importer.py`: Added immutable config snapshot filename/hash evidence to `ArchiveImportPlan`.
- `archive/__init__.py`: Exported `ConfigSnapshotEvidence` through the archive package API.
- `tests/test_archive_importer.py`: Added evidence coverage for full, absent, and manifest-matched config snapshot hashes.

### Changed
- `docs/task_board.md`: Added Tasks 151-156 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_importer.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py tests/test_archive_exporter.py tests/test_archive_export_service.py -q` - 49 passed.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-10 - Tasks 145-150: Archive Config Snapshot Import Preview Evidence

### Added
- `archive/importer.py`: Added read-only `config_snapshot_files` evidence to `ArchiveImportPlan`.
- `tests/test_archive_importer.py`: Added preview/plan coverage for full, partial, and absent config snapshot files.

### Changed
- `docs/task_board.md`: Added Tasks 145-150 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_importer.py tests/test_archive_roundtrip_acceptance.py tests/test_archive_verifier.py -q` - 29 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 139-144: Archive Config Snapshot Import Readiness Smoke

### Added
- `tests/test_archive_roundtrip_acceptance.py`: Added export-verify-import roundtrip smoke coverage for archives containing project config snapshots.

### Changed
- `docs/task_board.md`: Added Tasks 139-144 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_roundtrip_acceptance.py tests/test_archive_exporter.py tests/test_archive_verifier.py -q` - 20 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 133-138: Archive Config Snapshot Verification Smoke

### Added
- `tests/test_archive_exporter.py`: Added verifier smoke coverage for archives that include project config snapshots.
- `tests/test_archive_exporter.py`: Added config snapshot tamper detection coverage through manifest hash verification.

### Changed
- `docs/task_board.md`: Added Tasks 133-138 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_exporter.py tests/test_archive_export_service.py tests/test_archive_verifier.py -q` - 24 passed.
- `git diff --check` passes with CRLF warnings only.
## 2026-06-10 - Tasks 127-132: Archive Project Config Snapshot Readiness

### Added
- `archive/exporter.py` and `ArchiveExportService`: Added optional export-side project config snapshot copying via `config_sources`.
- Tests cover exporter config file inclusion, service forwarding, missing-config omission, and UI archive handler config source wiring.

### Changed
- `docs/task_board.md`: Added Tasks 127-132 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_archive_exporter.py tests/test_archive_export_service.py tests/test_archive_builder.py -q` - 26 passed.
- `.\.venv\Scripts\python.exe -m pytest tests/test_wfe_ui_wiring.py -q` - 71 passed.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-10 - Tasks 121-126: Config Foundation Acceptance and Next Slice Selection

### Changed
- `docs/context_brief.md`: Marked project/instrument config foundation complete and clarified that the next post-v0.2 engineering task must be selected.
- `docs/task_board.md`: Added Tasks 121-126 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_project_repo.py tests/test_project_service.py tests/test_instrument_editor.py -q` - 42 passed.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-10 - Tasks 115-120: Reproducibility Config Foundation Continuation

### Added
- `tests/test_instrument_editor.py`: Added editor save isolation, missing `instruments.json` recovery, invalid item recovery, and partial valid/invalid list tests.

### Changed
- `docs/task_board.md`: Added Tasks 115-120 to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_instrument_editor.py tests/test_project_repo.py tests/test_project_service.py -q` - 42 passed.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-10 - Task 114A-114C: InstrumentService Malformed Config Recovery Isolation

### Added
- `tests/test_instrument_editor.py`: Added malformed and empty `instruments.json` recovery tests proving default profile rewrite and preservation of `sessions.json` and `app_settings.json`.

### Changed
- `docs/task_board.md`: Added Task 114A-114C to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_instrument_editor.py -q` - 13 passed.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-10 - Task 113A-113C: InstrumentService Config Isolation Smoke

### Added
- `tests/test_instrument_editor.py`: Added InstrumentService project-mode test proving profile save writes valid instruments JSON, preserves `sessions.json` and `app_settings.json`, and reloads the saved profile.

### Changed
- `docs/task_board.md`: Added Task 113A-113C to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_instrument_editor.py -q` - 9 passed.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-10 - Task 112A-112C: ProjectService Config Boundary Smoke

### Added
- `tests/test_project_service.py`: Added ProjectService-level config file creation, JSON validity, open-preserve, and metadata readback smoke tests.

### Changed
- `docs/task_board.md`: Added Task 112A-112C to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_project_service.py -q` - 7 passed.
- `.\.venv\Scripts\python.exe -m pytest tests/test_project_repo.py -q` - 17 passed.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-10 - Task 111A-111C: Project Config Open-Preserve Tests

### Added
- `tests/test_project_repo.py`: Added `open_project()` preservation tests for custom `instruments.json`, `sessions.json`, `app_settings.json`, and ProjectMeta readback after config mutation.

### Changed
- `docs/task_board.md`: Added Task 111A-111C to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_project_repo.py -q` - 17 passed.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-10 - Task 110A-110C: Project Config Template Integrity Tests

### Added
- `tests/test_project_repo.py`: Added config template integrity tests for `instruments.json`, `sessions.json`, `app_settings.json`, and overwrite recreation.

### Changed
- `docs/task_board.md`: Added Task 110A-110C to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_project_repo.py -q` - 13 passed.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-10 - Task 107A-107C: Data Quality Tooltip Reset Hardening

### Fixed
- Data page status tooltip now clears stale quality evidence after import exceptions, new project, and open project flows while preserving state on canceled import.

### Added
- `tests/test_data_page_wiring.py`: Added focused stale tooltip reset coverage for failed import, cancel, new project, and open project paths.

### Changed
- `docs/task_board.md`: Added Task 107A-107C to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_data_page_wiring.py -q` - 42 passed.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-10 - Task 106A-106C: Data Quality Failure Evidence Hardening

### Added
- `tests/test_data_page_wiring.py`: Added failed-quality import mock and UI test proving `DataQualityReport(passed=False)` surfaces failure, first error, and warnings in the Data page status tooltip.

### Changed
- `docs/task_board.md`: Added Task 106A-106C to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_data_page_wiring.py -q` - 38 passed.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-10 - Task 105A-105C: Data Quality Evidence Surface

### Added
- `DataService.format_quality_evidence()` formats `DataQualityReport` status, warning count, error count, and first issues for UI display.
- Data page status label tooltip now shows quality evidence after successful import.
- `tests/test_data_page_wiring.py`: Added focused formatting and tooltip coverage for clean, warning, and failed quality reports.

### Changed
- `docs/task_board.md`: Added Task 105A-105C to Done.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests/test_data_page_wiring.py -q` - 37 passed.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-09 - Agent Loop Same-Round Fix Attempts

### Added
- `tools/agent_loop.py`: Added `--pass-score` and `--max-fix-attempts`. Rounds now contain same-round `attempt_XXX` retries, and scores below the pass threshold are forced to `NEED_FIX` even if Codex returns `PASS`.
- `tools/agent_loop.py`: Added same-round fix prompt generation from Codex review metadata so Reasonix can revise without consuming the next task round.
- `AGENT_LOOP_README.md`: Documented `round_XXX/attempt_XXX` artifacts and the default `8.8/10` pass gate.

### Verification
- `python -m py_compile tools\agent_loop.py`
- `python tools\agent_loop.py --help`


## 2026-06-09 - Agent Loop Evidence-Only Policy

### Added
- `tools/agent_loop.py`: Added `--reasonix-policy evidence-only`, repeatable `--evidence-command`, `00_evidence.md`, sandboxed Reasonix working directories, and `11_policy_check.json` for detecting tool/read/search violations.
- `AGENT_LOOP_README.md`: Documented evidence-only mode for command-whitelisted review-prep tasks such as `065J`.

### Verification
- `python -m py_compile tools\agent_loop.py`
- `python tools\agent_loop.py --help`


## 2026-06-09 - Agent Loop Task Identity Feedback

### Added
- `tools/agent_loop.py`: Added `task_id`, `task_title`, and `round_label` fields to Codex review JSON, per-round feedback, iteration summary, state updates, and console progress output.
- `AGENT_LOOP_README.md`: Documented task ID, title, and round label in `10_round_feedback.md`.

### Verification
- `python -m py_compile tools\agent_loop.py`
- `python tools\agent_loop.py --help`


## 2026-06-09 - Agent Loop Round Feedback Packets

### Added
- `tools/agent_loop.py`: Added per-round score, score reason, Reasonix result summary, Codex corrective-fix fields, `10_round_feedback.md`, `.ai_loop/iteration_summary.md`, and console progress output.
- `AGENT_LOOP_README.md`: Documented the new round feedback artifacts and expected review metadata.

### Verification
- `python -m py_compile tools\agent_loop.py`
- `python tools\agent_loop.py --help`


## 2026-06-09 - Codex Reasonix CLI Loop MVP

### Added
- `tools/agent_loop.py`: Minimal CLI-first Codex <-> Reasonix iteration orchestrator with round artifacts, CLI probing, Reasonix auto/manual modes, git diff capture, optional tests, Codex review, and `09_next_action.json` status handling.
- `AGENT_LOOP_README.md`: Usage, 5-round examples, test command examples, CLI probe findings, and Reasonix manual fallback instructions.
- `.ai_loop/state.json`, `.ai_loop/goal.md`, and `.ai_loop/rounds/.gitkeep`: Initial local loop state and artifact structure.

### Verification
- `python -m py_compile tools\agent_loop.py`
- `python tools\agent_loop.py --help`


## 2026-06-09 - Agent Loop Automation Script

### Added
- scripts/agent_loop.ps1: Adds a configurable DeepSeek/Reasonix implementation plus Codex review loop with counted rounds, score threshold gating, same-round fix attempts, prompt/output archives, and dry-run simulation.

### Changed
- docs/task_board.md: Added the agent loop automation script to Done.

### Verification
- powershell -NoProfile -ExecutionPolicy Bypass -File scripts\agent_loop.ps1 -Rounds 1 -DryRun
- powershell -NoProfile -ExecutionPolicy Bypass -File scripts\agent_loop.ps1 -Rounds 1 -MaxFixAttempts 1 -DryRun -DryRunScores "8.0,9.0" confirms below-threshold review returns to DeepSeek within the same counted round, then passes on score 9.0.
## 2026-06-09 - Task 065B-Impl: Import Error UX Smoke Test Only

### Added
- `tests/test_data_page_wiring.py`: `test_import_file_failure_produces_actionable_message` �� end-to-end test proving that when `import_file()` raises on a nonexistent file, the converted error is actionable.

### Changed
- `docs/task_board.md`: Added 065B-Impl to Done.

### Verification
- `pytest tests/test_data_page_wiring.py -q`: 14 passed (8 existing + 6 from 065A + 1 new).
- `git diff --check` passes with CRLF warnings only.

## 2026-06-09 - Task 065A-Impl: Data Import UX Hardening - Format Guidance and Actionable Errors

### Added
- `DataService.get_expected_format_guide()` - returns human-readable description of expected OHLCV CSV format.
- `DataService.get_actionable_import_error(e)` - converts raw exceptions into actionable user-facing messages.
- Format guidance label on the Data page near the Import button showing expected columns.
- 6 new tests for format guide content, actionable error mapping, and UI label existence.

### Changed
- `_handle_import_ohlcv_data()` in `main_window.py`: raw exceptions now routed through `get_actionable_import_error()` for user-facing messages.
- `docs/task_board.md`: Added 065A-Impl to Done. Set Next to None.
- `docs/context_brief.md`: Refreshed current review focus to 065A-Impl.

### Fixed
- Import error messages now tell the user what went wrong and how to fix it.

### Verification
- All existing data workflow tests pass (17/17).
- Focused data/UI wiring tests pass: 53 passed, including format guide, actionable error mapping, and Data page label coverage.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-09 - Task 064J: Next Engineering Task Candidate Brief

### Added
- `docs/next_engineering_task_candidate_brief_064J.md` - compares 3 next-direction candidates (Data Workflow Polish, Strategy Quality Expansion, System Hardening). Recommends **Data Workflow Polish / Import UX Hardening** as the smallest next task that creates real engineering progress.

### Changed
- `docs/task_board.md`: Moved 064J to Done. Next item points to the candidate brief for Codex/user decision.
- `docs/context_brief.md`: Refreshed current review focus to the 064J candidate brief.
- Codex tightened the 064J candidate brief so the recommended first data workflow batch remains UI/service-only and system-hardening wording does not imply staging or committing inside the planning task.

### Verification
- `git diff --check` passes with CRLF warnings only.

## 2026-06-09 - Codex Correction for Task 064H Documentation Artifact Staging Plan

### Added
- `docs/documentation_artifact_staging_plan_064H.md` groups accepted untracked documentation artifacts into agent reports, standalone docs, and historical archives.

### Changed
- `docs/task_board.md`: Moved the next item to a Codex/user decision on staging accepted documentation artifacts or continuing feature planning.
- `docs/context_brief.md`: Refreshed the current review focus and pointed to the 064H staging plan.

### Verification
- `git status --short` confirms `.codegraph/` is excluded and documentation artifacts remain visible.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-09 - Codex Correction for Task 064G Archive Historical Records Policy

### Added
- `docs/archive_historical_records_policy_064G.md` documents that `docs/archive/` historical records are repository documentation artifacts.

### Changed
- `docs/untracked_file_hygiene_064D.md`: Marked the `docs/archive/` decision resolved and distinguished historical docs from local tool-state.
- `docs/task_board.md`: Moved the next review focus to a documentation artifact staging plan.
- `docs/context_brief.md`: Refreshed the current review focus and archive policy note.

### Verification
- `git status --short` confirms `docs/archive/` remains visible as documentation artifacts.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-09 - Codex Correction for Task 064F CodeGraph Hygiene Policy

### Added
- `docs/codegraph_hygiene_policy_064F.md` documents the repository decision for `.codegraph/` local tool-state.

### Changed
- `.gitignore`: Added `.codegraph/` so local CodeGraph database, WAL/SHM, log, and PID files stay out of repository diffs.
- `docs/untracked_file_hygiene_064D.md`: Marked the `.codegraph/` decision resolved and distinguished it from documentation artifacts.
- `docs/task_board.md`: Moved the next review focus to `docs/archive/` historical record policy.

### Verification
- `git status --short` confirms `.codegraph/` no longer appears as an untracked directory.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-09 - Batch 064E-Acceptance: Post-063D/063E/063F Acceptance Smoke

### Added
- `docs/post_063d_063e_063f_acceptance_smoke_064E.md` - acceptance smoke for MC worst-case equity, WFE display, and IS Baseline Precheck UI feature chain.

### Changed
- `docs/task_board.md`: Moved 064E-Acceptance to In Progress (then Done). Next item is a Codex decision on `.codegraph/` / repository hygiene policy.

### Verification
- MC + pipeline tests: 98 passed in 3.50s.
- Widget + report + UI wiring tests: 129 passed in 12.85s.
- Data workflow focused tests: 17 passed in 5.27s - stale DataService failure claim retired.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-09 - Codex Review Correction for Batch 064C/064D

### Fixed
- Added the missing `.codegraph/` local tool-state directory to `docs/untracked_file_hygiene_064D.md`.
- Corrected the inventory wording so not all untracked files are described as plain documentation.
- Marked `.codegraph/` as needing a Codex decision before any ignore/delete policy change.

### Verification
- `git diff --check` passes with CRLF warnings only.

## 2026-06-09 - Codex Review Correction for Task 064B

### Fixed
- Removed the stale "13 pre-existing DataService failures" risk from the 064B decision note and replaced it with a current stale-claim hygiene risk.
- Refreshed `docs/context_brief.md` so price-noise, MC worst-case equity, WF equity charts, WFE, and precheck controls are no longer listed as deferred.
- Updated the context brief next item to 064C/064D cleanup and recorded that focused data workflow tests currently pass.

### Verification
- Data workflow focused tests: 17 passed after correction.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-09 - Batch 064C-Fix + 064D-Fix: Task Board Dedup + Untracked File Hygiene

### Added
- `docs/untracked_file_hygiene_064D.md` - inventory of 19 untracked doc files across docs/agent_reports/, docs/ (design/decision smokes), and docs/archive/. Classified as keep-as-task-artifact or needs-Codex-decision.

### Changed
- `docs/task_board.md`: Removed "Proposed Batch 064C-Fix + 064D-Fix" from Next (now Done). Set next item to "Batch 064E-Acceptance - Post-063D/063E/063F Acceptance Smoke".
- `docs/context_brief.md`: Updated next-item reference to 064E-Acceptance.

### Fixed
- No duplicate or stale entries found in the task board Done section (all impl/review pairs follow project convention).

### Verification
- `git diff --check` passes with CRLF warnings only.

## 2026-06-09 - Task 064B: Post-063F Milestone State Review and Next Direction Brief

### Added (Decision)
- `docs/next_milestone_decision_064B.md` - reviews 063D/063E/063F state, evidence surface coverage table, remaining risks. Recommends Option D (System Hardening / Cleanup) to fix stale context brief, deduplicate task board, clean untracked files.

### Verification
- No production code changed.
- `git diff --check` passes.

## 2026-06-09 - Codex Review Correction for Task 063F-Impl

### Fixed
- Normalized MC worst-case equity report labels from raw `trade_step` to user-facing `trade-step` in Markdown and HTML.
- Reused one report helper for MC curve-type wording so unknown curve types are explicitly not verified as bar-by-bar equity.
- Corrected WFE report visibility so the line appears when either `average_wfe` or `median_wfe` is present.
- Tightened report tests to reject raw `trade_step` output and cover median-only WFE payloads.

### Verification
- Report tests: 58 passed after correction.
- Widget + pipeline + MC regression tests: 140 passed after correction.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-09 - Task 063F-Impl: MC Worst-Case Equity Report Tables + WF Efficiency Report Display

### Added
- `reports/generator.py`: Added MC worst-case equity evidence to markdown and HTML reports when `worst_case_equity_curve` has ? 2 points. Labeled with `curve_type` (default `trade_step`). Includes start/end equity and percentage change. Explicitly states trade-step curve is from surviving trades only, not bar-by-bar equity.
- `tests/test_report_export.py`: 7 tests - markdown includes/omits, HTML includes/omits, WFE present, WFE None��N/A, WFE absent when keys missing.

### Verification
- Report tests: 57 passed.
- Widget + pipeline + MC tests: 140 passed.
- `git diff --check` passes.

## 2026-06-09 - Changelog and Task Board Archive

### Changed
- Moved older `docs/task_board.md` Done items into `docs/archive/task_board_done_archive.md` so the active board stays compact.
- Moved older `docs/changelog.md` entries into `docs/archive/changelog_archive.md` so recent context remains quick to load.
- Kept recent 062B+ context in the main files for the current Price-Noise / WF Equity / MC evidence workline.

### Verification
- Documentation-only archival change; checked that archive files exist and main files retain current milestone, recent Done, Next, and recent changelog entries.
## 2026-06-09 - Context Efficiency Protocol Hardening

### Changed
- Updated `SOUL.md` and `AGENTS.md` so low-risk tasks may use context levels, `docs/context_brief.md`, targeted task-board sections, and recent changelog entries instead of repeatedly loading every long project document in full.
- Updated the handoff template to require an explicit context level and file/section list.
- Refreshed `docs/context_brief.md` with current context-efficiency rules and the latest next task.

### Verification
- Documentation-only change; reviewed the policy diff for preservation of Level 3 full-context requirements.

## 2026-06-08 - Codex Review Correction for Task 063E-Impl

### Fixed
- Clarified MC worst-case equity widget wording so `trade_step` is shown as `trade-step` and explicitly labeled as surviving-trade evidence, not bar-by-bar equity.
- Corrected Walk-Forward Efficiency display to render WFE when WFE keys are present, including `None` average/median values as `N/A`.
- Added WFE defined/undefined counts to the Walk-Forward card and regression tests for key-present versus key-missing behavior.

### Verification
- Widget tests: 42 passed after correction.
- UI wiring tests: 29 passed after correction.
- Pipeline + MC tests: 98 passed after correction.
- `git diff --check` passes with CRLF warnings only.

## 2026-06-08  — Task 063E-Impl: MC Worst-Case Equity Widget + WF Efficiency Display + Precheck UI Controls

### Added
- `app/widgets/validation_summary.py`: Added `_MCEquityChart` widget (QGraphicsView line chart, orange, 150px height). Wired MC worst-case equity chart when `worst_case_equity_curve` has >= 2 points. Added WF Efficiency line to Walk-Forward card when WFE keys present (None rendered as N/A).
- `app/ui/main_window.py`: Added IS Baseline Quality Precheck controls (parent checkbox + dependent non-positive checkbox). Wired into PipelineConfig via `run_is_baseline_quality_precheck` and `fail_is_baseline_on_nonpositive_pnl`.
- `tests/test_validation_summary.py`: 7 new tests  — MC chart shown/absent/absent-short, WFE shown/NONE-avg/both-None-absent.
- `tests/test_wfe_ui_wiring.py`: 5 new tests  — controls exist, nonpositive enabled/disabled, unchecked passes False, parent+nonpositive checked, parent checked nonpositive unchecked.

### Verification
- Widget tests: 41 passed.
- Pipeline + MC tests: 98 passed.
- `git diff --check` passes.

## 2026-06-08 - Codex Review Correction for Task 063D-Impl

### Fixed
- Changed MC worst-case equity collection to track only the current worst iteration curve during the loop instead of retaining all iteration curves.
- Added `worst_case_equity_curve_type="trade_step"` and serialized MC warnings so downstream UI/report surfaces cannot mistake the curve for bar-by-bar equity.
- Added deterministic tie-break and serialization regression tests for the new MC evidence field.
- Cleaned the task board next assignment to a single 063E implementation batch.

### Verification
- MC + pipeline tests: 98 passed after correction.
- Widget + report tests: 85 passed after correction.
- `git diff --check` passes after correction.

## 2026-06-08  — Task 063D-Impl: MC Worst-Case Equity Engine and Serialization Slice

### Added
- `validation_engine/monte_carlo.py`: Added `worst_case_equity_curve` field to `MonteCarloResult`. Added `collect_worst_case_equity` parameter to `run_missed_trade_monte_carlo`. Worst iteration selected by lowest total_pnl  — highest abs max_drawdown_pnl  — lowest index.
- `app/services/validation_pipeline_service.py`: `_mc_to_dict` includes `worst_case_equity_curve` only when present.
- `tests/test_monte_carlo.py`: 5 tests  — default None, collected when enabled, not collected when disabled, deterministic, zero-trades empty.

### Verification
- MC tests: 54 passed (49 + 5).
- Pipeline tests: 40 passed.
- Widget + report tests: 85 passed.
- `git diff --check` passes.

## 2026-06-08 - Codex Review Correction for Batch 063B-Design + 063C-Design

### Fixed
- Corrected the 063B contract to use one field name, `worst_case_equity_curve`, everywhere.
- Added deterministic worst-iteration tie-break rules and required opt-in collection so MC does not store all per-iteration curves by default.
- Flagged missed-trade MC equity reconstruction as an engine ambiguity: implementation must either produce a clearly labeled trade-step curve or return `None` with a warning.
- Corrected the 063C precheck UI contract from stale spinbox/custom-value wording to checkbox-only behavior, including dependent enable/disable mapping.
- Split the next work into 063D engine/serialization and 063E widget/UI so UI work does not mask engine ambiguity.

### Verification
- No production code changed.
- Focused review tests: 198 passed after correction.
- `git diff --check` passes after correction.

## 2026-06-08  — Batch 063B-Design + 063C-Design: MC Worst-Case Equity Evidence Surface and WF Efficiency + Precheck Toggle Design

### Added (063B-Design)
- `docs/mc_worst_case_equity_surface_design_063B.md`  — defines worst-case equity curve storage in `MonteCarloResult`, widget line chart, report table, 7 focused tests. Engine change scope outlined.

### Added (063C-Design)
- `docs/wf_efficiency_ui_and_precheck_toggle_design_063C.md`  — defines WF Efficiency display in widget, IS-baseline precheck UI controls (2 checkboxes), 8 focused tests across widget + UI wiring.

### Verification
- No production code changed.
- `git diff --check` passes.
## 2026-06-08  — Task 063A: User-Directed Milestone Decision

### Added (Decision)
- `docs/next_milestone_decision_063A.md`  — 4 next-direction options: A (strategy quality), B (data workflow), C (GA/GP visibility), D (system hardening).

### Codex Review
- Rejected the first-pass Option B recommendation because it relied on the stale claim that 13 `DataService.import_file()` failures still exist.
- Corrected the recommendation to Option A  — Strategy Quality / Robustness Expansion.
- Clarified that data workflow polish remains valid as a UX polish path, not as a current import blocker fix.

### Verification
- No production code changed.
- Focused data workflow tests: 14 passed.
- Prior full-suite evidence from Task 062O: 1291 passed.
- `git diff --check` passes after correction.

## 2026-06-08  — Task 062O: Price-Noise Acceptance Smoke and Milestone Triage

### Added
- `docs/price_noise_acceptance_smoke_062O.md`  — verifies price-noise feature chain across engine, pipeline, UI controls, widget, and report. Default-off and research-only diagnostic handling confirmed.

### Verification
- Stress tests: 34 passed.
- Pipeline tests: 40 passed.
- UI wiring tests: 24 passed.
- Widget tests: 35 passed.
- Report tests: 50 passed.
- Full suite: 1291 passed.
- `git diff --check` passes.

### Codex Review
- Corrected the acceptance smoke note to reflect the current OHLC-preserving price-noise engine contract instead of stale "OHLC constraints may be violated" wording.
- Updated stale test counts and added full-suite verification evidence.
- Clarified that price-noise is accepted only as a research-only diagnostic, not proof of live robustness.

## 2026-06-08  — Batch 062N-Impl: Price-Noise Widget Display Implementation

### Added
- `app/widgets/validation_summary.py`: Added price_noise detail sub-lines in the stress results section  — shows Noise %, Iterations, Method, Research only flag, and warnings.
- `tests/test_validation_summary.py`: 3 widget tests  — price_noise detail shown when opt-in, omitted by default, warnings displayed.

### Verification
- Widget tests: 35 passed.
- `git diff --check` passes.

### Codex Review
- Stopped the widget from fabricating `research_only=True` when the price-noise payload omits that field.
- Replaced stale OHLC-constraint warning fixture text with the current research-only diagnostic warning.
- Added a regression test proving missing `research_only` renders as unknown instead of a false confirmed flag.

## 2026-06-08  — Batch 062L-Impl + 062M-Design: Report Price-Noise Display and Price-Noise Widget Display Design

### Added (062L-Impl)
- `reports/generator.py`: Added price_noise detail sub-lines in both markdown and HTML formatters  — shows noise_pct, iterations, method, research_only, and warnings.
- `tests/test_report_export.py`: 5 report tests  — markdown includes/omits, HTML includes/omits, HTML escaping.

### Added (062M-Design)
- `docs/price_noise_widget_display_design_062M.md`  — defines widget display for price-noise stress results, visibility rules, 4 focused future tests.

### Verification
- Report tests: 50 passed.
- `git diff --check` passes.

### Codex Review
- Replaced stale price-noise warning fixture text that contradicted the OHLC-preserving engine contract.
- Added `method` and `research_only` rendering so reports keep the price-noise diagnostic framed as research-only evidence.
- Added HTML escaping for price-noise assumption detail values and a regression test for malicious assumptions/warnings.
- Cleaned 062K/062M design docs to use explicit Yes/No visibility rules and current research-only wording.

## 2026-06-08  — Batch 062J-Impl + 062K-Design: Price-Noise UI Controls Implementation and Report Price-Noise Display Design

### Added (062J-Impl)
- `app/ui/main_window.py`: Added Validate page price-noise controls (checkbox + 3 spinboxes), default-off. `_handle_run()` wires values into `PipelineConfig`.
- `tests/test_wfe_ui_wiring.py`: 4 UI tests  — controls exist with defaults, spins toggle with checkbox, unchecked passes False, checked passes custom values.

### Added (062K-Design)
- `docs/price_noise_report_display_design_062K.md`  — defines markdown/HTML display for price-noise stress results, visibility rules, 4 focused tests.

### Verification
- Pipeline tests: 40 passed.
- UI wiring tests: 24 passed.
- Validation summary tests: 31 passed.
- `git diff --check` passes.

### Codex Review
- Changed the price-noise UI label from ambiguous percent wording to `Noise fraction:` because `PipelineConfig.price_noise_pct` expects a fraction (`0.005 = 0.5%`).
- Added a UI wording regression test so the control cannot silently drift back to percent-looking units.

## 2026-06-08  — Batch 062H-Impl + 062I-Design: WF Equity Chart Widget Implementation and Price-Noise UI Config Controls Design

### Added (062H-Impl)
- `app/widgets/validation_summary.py`: Added `_WFEquityChart`  — PySide6-only line chart using `QGraphicsView`/`QGraphicsScene`. Green for PASSED, red for FAILED. Height constrained to 200px. Renders only windows with equity_curve length >= 2.
- Wired chart after WF Equity Summary text section when equity data present.
- `tests/test_validation_summary.py`: 6 tests  — chart shown, absent when no windows key, absent when all equity None, handles partial equity, single point < 2 no chart.

### Added (062I-Design)
- `docs/price_noise_ui_controls_design_062I.md`  — defines Validate page controls (checkbox + 3 spinboxes), PipelineConfig mapping, 5 focused future tests.

### Verification
- Widget tests: 31 passed (22 existing + 9 new/strengthened).
- Pipeline tests: 40 passed.
- `git diff --check` passes.

### Codex Review
- Added tighter WF equity chart assertions for drawn pass/fail line count, line colors, fixed chart height, and basic axis labels.
- Added minimal axis and equity/bar labels to the WF equity chart so the evidence surface is readable without adding charting dependencies.

## 2026-06-08  — Batch 062F-Impl + 062G-Design: Price-Noise Pipeline Integration and WF Equity Widget Test Contract

### Added (062F-Impl)
- `app/services/validation_pipeline_service.py`: Imported `stress_price_noise`, added 4 `PipelineConfig` fields (`run_price_noise_stress`, `price_noise_pct`, `price_noise_iterations`, `price_noise_seed`), wired price-noise stress after remove-best-N stress. Default off.
- `tests/test_validation_pipeline_service.py`: 5 tests  — default not included, opt-in included, config snapshot fields, same-seed deterministic, explicit off.

### Added (062G-Design)
- `docs/wf_equity_widget_test_contract_062G.md`  — implementation-ready test contract for WF per-window equity chart: target file, input shape, visibility rules, color/label expectations, 7 focused tests, out-of-scope items.

### Codex Review
- Added missing pipeline assertions for price-noise `pnl_degradation_ratio`, `survival_rate`, and `research_only=True`.
- Added explicit-off coverage and full price-noise dict determinism comparison.
- Rewrote the WF equity widget visibility table to use explicit `Yes` / `No` values.

### Verification
- Pipeline tests: 40 passed (35 existing + 5 new).
- Stress tests: 34 passed.
- Full suite: 1269 passed.
- `git diff --check` passes.

## 2026-06-08 - Codex Review Correction for Batch 062D-Impl + 062E-Design

### Fixed
- Corrected first-pass `stress_price_noise()` behavior to preserve OHLC invariants through body/wick reconstruction instead of allowing independently perturbed invalid bars.
- Corrected `noise_pct=0` to be a valid identity run.
- Corrected `pnl_degradation_ratio` semantics to `median_total_pnl / baseline_pnl`, defined only when baseline PnL is positive.
- Added non-positive baseline PnL handling, survival-rate output, and the required research-only diagnostic warning.

### Verification
- `.\.venv\Scripts\python.exe -m pytest tests\test_stress_test.py -q` - 34 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_validation_pipeline_service.py -q` - 35 passed.
- `.\.venv\Scripts\python.exe -m pytest tests -q` - 1264 passed.
- `git diff --check` - passed.
- `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1` - passed.

## 2026-06-08  — Batch 062D-Impl + 062E-Design: Price-Noise Stress Test Engine Slice and WF Equity Widget Implementation Contract

### Added (062D-Impl)
- `validation_engine/stress_test.py`: Added `stress_price_noise()`  — Gaussian OHLC noise stress test with deterministic seeds, iterations, pnl_degradation_ratio pass/fail. Preserves existing stress test pattern. Default pipeline behaviour unchanged.
- `tests/test_stress_test.py`: 6 tests  — structure, deterministic, zero-noise raises, non-zero perturbation visible, baseline PnL warning, invalid noise_pct rejected.

### Added (062E-Design)
- `docs/wf_equity_widget_implementation_contract_062E.md`  — implementation checklist for WF per-window equity line chart: target file, rendering strategy (PySide6 QGraphicsView), empty/failure states, 6 future tests, out-of-scope items.

### Verification
- Stress tests: 32 passed.
- Pipeline tests: 35 passed (unchanged).
- Full suite: 1242 passed (excluding slow UI tests).

## 2026-06-08  — Batch 062B-Design + 062C-Design: Price-Noise Stress Test Contract and WF Equity Evidence Surface

### Added (062B-Design)
- `docs/price_noise_stress_contract_062B.md`  — defines price-noise stress test: deterministic OHLC-preserving perturbation, pass/fail metrics (`pnl_degradation_ratio`, `win_rate_change`, `survival_rate`), pipeline config fields, assumptions and warnings, 8 focused future tests.

### Added (062C-Design)
- `docs/wf_equity_evidence_surface_design_062C.md`  — defines WF equity chart/table rendering in UI and reports: required data shape, line chart per window, empty/failure states, markdown/HTML expectations, 7 focused future tests.

### Codex Review
- Replaced the unsafe independent OHLC noise model with an OHLC-preserving reconstruction contract.
- Added non-positive baseline PnL handling for `pnl_degradation_ratio`.
- Clarified that PDF embedding is optional future polish, not required implementation scope.

### Verification
- No production code changed.
- `git diff --check` passes.
