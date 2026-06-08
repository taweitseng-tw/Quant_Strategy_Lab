Completed:
- Batch 060U-Impl + 060V-Design — Results Archive Export Guard Wiring and Data-Source Adapter Design.

Files changed:
- app/ui/main_window.py (button + handler)
- tests/test_wfe_ui_wiring.py (2 tests)
- docs/archive_ui_data_source_adapter_design_060V.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. Results page now has an "Export Archive" button (disabled until strategy selected).
2. _handle_export_archive() has 4 guards: project root, selected strategy, validation passed, baseline metrics. Guard failures show QMessageBox + log WARN messages. No archive service called yet.
3. 060V design: ProjectArchiveDataSource adapter interface, UID mapping, failure modes, future wiring.

Tests run:
- UI wiring + export service: 19 passed.
- Full suite: 1235 passed.

Assumptions:
- Guard checks match the existing ranked_data / latest_validation_result patterns in MainWindow.
- Full export service call is deferred to 060W.

Known risks:
- No real archive export yet from UI — guard-first only.
- Dataset snapshot path discovery deferred to adapter implementation.

Reviewer focus:
- _handle_export_archive() guard sequence: project_root → ranked_data → strategy → validation passed → baseline metrics.
- Button wiring: created with setEnabled(False), added to header_layout, enabled/disabled with other export buttons.
