# Agent Reports

Agents write completion reports here so the next reviewer can inspect local files instead of reading pasted chat history.

Use this filename pattern:

```text
YYYY-MM-DD_task-name_agent.md
```

Use this report shape:

```markdown
# YYYY-MM-DD - Task Name - Agent

## Completed

- ...

## Files Changed

- ...

## Verification

- Command: `...`
- Result: ...

## Known Issues

- ...

## Risks

- ...

## Suggested Next Task

- ...

## Notes for Codex Review

- ...
```

Keep reports short, factual, and tied to files and commands. Do not paste full test logs unless a failure needs a specific excerpt.

