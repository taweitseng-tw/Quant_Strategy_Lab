# Milestone Direction Decision Brief — Task 056N

> Prepared for: User / Codex review
> Date: 2026-06-06
> Status: Ready for user decision

## Background

The v0.2 validation expansion series (056A–M) is complete and checkpointed. Full suite: **1038 passed, 0 failures**. The project is stable and ready for the next milestone.

This brief presents 4 candidate directions for the next work cycle. Choose one (or a blend), and execution resumes from a concrete next task.

---

## Candidate Directions

### Direction A: Complete Remaining Validation Gaps (Continue v0.2)

| Aspect | Detail |
|---|---|
| **Goal** | Finish PRD §12 validation backlog: MC bootstrap + CI, walk-forward per-window equity curves, precheck UI control |
| **Why now** | Validation engine is the most mature subsystem. MC/WF are the last Alpha items from PRD §12. Small pieces left. |
| **Files/modules** | `validation_engine/monte_carlo.py`, `validation_engine/walk_forward.py`, `app/widgets/`, `app/ui/main_window.py`, `reports/generator.py` |
| **Risk** | Low-Medium. Bootstrap requires statistical design; WF equity requires schema changes |
| **Verification** | Engine tests + pipeline tests + display tests + acceptance smoke (~15-20 new tests) |
| **Recommended agent** | DeepSeek V4 Pro (engine), Codex (review) |

### Direction B: Return to Prototype Gaps (Data / Instrument / Backtest Polish)

| Aspect | Detail |
|---|---|
| **Goal** | Address remaining prototype-level gaps: data quality checker UX, instrument profile editor polish, session template management, backtest assumption documentation |
| **Why now** | The prototype has rich validation but thin data/configuration UX. Users need solid data foundations before trusting validation output. |
| **Files/modules** | `data_engine/quality.py`, `app/widgets/instrument_editor.py`, `app/widgets/` data pages, `backtest_engine/` assumption docs |
| **Risk** | Low. Mostly UI polish and documentation. No engine redesign. |
| **Verification** | UI smoke tests + data import tests + manual walkthrough |
| **Recommended agent** | Anti-Gravity (UI), DeepSeek V4 Pro (engine changes if any), Codex (review) |

### Direction C: Strategy Generation Polish (GA/GP Workflow)

| Aspect | Detail |
|---|---|
| **Goal** | Improve GA/GP usability: better build progress display, generation stop conditions UI, strategy comparison UX, results ranking filtering |
| **Why now** | GA/GP are implemented but the workflow from "click Run" to "review ranked strategies" has friction. Users need clearer feedback during generation. |
| **Files/modules** | `app/widgets/build_page.py`, `app/services/ga_service.py`, `app/ui/main_window.py`, `app/widgets/results_page.py` |
| **Risk** | Low-Medium. UI changes but no engine redesign. Needs careful async/worker testing. |
| **Verification** | UI wiring tests + GA worker tests + manual workflow smoke |
| **Recommended agent** | Anti-Gravity (UI), DeepSeek V4 Pro (service layer), Codex (review) |

### Direction D: System-Wide Release Hardening

| Aspect | Detail |
|---|---|
| **Goal** | Harden the entire project for a v0.2 release: test coverage audit, edge-case stress, documentation cleanup, changelog finalization, release notes |
| **Why now** | The project has ~1038 tests but no broad release-quality audit. Before adding more, ensure existing code is release-grade across all modules. |
| **Files/modules** | All modules — audit scope, not implementation scope |
| **Risk** | Low. No new features. May discover pre-existing defects. |
| **Verification** | Full suite + coverage report + manual changelog/PRD gap review |
| **Recommended agent** | Codex (audit), DeepSeek V4 Pro (fixes), Anti-Gravity (minor fixes) |

---

## Recommended Default: **Direction A — Complete Remaining Validation Gaps**

**Rationale**:
1. Smallest remaining work in the most mature subsystem.
2. MC bootstrap and WF equity are the last explicit PRD §12 Alpha items.
3. After closing validation, the project can move cleanly to broader hardening (Direction D) or strategy/UI polish (B/C).
4. DeepSeek can execute independently with light Codex review.

---

## Next Task (After User Selection)

**Task 057A — `<Chosen Direction>` First Implementation Task**

Content depends on user's choice:

- If **A**: `Task 057A-Design — MC Bootstrap + CI Design Only`
- If **B**: `Task 057A — Data Quality Checker UX Audit and Fix`
- If **C**: `Task 057A — GA Build Progress UX Design Only`
- If **D**: `Task 057A — System-Wide Test Coverage Audit`

---

## Files Changed (this task)

None (design brief only).

## Brief metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Audience**: User / Codex
- **Status**: Awaiting user decision
