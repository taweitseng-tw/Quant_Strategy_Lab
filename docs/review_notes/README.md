# Review Notes

Codex writes review notes here after checking an agent report, local file changes, and verification output.

Use this filename pattern:

```text
YYYY-MM-DD_task-name_codex-review.md
```

Use this review shape:

```markdown
# YYYY-MM-DD - Task Name - Codex Review

## Verdict

- Accepted / Needs Fix / Blocked

## Findings

- ...

## Files Reviewed

- ...

## Verification

- Command: `...`
- Result: ...

## Follow-up Task

- ...

## Handoff Prompt

```text
...
```
```

Reviews should prioritize correctness, architecture boundaries, missing tests, and documentation drift.

