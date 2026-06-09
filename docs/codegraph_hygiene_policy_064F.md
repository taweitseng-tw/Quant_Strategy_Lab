# CodeGraph Hygiene Policy - Task 064F

> Documentation-only repository hygiene decision.
> Generated: 2026-06-09

## Decision

`.codegraph/` is local tool-state and must stay out of repository history.

The repository-level `.gitignore` now explicitly ignores:

```text
.codegraph/
```

## Rationale

The local `.codegraph/` directory contains generated machine-local state:

- `codegraph.db`
- `codegraph.db-wal`
- `codegraph.db-shm`
- `daemon.log`
- `daemon.pid`
- `.codegraph/.gitignore`

These files are not project documentation, source code, reproducibility artifacts, or review evidence. They can change while local tooling runs and should not appear in ordinary review diffs.

## Boundary

This policy applies only to `.codegraph/` local tool-state.

It does not apply to:

- `docs/agent_reports/`
- `docs/archive/`
- task design documents
- acceptance smoke documents
- changelog or task board records

Those files remain repository documentation artifacts and should be reviewed or committed according to task acceptance.

## Verification

Required verification for this policy task:

```powershell
git status --short
git diff -- .gitignore docs/codegraph_hygiene_policy_064F.md docs/untracked_file_hygiene_064D.md docs/task_board.md docs/changelog.md
git diff --check
```

Expected result:

- `.codegraph/` no longer appears as an untracked directory.
- No production Python files are changed by this task.
- `git diff --check` has no whitespace errors.
