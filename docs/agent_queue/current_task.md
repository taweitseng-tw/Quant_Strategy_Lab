# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 057Q-Docs + 057R-ReleaseNotes - README Milestone Sync and v0.2 Release Notes.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/review_notes/2026-06-06_task-057m-fix_057p-audit_acceptance-smoke-hardening-and-v0.2-release-readiness_codex-review.md`
8. `docs/v0.2_release_readiness_audit_057P.md`
9. This task file

## Context

Codex accepted Batch 057M-Fix + 057P-Audit with score 8.9 / 10. The v0.2 alpha validation expansion slice is GO, but release docs need final cleanup before a clean v0.2 baseline. `README.md` still says `Prototype v0.0.1`, and generated project brief artifacts are present under `docs/` but must not be committed into the release baseline without explicit approval.

## Scope

### Do

- Complete two sequential tasks:
  - Task 057Q-Docs - README Milestone Sync and Generated Brief Artifact Hygiene
  - Task 057R-ReleaseNotes - v0.2 Alpha Validation Expansion Release Notes
- For Task 057Q-Docs:
  - Update `README.md` current milestone from `Prototype v0.0.1` to `v0.2 Alpha - validation expansion release-ready`.
  - Replace the prototype goal text with a concise v0.2 alpha validation expansion summary.
  - Keep the financial/research-only posture intact; do not imply trading advice or live trading readiness.
  - Add targeted `.gitignore` entries for generated local project brief artifacts only after verifying no tracked file would be ignored.
  - Do not delete or move `docs/project_brief_2026-06-06*` files in this task.
- For Task 057R-ReleaseNotes:
  - Create `docs/v0.2_alpha_validation_expansion_release_notes_057R.md`.
  - Summarize completed 056/057 validation expansion capabilities.
  - Include verification summary: acceptance smoke, full suite, known warning.
  - Include known deferred items from `docs/v0.2_release_readiness_audit_057P.md`.
  - Include release caveats: research/backtesting only, no financial advice, no live trading.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-06_task-057q-docs_057r-release-notes_readme-sync-and-v0.2-release-notes_deepseek.md`

### Do Not

- Do not add new product features.
- Do not change production Python code.
- Do not delete, move, archive, or commit generated project brief artifacts.
- Do not create a git tag.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `README.md`
- `.gitignore`
- `docs/v0.2_alpha_validation_expansion_release_notes_057R.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-06_task-057q-docs_057r-release-notes_readme-sync-and-v0.2-release-notes_deepseek.md`

## Acceptance Criteria

1. README current milestone no longer says `Prototype v0.0.1`.
2. README v0.2 summary is accurate, concise, and does not imply live trading or financial advice.
3. `.gitignore` handles generated local project brief artifacts without hiding intended source docs broadly.
4. v0.2 release notes summarize capabilities, verification, caveats, and deferred items.
5. Changelog and task board are updated.
6. Completion report is created.
7. `git diff --check`, full suite, and agent status pass.

## Verification

Run:

```powershell
git check-ignore -v docs/project_brief_2026-06-06.pdf docs/project_brief_2026-06-06.pptx docs/~$project_brief_2026-06-06.pptx
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
```

Expected:

- Generated project brief binary/temp artifacts are ignored by targeted rules.
- Full suite passes with only known pre-existing warnings.
- `git diff --check` passes.
- Agent status shows Batch 057Q-Docs + 057R-ReleaseNotes completion report as the latest report.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
