# Hold Artifact Final Decision - Tasks 277-282

Decision document. No hold artifacts were edited, moved, staged, or deleted.
Generated: 2026-06-10

## Scope Reviewed

Current untracked hold artifacts:

| Artifact | Type | Decision For Developer Alpha | Decision For Formal Release |
|---|---|---|---|
| `AGENT_LOOP_README.md` | Local agent-loop documentation | Keep untracked | Exclude unless accepted as experimental tooling |
| `tools/agent_loop.py` | Local agent-loop Python tool | Keep untracked | Exclude unless accepted as experimental tooling |
| `scripts/agent_loop.ps1` | Local agent-loop PowerShell wrapper | Keep untracked | Exclude unless accepted as experimental tooling |
| `tools/__pycache__/` | Generated Python cache | Keep ignored/untracked | Exclude |

## Decision Rationale

### `AGENT_LOOP_README.md`

Decision: keep untracked for developer alpha.

Reasoning:
- It documents local Codex/Reasonix workflow automation.
- It is not required to launch the desktop app, import data, run a backtest, or
  generate a report.
- It references local automation state such as `.ai_loop/`, which is outside
  the evaluator workflow.

Formal release stance:
- Do not include it in a user-facing release unless Codex explicitly accepts an
  experimental tooling package.

### `tools/agent_loop.py`

Decision: keep untracked for developer alpha.

Reasoning:
- It is workflow orchestration tooling, not quant strategy, data, backtest,
  validation, reporting, or desktop UI functionality.
- It can run agent commands, capture diffs, parse reviews, and manage retries.
  That behavior is too broad to commit without a separate tooling review.
- It is not needed by evaluator smoke tests or desktop startup.

Formal release stance:
- Exclude from formal desktop release by default.
- If accepted later, place it under an explicit experimental or developer-tools
  policy with separate tests and documentation.

### `scripts/agent_loop.ps1`

Decision: keep untracked for developer alpha.

Reasoning:
- It is a wrapper for the local agent-loop workflow.
- It is not part of the desktop product workflow.
- It should not be mixed with release scripts until the Python tooling decision
  is made.

Formal release stance:
- Exclude from formal desktop release by default.
- Accept only if the full agent-loop toolchain is accepted.

### `tools/__pycache__/`

Decision: keep ignored/untracked.

Reasoning:
- It is generated Python cache output.
- It should never be part of source control or release packaging.

## Alpha Decision

These artifacts do not block developer-alpha readiness as long as they remain
untracked and outside the evaluator path.

Alpha-safe decision:
- Keep all hold artifacts untracked.
- Do not stage them.
- Do not delete them during this milestone unless the user explicitly asks.

## Formal Release Decision

These artifacts are not formal-release-ready.

Formal-release default:
- Exclude all hold artifacts from release scope.
- Revisit only if the project creates a separate developer-tooling acceptance
  task.

## Next Safe Action

Codex should close the hold-artifact blocker by accepting the current
"keep untracked" decision for developer alpha.

Recommended next task:
- Run or document a final alpha acceptance smoke packet using the accepted
  startup smoke, sample-data workflow smoke, and evaluator walkthrough.
