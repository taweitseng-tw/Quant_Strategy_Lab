# Remaining Validation Gap Triage — Task 057H

> Design-only. No production code changed.

## 1. 057 Series Completed

The 057 series delivered bootstrap Monte Carlo end-to-end:

| Layer | Capability |
|---|---|
| Engine | `run_bootstrap_monte_carlo()` with local RNG, 95% CI, `MonteCarloResult.confidence_intervals` |
| Pipeline | Default-off config fields, wiring, serialization |
| Display | Widget card, markdown lines, HTML paragraphs with CI values |
| UI | Validate page controls (checkbox + iterations + confidence) |
| Tests | 11 engine + 3 pipeline + 6 display + 4 UI + 10 acceptance = 34 tests |

Full suite: 1084 passed.

## 2. Remaining PRD Validation Gaps

| Gap | PRD Reference | Status | Recommendation |
|---|---|---|---|
| Price noise stress test | §12.3 (deferred) | Not started | Low priority. Defer. |
| WF per-window equity charts | §12.5 (Alpha) | Equity stored, no charts | Display task. Medium priority. |
| Full validation acceptance audit | — | Partial (056L, 056M, 057H) | ~80% done. |
| System-wide release hardening | — | Not started | Cross-cutting. |

## 3. Recommended Next Task

**Task 057J — WF Per-Window Equity Chart Display (design first)**

Rationale:
- Equity data is already stored (057B-Impl). The gap is visualization only.
- Smallest remaining user-visible gap.
- Design-only first to avoid scope creep.

Alternative: If user prefers to close the bootstrap chapter, Task 057K — Bootstrap Feature Acceptance Sign-off (one doc + changelog only).

## 4. Triage metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Dependencies**: 057A-F — Complete
