# Post-v0.2 Milestone Decision Brief — Task 057V

> For user decision. No production code changed.

## Background

v0.2 Alpha validation expansion is tagged (`v0.2-alpha-validation-expansion` → `1a9c533`). The validation pipeline now has IS/OOS stability gates, remove-best-N stress, bootstrap MC, WF per-window equity, precheck, and full display/acceptance coverage. **1101 tests passing.**

## Three Next Directions

### Option A: Continue v0.2 Cleanup / Hardening

| Aspect | Detail |
|---|---|
| **Goal** | Stabilize the v0.2 validation expansion baseline: test coverage audit, edge-case stress, remaining display polish, documentation finalization |
| **Files/modules** | Docs, tests, minor widget/reports polish |
| **Risk** | Low (no new features) |
| **Recommended agent** | Codex (audit), Anti-Gravity (minor fix), DeepSeek (test/lint) |

### Option B: Switch to v0.3 Feature Completion

| Aspect | Detail |
|---|---|
| **Goal** | Address remaining deferred PRD items: price noise stress test, MC worst-case equity curve, WF plotted equity charts, precheck UI control |
| **Files/modules** | `validation_engine/`, `app/widgets/`, `reports/` |
| **Risk** | Medium (some items require design-first approach) |
| **Recommended agent** | DeepSeek (engine), Codex (design review) |

### Option C: Start v1.0 Reproducible Experiment Archive Design

| Aspect | Detail |
|---|---|
| **Goal** | Design how strategies, build configs, datasets, instrument profiles, and validation results are packaged into reproducible experiment archives |
| **Files/modules** | `core/` models, `repository/`, new `archive/` module |
| **Risk** | High (architecture-level work; needs user-stakeholder decisions) |
| **Recommended agent** | Codex (design), DeepSeek (design review), user (decision) |

## Recommendation

**Option A — v0.2 Cleanup / Hardening.**

Rationale: The v0.2 baseline is fresh. A short stabilization cycle (test audit, edge-case stress, docs polish) before v0.3 feature work prevents accumulating small debts. Low risk, quick win.

## Next Batch

**Task 058A — v0.2 Test Coverage Audit and Edge-Case Hardening** (audit-only first, then targeted fixes).

## Metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-07
- **Awaiting**: User decision
