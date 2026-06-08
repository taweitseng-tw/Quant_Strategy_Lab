Completed:
- Batch 060Y-Design + 060Z-Signoff — Full UI Export Boundary Design and Reproducibility Milestone Acceptance.

Files changed:
- docs/archive_full_ui_export_boundary_design_060Y.md (created)
- docs/reproducibility_milestone_acceptance_060Z.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. 060Y: raw-row provider resolved with Option A (StrategyRepository.list_all_raw()). Data contracts, user-facing errors, test plan defined.
2. 060Z: 16-component reproducibility chain status table. Verdict: complete at engine/adapter/service/round-trip level. 3 remaining gaps before full UI export.

Tests run:
- Full suite: 1247 passed.

Assumptions:
- StrategyRepository.list_all_raw() will return dicts with strategy_json key, matching ProjectArchiveDataSource expectations.
- DatasetRepository.get_raw_by_id() (or equivalent) can resolve snapshot path from dataset ID.

Known risks:
- No repository changes implemented yet — design only.
- Full UI export still requires repository additions and MainWindow wiring.

Reviewer focus:
- 060Y Option A recommendation: list_all_raw() as minimal, testable change.
- 060Z gap list: 3 required items before full UI export (raw-row provider, dataset path, validation UID lookup).
