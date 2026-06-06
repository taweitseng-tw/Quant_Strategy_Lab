# Codex Review - Task 056J Validation Expansion Follow-up Triage Design

## Verdict

Needs fix before acceptance.

## Score

8.1 / 10

## Review Summary

The triage is useful and broadly aligned with the validation roadmap: it summarizes the current 056-series coverage and correctly recognizes that Monte Carlo, price-noise stress, and walk-forward visualization remain meaningful follow-up areas.

However, this note is intended to route the next production task, so precision matters. Codex found several non-code blockers in the design note.

## Blocking Findings

### P1 - Candidate count does not match the assignment

Task 056J asked for **Top 3 candidate next tasks**. The triage note lists 4 candidates: IS Baseline Quality Gate, MC Bootstrap + CI, Price Noise Stress Test, and WF Per-Window Equity Curves.

### P1 - PRD reference for the recommended task is inaccurate

The note says the IS Baseline Quality Gate is referenced by PRD Section 12.2 as "The pipeline runs too much work on strategies that can't pass core thresholds." Section 12.2 is actually about OOS pass standards. The cited text is not a stable PRD reference.

### P2 - Recommendation needs short-circuit visibility details

The recommended baseline gate proposes skipping stress/MC/WF for weak strategies. That may be valid if opt-in, but the design must state how the result/report makes the skip visible so users do not mistake missing validation evidence for passing validation.

## Verified

- No production code changed.
- `git diff --check` passed.
- Source inspection confirms current validation pipeline structure.

## Required Fix

Update the triage note to list exactly 3 candidates, correct PRD/AGENTS references, remove mojibake references, and clarify how short-circuit visibility would be handled before using the note to assign implementation.
