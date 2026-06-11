# Version Roadmap and 1.0 Gap Rebaseline - Tasks 493-498

Date: 2026-06-11

## Purpose

This document gives a compact tracking baseline after Tasks 487-492. It separates three different counters so future reviews do not confuse task IDs, standardized six-task rounds, and formal 1.0 readiness.

## Round Count Baseline

### Task-ID Counter

- Latest completed task block: Tasks 493-498.
- Nominal six-task blocks by task ID: 498 / 6 = 83 blocks.
- Caveat: earlier project history includes lettered tasks and combined batches, so 83 is a task-ID counter, not a reliable count of actual model turns.

### Standardized Recent Round Counter

The modern six-task rhythm is reliably visible from Tasks 397-402 onward.

- Completed recent six-task rounds: 17 / 17.
- Range counted: 397-402 through 493-498.
- Current hardening milestone rounds: 7 / 7.
  - 457-462: milestone planning
  - 463-468: same-bar ambiguity audit and design
  - 469-474: same-bar ambiguity test verification
  - 475-480: tick rounding design
  - 481-486: tick rounding implementation
  - 487-492: acceptance audit
  - 493-498: roadmap and 1.0 gap rebaseline

### How to Report Going Forward

Each future Codex review should report:

```text
Current block: Tasks NNN-NNN
Recent standardized rounds: X completed / Y estimated
Current milestone: X/Y rounds
Formal 1.0 readiness: rough %
Remaining to 1.0: rough remaining rounds
```

## Current Status

### Developer-Alpha Readiness

Estimated: 95-97%.

Reason: local desktop startup, sample workflow, developer-alpha evidence, release packet, and focused backtest correctness hardening have been accepted in prior rounds.

Remaining alpha risk: evaluator environment differences and manual desktop walkthrough repeatability.

### Formal 1.0 Readiness

Estimated: 40-45%.

Reason: important engine and validation slices exist, but a formal 1.0 still needs broader end-to-end desktop workflow polish, data workflow hardening, UI chart reliability, packaging automation, release verification, and user-facing documentation.

This is intentionally conservative. It should not be treated as a release claim.

## Estimated Remaining Rounds to 1.0

Rough estimate: 20-30 six-task rounds.

Breakdown:

- Data import, normalization, and resampling hardening: 3-5 rounds.
- UI cockpit, charting, and workflow integration: 5-7 rounds.
- Strategy builder and report workflow polish: 3-5 rounds.
- Performance and large-file hardening: 3-4 rounds.
- Packaging automation and release candidate verification: 3-5 rounds.
- Final documentation, evaluator packet, and acceptance audit: 2-4 rounds.

## Next Milestone Sequence

1. Data Resampling and Normalization Hardening.
2. Desktop Workflow and Chart Reliability.
3. Strategy Builder and Report Polish.
4. Performance and Large-File Hardening.
5. Packaging Automation and Release Candidate Verification.
6. Formal 1.0 Acceptance Audit.

## Immediate Next Block

Tasks 499-504 should be executed as one integrated six-subtask block:

- Audit current resampler and normalization behavior.
- Identify edge cases and missing warnings.
- Design the smallest safe hardening slice.
- Add focused tests if code changes are made.
- Update task board and changelog.
- Stop for Codex review.
