# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 058F-Signoff + 058G-Decision - v0.2 Cleanup Signoff and Next Milestone Decision.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `docs/review_notes/2026-06-07_task-058d-fix_058e-verify_normalizer-warning-suppression-and-zero-warning-verification_codex-review.md`
9. `docs/zero_warning_verification_058E.md`
10. This task file

## Context

Batch 058D-Fix + 058E-Verify was accepted by Codex. The full suite is now verified at 1103 passing tests with zero warnings. This batch is documentation/signoff only: close the 058 cleanup series cleanly, then recommend the next two-task milestone batch.

## Scope

### Do

- Complete two sequential tasks:
  - Task 058F-Signoff - Final v0.2 cleanup signoff
  - Task 058G-Decision - Next milestone direction decision matrix
- For Task 058F-Signoff:
  - Create `docs/v0.2_cleanup_signoff_058F.md`.
  - Summarize the accepted 058 cleanup series, latest verification state, remaining deferred items, and any non-blocking risks.
  - Include the exact verification evidence from Codex review: focused test passed, full suite 1103 passed, tag still points to `1a9c533`.
- For Task 058G-Decision:
  - Create `docs/next_milestone_options_058G.md`.
  - Compare exactly three next milestone directions:
    1. v0.3 validation/robustness expansion.
    2. v1.0 research archive/reproducibility foundation.
    3. UI workflow polish and visual inspection.
  - Recommend exactly one direction and exactly one next two-task batch.
  - Keep the recommendation aligned with SOUL.md, AGENTS.md, PRD, and architecture boundaries.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-058f-signoff_058g-decision_v0.2-cleanup-signoff-and-next-milestone-decision_deepseek.md`

### Do Not

- Do not change production Python code.
- Do not change tests.
- Do not create, delete, move, retarget, or push any git tag.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.
- Do not expand scope into implementation of the next milestone.

## Files Likely Involved

- `docs/v0.2_cleanup_signoff_058F.md`
- `docs/next_milestone_options_058G.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-058f-signoff_058g-decision_v0.2-cleanup-signoff-and-next-milestone-decision_deepseek.md`

## Acceptance Criteria

1. v0.2 cleanup signoff document exists and accurately summarizes the accepted cleanup state.
2. Next milestone decision matrix exists and compares exactly three options.
3. Exactly one next direction and exactly one next two-task batch are recommended.
4. No production code or tests are changed.
5. Changelog and task board are updated.
6. Completion report is created.
7. `git diff --check`, tag verification, and agent status pass.

## Verification

Run:

```powershell
git diff --check
git show --no-patch --decorate --date=iso --format=fuller v0.2-alpha-validation-expansion
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- `git diff --check` passes.
- Tag remains unchanged and points to `1a9c533`.
- Agent status shows Batch 058F-Signoff + 058G-Decision completion report as latest report.
- No production Python code or tests are changed.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
