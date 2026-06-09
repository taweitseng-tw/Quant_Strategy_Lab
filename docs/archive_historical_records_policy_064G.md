# Archive Historical Records Policy - Task 064G

> Documentation-only repository hygiene decision.
> Generated: 2026-06-09

## Decision

`docs/archive/` is repository documentation, not local tool-state.

The current archive files should remain visible to Git and should be committed with the accepted documentation batch:

- `docs/archive/changelog_archive.md`
- `docs/archive/task_board_done_archive.md`

## Rationale

These files preserve historical changelog and task-board records that were moved out of active documents to keep routine agent context smaller. They are referenced by:

- `docs/context_brief.md`
- `docs/task_board.md`
- `docs/changelog.md`
- `docs/untracked_file_hygiene_064D.md`

Leaving them permanently untracked would make those references incomplete for future checkouts and agent handoffs.

## Boundary

This policy applies only to curated historical records under `docs/archive/`.

It does not apply to local generated tool-state such as:

- `.codegraph/`
- local databases
- logs
- PID files
- cache directories

Do not add a broad `docs/archive/` ignore rule. Documentation archives should stay reviewable.

## Current Files

| File | Policy |
|---|---|
| `docs/archive/changelog_archive.md` | Keep as repository documentation artifact |
| `docs/archive/task_board_done_archive.md` | Keep as repository documentation artifact |

## Verification

Required verification for this policy task:

```powershell
git status --short
git diff -- docs/archive docs/archive_historical_records_policy_064G.md docs/task_board.md docs/changelog.md docs/untracked_file_hygiene_064D.md docs/context_brief.md
git diff --check
```

Expected result:

- `docs/archive/` remains visible as documentation artifacts.
- No production Python files are changed by this task.
- `git diff --check` has no whitespace errors.
