# Post-063F Milestone State Review and Next Direction Brief — Task 064B

> Decision-only. No production code changed.

## 1. Current State After 063D/063E/063F

| Feature | Engine | Widget | Report |
|---|---|---|---|
| MC worst-case equity curve | `worst_case_equity_curve` field, opt-in `collect_worst_case_equity` | Orange line chart, labeled `trade-step` | Start/End + % change + disclaimer |
| WF Efficiency display | Already in pipeline output | Widget line (None → N/A) | Already present in reports |
| IS Baseline Precheck UI | Existing pipeline config | — | — |

### Evidence Surface Coverage

| Surface | MC worst-case equity | WFE | Precheck |
|---|---|---|---|
| Engine serialization | ✅ | ✅ (existing) | ✅ (existing) |
| UI controls | — | — | ✅ |
| Widget display | ✅ (063E) | ✅ (063E) | — |
| Report display | ✅ (063F) | ✅ (existing) | — |

## 2. Remaining Risks

| Risk | Severity | Notes |
|---|---|---|
| Context brief still lists completed features as "deferred" | Low | Stale since 062 series; cosmetic |
| Stale `DataService.import_file()` failure claim can re-enter handoffs | Medium | The old 13-failure claim was already rejected in 063A Codex review; focused data workflow tests currently pass |
| MC worst-case equity only works for missed-trade MC | Low | Other MC runners don't support it |
| No post-062/063 acceptance smoke document exists | Low | Feature-by-feature verification done per task |

## 3. Next Direction Options

### A: Strategy Quality / Robustness Expansion

PRD §12 remaining items: price-noise stress test (engine complete + UI done), MC worst-case equity (engine + widget + report complete). Little scope remains — this milestone is functionally complete.

### B: Data Workflow Polish

Data import wizard, import UX, and session filter polish. High user impact, but not currently justified by a known `DataService.import_file()` test failure.

### C: GA/GP Research Visibility

Strategy detail view improvements, GA convergence charts, GP tree visualization. Medium risk, engine + UI work.

### D: System Hardening / Cleanup

Fix context brief staleness, audit docs, clean up untracked files, bump test count in README. Low risk, cross-cutting.

## 4. Recommendation

### Option D — System Hardening / Cleanup

Rationale:
- The context brief is stale (prices-noise, MC worst-case, WF charts, precheck toggle listed as "deferred" but all implemented).
- The task board has duplicate entries (some tasks listed twice).
- 11 untracked agent report docs need cleanup.
- DeepSeek has twice reintroduced the stale `DataService.import_file()` failure claim, so cleanup must include explicit stale-risk removal from handoff context.
- A lightweight audit pass will reduce friction for the next real milestone.

### Suggested First Batches

1. **064C-Fix**: Update context brief to reflect current state.
2. **064D-Fix**: Task board deduplication + untracked file hygiene.
3. **064E-Acceptance**: Post-063D/063E/063F acceptance smoke document with current verification evidence, including focused data workflow tests to retire the stale DataService risk.

## 5. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-09
