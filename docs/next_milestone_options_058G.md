# Next Milestone Decision Matrix — Task 058G

> For user / Codex decision. No production code changed.

## 1. Current State

- v0.2 Alpha tagged: `v0.2-alpha-validation-expansion` → `1a9c533`
- Full suite: 1103 passed, 0 warnings
- Zero blockers, zero unaddressed cleanup items

## 2. Three Next Directions

### A: v0.3 Validation/Robustness Expansion

| Aspect | Detail |
|---|---|
| **Goal** | Address remaining deferred PRD items: price noise stress test, MC worst-case equity, WF plotted charts, precheck UI toggle |
| **Files** | `validation_engine/`, `app/widgets/`, `reports/` |
| **Risk** | Medium — some items need design-first approach |
| **Value** | Completes PRD §12 validation backlog |
| **Agent** | DeepSeek (engine), Codex (review) |

### B: v1.0 Research Archive/Reproducibility Foundation

| Aspect | Detail |
|---|---|
| **Goal** | Design and build experiment packaging: strategy + build config + dataset + instrument + validation result → self-contained archive |
| **Files** | `core/` models, `repository/`, new `archive/` module |
| **Risk** | High — architecture-level work, needs user decisions on format and scope |
| **Value** | Fulfills SOUL §3.4 "every strategy must have provenance" at archive level |
| **Agent** | Codex (design), DeepSeek (review), user (decisions) |

### C: UI Workflow Polish and Visual Inspection

| Aspect | Detail |
|---|---|
| **Goal** | Improve end-to-end user experience: data import wizard, build progress UX, results filtering, report preview, dark theme consistency |
| **Files** | `app/ui/`, `app/widgets/`, `reports/` |
| **Risk** | Low — mostly UI, no engine changes |
| **Value** | High discoverability for new users |
| **Agent** | Anti-Gravity (UI), DeepSeek (service layer), Codex (review) |

## 3. Recommendation

### **B — v1.0 Research Archive/Reproducibility Foundation (design-first).**

Rationale:
- The PRD says "every strategy must have provenance" (SOUL §3.4) and the prototype has rich data but no systematic way to package a complete experiment.
- The validation and backtest engines are mature enough to support archiving.
- Starting with a design-only batch (architecture doc + user decisions) keeps scope safe before implementation.

## 4. Recommended Next Two-Task Batch

**Task 059A-Design + 059B-Design — Reproducible Experiment Archive Architecture Design**

- 059A: Archive data model and storage format design
- 059B: Provenance schema and integrity verification design

Both are design-only. No implementation until user approves the architecture.

## 5. Metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-07
- **Awaiting**: User decision
