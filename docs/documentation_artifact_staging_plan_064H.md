# Documentation Artifact Staging Plan - Task 064H

> Documentation-only staging plan. No files were staged, committed, deleted, or moved.
> Generated: 2026-06-09

## Decision

Accepted documentation artifacts should be staged as documentation, while local tool-state stays ignored.

This plan is advisory. It does not stage or commit files.

## Artifact Groups

### Group A - Agent Reports

Stage accepted task reports under:

```text
docs/agent_reports/
```

Current untracked accepted reports:

- `2026-06-08_task-062h-impl_062i-design_wf-equity-chart-widget-and-price-noise-ui-controls-design_deepseek.md`
- `2026-06-08_task-062j-impl_062k-design_price-noise-ui-controls-and-report-display-design_deepseek.md`
- `2026-06-08_task-062l-impl_062m-design_price-noise-report-display-and-widget-design_deepseek.md`
- `2026-06-08_task-062n-impl_price-noise-widget-display-implementation_deepseek.md`
- `2026-06-08_task-062o_price-noise-acceptance-smoke_deepseek.md`
- `2026-06-08_task-063a-decision_user-directed-milestone-decision_deepseek.md`
- `2026-06-08_task-063b-design_063c-design_mc-worst-case-equity-and-wf-efficiency-precheck-design_deepseek.md`
- `2026-06-08_task-063d-impl_mc-worst-case-equity-engine_deepseek.md`
- `2026-06-08_task-063e-impl_mc-widget-wfe-precheck_deepseek.md`
- `2026-06-09_task-063f-impl_mc-worst-case-equity-report-tables_deepseek.md`
- `2026-06-09_task-064b_post-063f-milestone-state-review_deepseek.md`

### Group B - Design, Decision, Acceptance, and Policy Docs

Stage accepted standalone documentation artifacts under `docs/`:

- `docs/archive_historical_records_policy_064G.md`
- `docs/codegraph_hygiene_policy_064F.md`
- `docs/mc_worst_case_equity_surface_design_063B.md`
- `docs/next_milestone_decision_063A.md`
- `docs/next_milestone_decision_064B.md`
- `docs/post_063d_063e_063f_acceptance_smoke_064E.md`
- `docs/price_noise_acceptance_smoke_062O.md`
- `docs/price_noise_report_display_design_062K.md`
- `docs/price_noise_ui_controls_design_062I.md`
- `docs/price_noise_widget_display_design_062M.md`
- `docs/untracked_file_hygiene_064D.md`
- `docs/wf_efficiency_ui_and_precheck_toggle_design_063C.md`
- `docs/documentation_artifact_staging_plan_064H.md`

### Group C - Historical Archives

Stage curated historical records under:

- `docs/archive/changelog_archive.md`
- `docs/archive/task_board_done_archive.md`

These are repository documentation artifacts per Task 064G.

## Exclusions

Do not stage local tool-state or generated runtime files:

- `.codegraph/`
- databases
- WAL/SHM files
- logs
- PID files
- cache directories

Do not stage or commit production Python changes as part of this documentation-only grouping task.

## Recommended Commit Grouping

Use one documentation commit after Codex acceptance:

```text
docs: add accepted artifact inventory and archive policies
```

The commit should include only accepted documentation artifacts and policy updates. Production code and tests from unrelated implementation rounds should be reviewed separately.

## Verification

Required verification before any future staging:

```powershell
git status --short
git diff -- docs docs/agent_reports docs/archive
git diff --check
```

Expected result:

- Untracked docs are visible and classifiable.
- `.codegraph/` does not appear in `git status --short`.
- No production Python files are included in the documentation staging plan.
- `git diff --check` has no whitespace errors.
