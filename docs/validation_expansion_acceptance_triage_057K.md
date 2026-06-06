# Validation Expansion Acceptance Triage — Task 057K

> Design-only. No production code changed.

## 1. 057 Series — What Was Added

| Area | Capability | Tasks |
|---|---|---|
| **Bootstrap MC** | Engine, pipeline, display, UI controls, acceptance smoke | 057A-Impl/Fix, 057C/Design/Fix, 057D-Impl, 057E-Impl/Fix, 057F-Impl/Design, 057G-Impl |
| **WF Equity** | Per-window equity storage, pipeline config, serialization | 057B-Impl |
| **Triage** | Gap analysis and milestone direction | 057H-Design, 057K (this doc) |
| **WF Display** | Design-only (chart/table) | 057J-Design |

Full suite: **1084 passed**, 1 pre-existing warning.

## 2. Remaining Validation Gaps After 057J

| Gap | Status | Recommendation |
|---|---|---|
| WF equity widget display | Designed (057J), not implemented | Implement next |
| WF equity report display | Designed (057J), deferred | Follow after widget |
| Price noise stress test | Not started | Defer indefinitely |
| MC worst-case equity curve | Deferred to v0.3 | No action |
| Full v0.2 release hardening | Partial (056M audit exists) | After WF display |

## 3. Recommendation

**Implement WF equity display (057J-Impl)** — widget only first.

Rationale:
- Smallest remaining user-visible gap (~20 lines in widget, 2 tests).
- Completes the WF equity chain started in 057B.
- Closes the last "data stored but not shown" gap in the 057 series.
- After this, the 057 validation expansion is functionally complete and ready for a final acceptance checkpoint.

## 4. Next Task

**Task 057J-Impl — WF Per-Window Equity Widget Display** (widget only, ~20 lines).

## 5. Triage metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Dependencies**: 057J-Design — Done
