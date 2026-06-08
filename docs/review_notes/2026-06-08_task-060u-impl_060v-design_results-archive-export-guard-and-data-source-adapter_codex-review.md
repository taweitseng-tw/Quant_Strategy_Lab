# Codex Review - Batch 060U-Impl + 060V-Design

Decision: PASS after Codex corrective patch

Score:
- DeepSeek original submission: 8.4 / 10, not passable under the 8.8 gate.
- Final corrected state: 9.0 / 10, pass.

Findings:
- [P1] `app/ui/main_window.py`: `_handle_export_archive()` treated `latest_validation_result` as a dict and called `.get(...)`, but the app stores `PipelineResult` dataclass instances after validation runs. This would crash once the handler passed earlier guards. Codex added a helper that supports both dataclass and dict validation payloads.
- [P2] `app/ui/main_window.py`: the project-root guard only checked `_project_root`, which is not part of the existing project-open/create flow. Codex added fallback resolution through `ProjectService.get_active_project()`.
- [P2] `tests/test_wfe_ui_wiring.py`: the new guard test only asserted "does not crash" and did not patch `QMessageBox.warning`, verify WARN logging, or actually reach the no-selection guard due to missing project root. Codex tightened the test and added a `PipelineResult` helper regression.

Required fixes:
- Completed by Codex in this review round.

Architecture risk:
- Low after the fix. The UI still only exposes a guarded action surface and does not run archive export logic directly. The next task should implement the project archive data-source adapter before enabling full UI export.

Verification:
- `.\.venv\Scripts\python.exe -m pytest tests\test_wfe_ui_wiring.py tests\test_archive_export_service.py -q` -> 20 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 1236 passed.
- `git diff --check` -> passed, with existing line-ending normalization warnings for touched files.
- `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1` -> status script ran successfully.

Next assignment:
- Batch 060W-Impl + 060X-Design: implement `ProjectArchiveDataSource` as a service/repository adapter slice, then design full archive export UI delegation. Do not wire full export from `MainWindow` until the adapter has focused tests.
