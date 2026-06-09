# User-Directed Milestone Decision — Task 063A

> Decision-only. No production code changed.

## 1. Current State

- **v0.2 Alpha validation expansion** — tagged `v0.2-alpha-validation-expansion`
- **Reproducibility archive** — closed (061E)
- **Price-noise stress + WF equity chart** — complete (062A–O)
- **Latest full-suite evidence**: 1291 passed from Task 062O acceptance smoke.
- **Data import status**: not considered broken. The stale `DataService.import_file()` regression from 061C was already fixed during Codex review, and focused data workflow tests pass.

## 2. Options

### A: Strategy Quality / Robustness Expansion

| Aspect | Detail |
|---|---|
| **Goal** | MC worst-case equity curve, WF efficiency display polish, precheck UI toggle |
| **Why now** | Completes remaining PRD §12 validation items |
| **Files** | `validation_engine/`, `app/widgets/`, `reports/` |
| **Risk** | Low — engine + display, no new architecture |
| **First batch** | 063B-Design + 063C-Design — MC worst-case equity design + WF efficiency display design |

### B: Data Workflow Polish

| Aspect | Detail |
|---|---|
| **Goal** | Improve import wizard clarity, dataset selection state, data-quality visibility, and session/profile workflow |
| **Why now** | Data import is the first user experience; polish would reduce friction, but it is no longer a known blocker |
| **Files** | `data_engine/`, `app/services/`, `app/ui/` |
| **Risk** | Low to medium — mostly UI/service wiring, but dataset state must remain reproducible |
| **First batch** | 063B-Design + 063C-Design — Dataset selection state audit + import UX gap design |

### C: GA/GP Research Visibility

| Aspect | Detail |
|---|---|
| **Goal** | Strategy detail view improvements, GA convergence charts, GP tree visualization |
| **Why now** | GA is core strategy generator; current display is sparse |
| **Files** | `strategy_engine/`, `app/widgets/`, `app/ui/` |
| **Risk** | Medium — fitness visualization touches engine + UI |
| **First batch** | 063B-Design + 063C-Design — GA convergence metric design + strategy detail display design |

### D: System Hardening / Release Hygiene

| Aspect | Detail |
|---|---|
| **Goal** | Add CI smoke config, update README, audit docs/test runtime, and clean stale milestone notes |
| **Why now** | Reduces friction; prepares for broader distribution |
| **Files** | All — cross-cutting |
| **Risk** | Low — no new features |
| **First batch** | 063B-Audit + 063C-Design — CI smoke contract + docs/test-runtime hygiene plan |

## 3. Recommendation

**Option A — Strategy Quality / Robustness Expansion.**

Rationale:
- This is most aligned with the project soul: robustness over profit screenshots.
- The archive and price-noise/WF evidence work now preserve and display stronger evidence; the next best step is continuing to attack fragile strategies.
- The alleged `DataService.import_file()` blocker is stale. Focused data tests pass, and the full-suite evidence from 062O is 1291 passed.
- Data workflow polish remains a valid alternate path, but it should not be justified as a current import failure fix.

## 4. Recommended Next Batch

| Batch | Scope |
|---|---|
| **063B-Design** | Monte Carlo worst-case equity evidence surface: required data shape, report/UI display, failure states, and focused tests. |
| **063C-Design** | WF efficiency display polish and IS-baseline precheck UI toggle contract. |
| Type | Design-first batch before implementation |
| Verification | No production code changed; run focused data tests to preserve the corrected import status and targeted validation/report/widget tests once implementation begins. |

## 5. Codex Review Correction

- DeepSeek's first-pass recommendation did **not** pass Codex review because it relied on a stale claim of 13 `DataService.import_file()` failures.
- Codex verification on 2026-06-08: `.\.venv\Scripts\python.exe -m pytest tests\test_data_page_wiring.py tests\test_dataset_persistence_wiring.py -q` — **14 passed**.
- Corrected recommendation: Option A, with data workflow polish kept as an alternate instead of a blocker fix.

## 6. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-08
- **Codex correction**: 2026-06-08
