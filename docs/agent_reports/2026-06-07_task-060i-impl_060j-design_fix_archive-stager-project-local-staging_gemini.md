Completed:
- Batch 060I/060J Fix — ArchiveStager project-local staging, cleanup policy, aligned transaction ordering.

Files changed:
- docs/archive_stager_implementation_design_060J.md

Behavior changed:
1. Staging dir changed from `tempfile.gettempdir()` to project-local `<project_root>/.staging/<experiment>_<run_id>/`.
2. ArchiveStager init now requires `archive_root`, `project_root`, `experiment_name`, `run_id`.
3. Final destination: `<project_root>/data/imported/<experiment>/ohlcv.csv` — deterministic from init.
4. Cleanup policy explicit: scoped to temp staging only. DB failure cleans temp only (no final destination files exist). Move failure returns partial/repair-needed, does NOT delete DB rows.
5. Transaction ordering aligned: Stage → Verify Hash → DB writes/commit → Final Move → cleanup_temp().
6. `cleanup_temp()` method added. `move_to_final_destination()` takes no args (uses init-computed paths).
7. Focused future tests expanded from 7 to 9 (added project-local path, DB failure cleanup, move failure partial).

Tests run:
- Dataset adapter: 11 passed (unchanged).
- Full suite: 1203 passed, 0 warnings.
- No production code changed.

Reviewer focus:
- Section 4 (project-local .staging path).
- Section 5 (ArchiveStager API: init params, stage, move, cleanup).
- Section 7 (cleanup policy matrix — 5 scenarios).
- Section 8 (transaction ordering aligned with 060A and 059Z).
