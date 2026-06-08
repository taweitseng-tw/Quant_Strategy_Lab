# Next Milestone Decision Brief - Task 062A

> Decision-only. No production code changed.

## 1. Current State

- v0.2 validation expansion is complete.
- Reproducibility archive milestone is closed at engine, adapter, service, UI, and acceptance-test levels.
- Full suite evidence from Codex 061C review: 1256 passed.
- Data import is not considered broken; the prior `DataService.import_file()` failure was fixed during Codex 061C review.

## 2. Next Milestone Options

### Option A: Strategy Quality and Robustness Expansion

| Aspect | Detail |
|---|---|
| Objective | Add the remaining robustness diagnostics that directly attack fragile strategies: price-noise stress, Monte Carlo worst-case equity surface, and clearer WF equity evidence. |
| Why now | This best matches the project soul: kill weak curve-fit strategies before adding broader product polish. It builds on the completed validation and archive foundation. |
| Risks | Medium. Engine logic and reporting surfaces must avoid future leak and must not overstate robustness. |
| Likely files/modules | `validation_engine/`, `app/widgets/`, `app/ui/main_window.py`, `reports/`, focused validation tests. |
| Suggested first two-task batch | `062B-Design + 062C-Design - Price-Noise Stress Test Contract and WF Equity Evidence Surface Design`. |

### Option B: Data Workflow and Import UX Polish

| Aspect | Detail |
|---|---|
| Objective | Improve the first-mile workflow: import wizard clarity, dataset selection state, data quality visibility, and session/profile UX. |
| Why now | Better data UX reduces friction before research runs, but it is less central than robustness logic after the archive milestone. |
| Risks | Low to medium. Mostly UI/service wiring, but file path and dataset state must remain reproducible. |
| Likely files/modules | `data_engine/`, `app/services/data_service.py`, `app/ui/main_window.py`, `app/widgets/`, dataset tests. |
| Suggested first two-task batch | `062B-Design + 062C-Design - Dataset Selection State Audit and Import UX Gap Design`. |

### Option C: Strategy Generation and GA Research Visibility

| Aspect | Detail |
|---|---|
| Objective | Add GA/strategy generation diagnostics: population diversity, convergence evidence, duplicate strategy detection, and better build provenance display. |
| Why now | Generation quality matters, but without stronger robustness evidence it may create more candidates than the lab can safely judge. |
| Risks | Medium to high. Fitness and generation changes can accidentally encourage curve fitting if not paired with validation gates. |
| Likely files/modules | `strategy_engine/`, `validation_engine/`, `app/widgets/`, `app/ui/main_window.py`, strategy persistence tests. |
| Suggested first two-task batch | `062B-Design + 062C-Design - GA Diversity Metric Contract and Convergence Evidence Surface Design`. |

### Option D: System Hardening and Developer Velocity

| Aspect | Detail |
|---|---|
| Objective | Reduce friction: test runtime triage, CI smoke command, encoding/mojibake cleanup priorities, and packaging-readiness audit. |
| Why now | Useful for long-term maintainability, but less product-visible than robustness or data workflow. |
| Risks | Low. The main risk is spending a round on cleanup without improving user research capability. |
| Likely files/modules | `tests/`, `scripts/`, `docs/`, packaging metadata, selective app/service modules. |
| Suggested first two-task batch | `062B-Audit + 062C-Design - Test Runtime Triage and CI Smoke Contract`. |

## 3. Recommendation

### Recommended Default: Option A - Strategy Quality and Robustness Expansion

Rationale:

1. It is most aligned with the project mission: robustness over profit screenshots.
2. The archive milestone now preserves evidence; the next best use of that foundation is producing stronger evidence.
3. It stays safely inside research/backtesting scope and avoids live trading, broker, portfolio, and zip/import-UI expansion.
4. The first batch can be design-only, keeping risk controlled before touching engine logic.

## 4. Recommended First Batch

**Batch 062B-Design + 062C-Design - Price-Noise Stress Test Contract and WF Equity Evidence Surface Design**

- 062B-Design: Define a price-noise stress test contract, assumptions, deterministic seed behavior, no-future-leak constraints, metrics, and focused tests.
- 062C-Design: Define the WF equity evidence surface for UI/report output, including required data shape, rendering scope, failure states, and acceptance tests.

Do not implement either feature in the first batch.

## 5. Decision Notes

- Option B is the best alternate if the user wants immediate UI workflow polish.
- Option C should wait until robustness evidence is stronger, otherwise generation improvements may amplify weak candidates.
- Option D can be inserted between feature batches if test runtime or developer friction becomes painful.

## 6. Metadata

- Author: Codex
- Date: 2026-06-08
