# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 059A-Design + 059B-Design - Reproducible Experiment Archive Architecture and Provenance Integrity Design.

## Context Level

Level 3 - architecture, repository schema, product scope, and provenance design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `docs/next_milestone_options_058G.md`
9. `docs/review_notes/2026-06-07_task-058f-signoff_058g-decision_v0.2-cleanup-signoff-and-next-milestone-decision_codex-review.md`
10. This task file

## Context

v0.2 cleanup is complete. Codex selected the next direction as reproducible experiment archive / provenance foundation, but explicitly reframed it as a conservative post-v0.2 design milestone instead of a literal v1.0 implementation push.

This batch is design-only. The goal is to make future implementation safe by defining archive boundaries, provenance schema, integrity checks, and repository responsibilities before writing production code.

## Scope

### Do

- Complete two sequential design tasks:
  - Task 059A-Design - Reproducible Experiment Archive Architecture
  - Task 059B-Design - Provenance Schema and Integrity Verification
- For Task 059A:
  - Create `docs/archive_architecture_059A.md`.
  - Define the archive purpose, non-goals, user workflow, module boundaries, storage layout options, repository responsibilities, and export/import lifecycle.
  - Compare at least two storage formats, such as folder + manifest JSON and zipped archive package.
  - Recommend exactly one MVP archive format.
- For Task 059B:
  - Create `docs/provenance_integrity_design_059B.md`.
  - Define required provenance fields for strategy, dataset, instrument profile, session template, build config, backtest assumptions, validation config, software version, and source file references.
  - Define integrity checks, including content hashes, manifest version, missing-file detection, schema version handling, and non-financial-advice disclaimer preservation.
  - Recommend exactly one next two-task implementation batch.
- Update:
  - `docs/architecture.md` with a short design-level archive/reproducibility section only.
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-059a-design_059b-design_reproducible-experiment-archive-and-provenance-integrity_deepseek.md`

### Do Not

- Do not write production Python code.
- Do not change tests.
- Do not change repository schema or migrations.
- Do not create new runtime dependencies.
- Do not implement archive export/import yet.
- Do not rename existing modules or move existing files.
- Do not create, delete, move, retarget, or push any git tag.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `docs/archive_architecture_059A.md`
- `docs/provenance_integrity_design_059B.md`
- `docs/architecture.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-059a-design_059b-design_reproducible-experiment-archive-and-provenance-integrity_deepseek.md`

## Acceptance Criteria

1. Archive architecture design exists and recommends exactly one MVP archive format.
2. Provenance/integrity design exists and defines required fields plus verification checks.
3. `docs/architecture.md` is updated only at design level.
4. No production code, tests, schema migrations, or dependencies are changed.
5. Changelog and task board are updated.
6. Completion report is created.
7. `git diff --check` and agent status pass.
8. The report recommends exactly one next two-task implementation batch, but does not implement it.

## Verification

Run:

```powershell
git diff --check
powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1
git status --short
```

Expected:

- `git diff --check` passes.
- Agent status shows Batch 059A-Design + 059B-Design completion report as latest report.
- `git status --short` shows only files within this task scope.
- No production Python code or tests are changed.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Recommended next two-task batch
