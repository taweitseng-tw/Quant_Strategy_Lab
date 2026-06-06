# Codex Review - Task 056C OOS Stability Reporting Surface Design

Date: 2026-06-06
Reviewer: Codex
Verdict: Needs Fix
Score: 8.2 / 10

## Summary

Task 056C correctly identified the main product-surface gap: `PipelineResult.oos_metrics` is now computed, but the validation summary widget, report generator, and validation log do not display it.

The design should not be implemented as written yet. It recommends displaying stability ratios and pass/fail status in UI/report surfaces, but those ratios are not currently exposed as structured pipeline output. Implementing the recommendation directly would likely require recomputing OOS/IS stability ratios inside presentation code, which would weaken the UI/engine boundary.

## Findings

### P1 - Stability ratios are requested in presentation surfaces but are not exposed as structured output

The design recommends showing PF degradation, drawdown ratio, and average-trade degradation in `app/widgets/validation_summary.py` and `reports/generator.py`. Current `PipelineResult` exposes:

- `baseline_metrics`
- `oos_metrics`
- `elimination_result`

`elimination_result` includes warnings, failed rules, metrics snapshot, and config snapshot, but not a structured `oos_stability` payload. Without a new structured payload, the UI/report layer would need to recompute ratios from `baseline_metrics` and `oos_metrics`, duplicating validation logic outside the engine/service layer.

Required correction:

- Either narrow Task 056D to display only existing structured data:
  - OOS metrics.
  - Elimination warnings / failed rules that already mention configured stability gates.
- Or explicitly propose a later engine/service-layer payload such as `oos_stability: dict | None`, with tests, before UI/report displays raw ratios.

For the smallest safe next step, Codex recommends the first option: display OOS metrics and existing warning/fail text only.

## Non-Blocking Notes

- The design note contains mojibake/garbled symbols in diagrams and examples. This does not break implementation, but the fix should replace unclear symbols with ASCII text.
- The proposed Task 056D says not to add tests. For display work touching report output, at least focused report formatter tests or existing snapshot-style assertions should be considered if suitable local tests already exist.

## Verification

- Reviewed `docs/oos_stability_reporting_surface_design_056C.md`.
- Compared the design against:
  - `app/services/validation_pipeline_service.py`
  - `validation_engine/elimination.py`
  - `app/widgets/validation_summary.py`
  - `reports/generator.py`
  - `app/ui/main_window.py`
- Confirmed no production code or tests were changed.
- `git diff --check` was reported by the agent and should be rerun after the fix.

## Decision

Do not implement Task 056D from the current design. Run Task 056C-Fix first to narrow the implementation plan and preserve engine/UI separation.

## Next Task

Task 056C-Fix - OOS Stability Reporting Surface Design Correction.
