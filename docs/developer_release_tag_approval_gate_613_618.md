# Developer Release Tag Approval Gate - Tasks 613-618

Date: 2026-06-12

## Decision

READY FOR USER APPROVAL after this approval-gate document is committed.

No git tag was created, pushed, deleted, or moved in this task. Because git tag
creation changes repository release state and can trigger CI packaging, Codex
should perform the tag operation only after explicit user approval.

## Proposed Tag

| Property | Value |
|---|---|
| Tag name | `v0.4.0-dev` |
| Tag type | Annotated git tag |
| Tag target | The committed approval-gate HEAD |
| Package version | `0.4.0.dev0` |
| Release type | Developer pre-release, not public 1.0 |

Proposed tag message:

```text
v0.4.0-dev - Developer pre-release with async validation, cancellation support, session-aware quality gaps, structured quality issues, English quickstart, and CI packaging.
```

## Commands Prepared but Not Executed

Create the local annotated tag:

```powershell
git tag -a v0.4.0-dev -m "v0.4.0-dev - Developer pre-release with async validation, cancellation support, session-aware quality gaps, structured quality issues, English quickstart, and CI packaging."
```

Push the tag:

```powershell
git push origin v0.4.0-dev
```

## Approval Boundary

Codex should execute the tag commands after user approval.

Do not delegate this git tag operation to DeepSeek, Gemini, or another model:

- it is a repository release-state operation,
- it may trigger CI packaging,
- it is simple enough for Codex to execute directly after approval,
- it should not be bundled with unrelated edits.

## Pre-Approval Checks

| Check | Status | Notes |
|---|---|---|
| Existing local `v0.4.0*` tag | PASS | No matching local tag was found during review. |
| Focused desktop smoke | PASS | Startup and sample workflow smoke tests passed. |
| Whitespace check | PASS | `git diff --check` passed with CRLF warnings only. |
| Release type clarity | PASS | This is documented as a developer pre-release, not public 1.0. |
| Tag creation | NOT DONE | Waiting for explicit user approval. |

## Verification

Commands run:

```powershell
git tag --list "v0.4.0*"
.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py -q
git diff --check
```

Results:

- No local `v0.4.0*` tag exists.
- `12 passed`
- `git diff --check` passed with CRLF warnings only.

## Next Safe Action

Ask the user for explicit approval:

```text
Approve Codex to create and push the annotated tag v0.4.0-dev?
```

If approved, Codex should create the local tag first, then push it. After the
push, inspect the CI result or ask the user whether to proceed with GitHub
Actions observation.
