# Untracked File Hygiene Inventory — Task 064D

> Documentation-only inventory. No files were deleted or moved.
> Generated: 2026-06-09

## Summary

After Task 064B (post-063F milestone state review), 19 untracked doc files were found across three documentation locations plus one local `.codegraph/` tool-state directory.

---

## 1. `docs/agent_reports/` — 11 untracked files

All follow the established naming convention `<date>_<task>_<agent>.md` and are standard task handoff artifacts.

| # | File | Classification |
|---|---|---|
| 1 | `2026-06-08_task-062h-impl_062i-design_wf-equity-chart-widget-and-price-noise-ui-controls-design_deepseek.md` | keep as task artifact |
| 2 | `2026-06-08_task-062j-impl_062k-design_price-noise-ui-controls-and-report-display-design_deepseek.md` | keep as task artifact |
| 3 | `2026-06-08_task-062l-impl_062m-design_price-noise-report-display-and-widget-design_deepseek.md` | keep as task artifact |
| 4 | `2026-06-08_task-062n-impl_price-noise-widget-display-implementation_deepseek.md` | keep as task artifact |
| 5 | `2026-06-08_task-062o_price-noise-acceptance-smoke_deepseek.md` | keep as task artifact |
| 6 | `2026-06-08_task-063a-decision_user-directed-milestone-decision_deepseek.md` | keep as task artifact |
| 7 | `2026-06-08_task-063b-design_063c-design_mc-worst-case-equity-and-wf-efficiency-precheck-design_deepseek.md` | keep as task artifact |
| 8 | `2026-06-08_task-063d-impl_mc-worst-case-equity-engine_deepseek.md` | keep as task artifact |
| 9 | `2026-06-08_task-063e-impl_mc-widget-wfe-precheck_deepseek.md` | keep as task artifact |
| 10 | `2026-06-09_task-063f-impl_mc-worst-case-equity-report-tables_deepseek.md` | keep as task artifact |
| 11 | `2026-06-09_task-064b_post-063f-milestone-state-review_deepseek.md` | keep as task artifact |

**Total: 11 files, all standard task artifacts. No action required beyond eventual commit.**

---

## 2. `docs/` — 8 untracked design / decision / acceptance files

These are design contracts, milestone decisions, and acceptance smoke documents generated during the 062–064 task series.

| # | File | Classification | Notes |
|---|---|---|---|
| 1 | `mc_worst_case_equity_surface_design_063B.md` | keep as task artifact | Design contract; scope implemented in 063D/063E/063F |
| 2 | `next_milestone_decision_063A.md` | keep as task artifact | Milestone decision record |
| 3 | `next_milestone_decision_064B.md` | keep as task artifact | Milestone decision record |
| 4 | `price_noise_acceptance_smoke_062O.md` | keep as task artifact | Acceptance smoke for price-noise feature |
| 5 | `price_noise_report_display_design_062K.md` | keep as task artifact | Design contract; scope implemented |
| 6 | `price_noise_ui_controls_design_062I.md` | keep as task artifact | Design contract; scope implemented |
| 7 | `price_noise_widget_display_design_062M.md` | keep as task artifact | Design contract; scope implemented |
| 8 | `wf_efficiency_ui_and_precheck_toggle_design_063C.md` | keep as task artifact | Design contract; scope mostly implemented |

**Total: 8 files, all design/decision records. No action required beyond eventual commit.**

---

## 3. `docs/archive/` — directory with 2 files

| # | File | Classification |
|---|---|---|
| 1 | `changelog_archive.md` (3443 lines) | resolved in 064G |
| 2 | `task_board_done_archive.md` (396 lines) | resolved in 064G |

**Notes:**
- Both files were created during the 2026-06-09 "Changelog and Task Board Archive" task but were never committed.
- They are referenced by `docs/context_brief.md` (lines 80–81) and `docs/task_board.md` (lines 57–59, 73–76) as the canonical location for historical records.
- **Codex decision:** Task 064G classifies these as repository documentation artifacts. They should stay visible to Git and be committed with the accepted documentation batch so active references remain valid in future checkouts.

---

## 4. `.codegraph/` local tool-state directory

| Path | Classification | Notes |
|---|---|---|
| `.codegraph/` | resolved in 064F | Contains `codegraph.db`, WAL/SHM files, `daemon.log`, `daemon.pid`, and its own `.gitignore`. This is local tool-state and is now explicitly ignored by the repository-level `.gitignore`. |

**Codex decision:** Task 064F adds `.codegraph/` to the repository-level `.gitignore`. The directory is local tool-state and should not be committed as repository documentation.

---

## 5. `.gitignore` note

- `docs/agent_reports/` is not gitignored; the tracked agent reports are already part of the repository.
- `docs/archive/` is not gitignored.
- `.codegraph/` contains local generated database/log/process files and is not documentation. It is ignored by root `.gitignore` as of Task 064F.

---

## 6. Classification Key

| Classification | Meaning |
|---|---|
| **keep as task artifact** | Standard generation from the task workflow. Should be committed when the batch is accepted. |
| **archive later** | No longer needed in the active tree; candidate for moving to `docs/archive/` in a future cleanup batch. |
| **needs Codex decision** | Requires higher-level policy determination before action. |
