# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Task 058A - v0.2 Cleanup and Hardening Audit.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-07_task-057u-fix_057v-milestone-decision_post-tag-doc-reconciliation-and-next-milestone_codex-review.md`
8. `docs/post_v0.2_milestone_decision_057V.md`
9. This task file

## Context

v0.2 Alpha validation expansion is tagged as `v0.2-alpha-validation-expansion` and points to `1a9c533`. Codex accepted post-tag documentation reconciliation. The recommended next direction is a low-risk v0.2 cleanup/hardening audit before starting v0.3 feature work.

## Scope

### Do

- Perform an audit-only pass for v0.2 cleanup/hardening.
- Create `docs/v0.2_cleanup_hardening_audit_058A.md`.
- Focus on:
  - lingering documentation drift
  - test coverage gaps around 056/057 validation expansion features
  - small edge-case risks in reports/widgets/pipeline config
  - known warning triage
  - generated artifact hygiene
- Classify each finding as:
  - blocker
  - recommended cleanup
  - defer
- Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-058a_v0.2-cleanup-hardening-audit_deepseek.md`

### Do Not

- Do not change production Python code.
- Do not change tests unless documenting an audit fixture is impossible without it.
- Do not create, delete, move, retarget, or push any git tag.
- Do not add broad ignore rules.
- Do not delete, move, archive, or commit generated project brief artifacts.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `docs/v0.2_cleanup_hardening_audit_058A.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-058a_v0.2-cleanup-hardening-audit_deepseek.md`

## Acceptance Criteria

1. Audit file exists and is audit-only.
2. Findings are classified as blocker, recommended cleanup, or defer.
3. Audit covers docs, tests, report/widget/pipeline edge risks, known warning, and generated artifact hygiene.
4. Audit recommends exactly one next two-task batch.
5. Changelog and task board are updated.
6. Completion report is created.
7. Full suite, `git diff --check`, tag verification, and agent status pass.

## Verification

Run:

```powershell
git show --no-patch --decorate --date=iso --format=fuller v0.2-alpha-validation-expansion
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Tag remains unchanged and points to `1a9c533`.
- Full suite passes with only known pre-existing warning.
- `git diff --check` passes.
- Agent status shows Task 058A completion report as latest report.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
