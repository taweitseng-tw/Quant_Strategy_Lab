# Codex Review - Task 056E-Fix Remove Best N Trades Stress Design Hardening

Date: 2026-06-06
Reviewer: Codex
Verdict: Needs Fix
Score: 8.4 / 10

## Summary

Task 056E-Fix corrected the main design ideas in the first half of `docs/remove_best_n_trades_stress_design_056E.md`: degradation semantics are now aligned with existing `StressTestResult.degradation`, `pnl_loss_ratio` is separated for pass/fail, engine-only implementation is recommended first, and insufficient trade count is no longer a free pass.

However, the design note still contains an old duplicated pipeline section after the corrected deferred pipeline section. That stale section reintroduces the exact contradictions this fix was meant to remove.

## Findings

### P1 - Stale duplicated pipeline section still contradicts the corrected design

The corrected design now has:

- `4.1 First Task: Engine-Only`
- `4.2 Later Task: Pipeline Integration`
- `4.3 Pipeline Configuration (Deferred)`
- `4.4 Pipeline Wiring (Deferred)`

But the document then repeats old sections:

- `4.1 PipelineConfig Addition`
- `4.2 Pipeline Wires After Existing Stress Tests`

The stale section also still contains the typo `degration_threshold`.

Required correction:

- Delete the stale duplicated `4.1 PipelineConfig Addition` and `4.2 Pipeline Wires After Existing Stress Tests` sections.
- Confirm `rg -n "degration|PipelineConfig Addition|Pipeline Wires After Existing Stress Tests" docs/remove_best_n_trades_stress_design_056E.md` returns no matches.
- Keep only the corrected deferred pipeline section.

## Verification

- Reviewed `docs/remove_best_n_trades_stress_design_056E.md`.
- Ran targeted search and found stale `degration_threshold` still present.
- Confirmed no production code or tests were changed.

## Decision

Do not implement Task 056E-Impl yet. Run a narrow Task 056E-Fix2 to remove stale duplicated design text.

## Next Task

Task 056E-Fix2 - Remove Best N Trades Design Duplicate Cleanup.
