# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 057J-Design + 057K-Design - WF Equity Chart Display Design and 057 Validation Acceptance Triage.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-06_task-057g-impl_057h-design_bootstrap-acceptance-and-validation-gap-triage_codex-review.md`
8. `docs/validation_gap_triage_057H.md`
9. `docs/bootstrap_ui_config_controls_design_057F.md`
10. `docs/bootstrap_pipeline_report_surface_design_057C.md`
11. `docs/v0.2_validation_expansion_readiness.md`
12. This task file

## Context

Batch 057G-Impl + 057H-Design accepted the bootstrap feature chain and recommended WF per-window equity chart display as the smallest remaining user-visible validation gap. This batch is design-only. Do not implement charts.

## Scope

### Do

- Complete two sequential design-only tasks:
  - Task 057J-Design - WF Per-Window Equity Chart Display Design
  - Task 057K-Design - 057 Validation Expansion Acceptance Triage
- For Task 057J-Design:
  - Write `docs/wf_equity_chart_display_design_057J.md`.
  - Cover widget/report display surfaces for already-stored `walk_forward_summary["windows"][*]["equity_curve"]`.
  - Include data availability rules, empty/missing equity behavior, chart/table fallback, markdown/HTML strategy, no-new-dependency approach, test plan, and non-goals.
  - Decide whether first implementation should be widget only, report only, or both.
- For Task 057K-Design:
  - Write `docs/validation_expansion_acceptance_triage_057K.md`.
  - Summarize what 057 added across bootstrap MC and WF equity persistence.
  - List remaining validation gaps after 057J design.
  - Recommend exactly one next task:
    - implement WF equity display,
    - do validation expansion acceptance smoke,
    - or pause validation expansion for broader v0.2 hardening.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-057j-design_057k-design_wf-equity-display-and-validation-acceptance-triage_deepseek.md`

### Do Not

- Do not modify production code.
- Do not add tests.
- Do not add `worst_case_equity`.
- Do not change walk-forward production code.
- Do not implement charts.
- Do not modify UI widgets or reports.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `docs/wf_equity_chart_display_design_057J.md`
- `docs/validation_expansion_acceptance_triage_057K.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-057j-design_057k-design_wf-equity-display-and-validation-acceptance-triage_deepseek.md`

## Acceptance Criteria

1. 057J design identifies exact widget/report surfaces and no-dependency rendering approach.
2. 057J design defines behavior for missing/empty per-window equity curves.
3. 057J design has a focused implementation/test plan.
4. 057K triage accurately summarizes 057 completion and remaining validation gaps.
5. 057K recommends exactly one next task.
6. No production code or tests are changed.
7. Changelog and task board are updated.
8. Completion report is created.
9. `git diff --check` passes.

## Verification

Run:

```powershell
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- `git diff --check` passes.
- Agent status shows Batch 057J-Design + 057K-Design completion report as the latest report.
- No production code or tests are changed.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
