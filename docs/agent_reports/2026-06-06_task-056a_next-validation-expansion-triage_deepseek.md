# Task 056A — Next Validation Expansion Triage Design Only

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

1. Read required documents: SOUL.md, AGENTS.md, docs/PRD.md, docs/architecture.md, docs/task_board.md, docs/changelog.md, docs/review_notes/2026-06-06_task-053k_codex-reentry-audit.md, and this task file.
2. Surveyed current validation engine modules (stress_test.py, monte_carlo.py, walk_forward.py, walk_forward_matrix.py, elimination.py, validation_pipeline_service.py) via `explore` subagent.
3. Identified 4 candidate gaps for validation expansion:
   - **A: IS/OOS Stability Checks** — OOS max drawdown ratio, IS/OOS metric gap stability (PRD §12.2).
   - **B: Remove Best N Trades Stress Test** — surgically remove top-N trades (PRD §12.3 deferred).
   - **C: Monte Carlo Bootstrap + Confidence Intervals** — bootstrap resampling, 95% CI, worst-case equity curve (PRD §12.4 Alpha).
   - **D: IS Baseline Quality Gate** — early short-circuit for degenerate strategies.
4. Recommended **Task 056B — IS/OOS Stability Gate Implementation** as the next task, with rationale:
   - Most direct PRD alignment (§12.2 + SOUL §3.3 "OOS is Sacred").
   - Lowest risk (new elimination rules only, no engine changes).
   - Small scope (2-3 files, estimable in one focused task).
5. Created triage design note: `docs/next_validation_expansion_triage_056A.md`.
6. Updated `docs/changelog.md` with Task 056A entry.
7. Updated `docs/task_board.md` (Task 056A → Done, Task 056B → In Progress).

## Files Changed

| File | Change |
|---|---|
| `docs/next_validation_expansion_triage_056A.md` | **Created** — triage note with gap analysis, candidate comparison, and Task 056B recommendation |
| `docs/changelog.md` | Added Task 056A entry at top |
| `docs/task_board.md` | Task 056A → Done, Task 056B → In Progress |
| `docs/agent_reports/2026-06-06_task-056a_next-validation-expansion-triage_deepseek.md` | **Created** — this completion report |

## Verification

- **No production code changed** (design-only triage, per scope).
- **`git diff --check`**: ✅ passes (only doc whitespace, no trailing whitespace errors).
- **Git status**: Dirty only with expected doc/report files (no engine, test, or UI changes).

## Known Issues

- None.

## Risks

- None (design-only task).

## Suggested Next Task

**Task 056B — IS/OOS Stability Gate Implementation** as scoped in `docs/next_validation_expansion_triage_056A.md`:

- Add `_compute_oos_stability()` helper to `validation_engine/elimination.py`
- Add config fields to `EliminationConfig`: `max_oos_pf_degradation`, `max_oos_drawdown_ratio`, `max_oos_avg_trade_degradation`
- Wire new rules into `evaluate_elimination`
- Add focused tests for each new rule
- Update docs

## Handoff Prompt

```
Task 056B — IS/OOS Stability Gate Implementation.

Read:
1. SOUL.md
2. AGENTS.md
3. docs/PRD.md (especially §12.2, §12.3)
4. docs/architecture.md
5. docs/task_board.md
6. docs/changelog.md
7. docs/next_validation_expansion_triage_056A.md (the triage scope)
8. validation_engine/elimination.py
9. core/models/validation.py (EliminationConfig dataclass)
10. tests/test_elimination.py

Scope:
- Add _compute_oos_stability(oos_metrics, is_metrics) → dict to elimination.py computing:
  - IS/OOS profit factor gap ratio
  - IS/OOS max drawdown ratio  
  - IS/OOS avg trade gap
- Add config fields to EliminationConfig: max_oos_pf_degradation (0.5), max_oos_drawdown_ratio (2.0), max_oos_avg_trade_degradation (0.5)
- Wire new rules into evaluate_elimination
- Add focused tests in test_elimination.py
- Update changelog and task board
- Write completion report under docs/agent_reports/

Do NOT touch backtest engine, stress tests, Monte Carlo, walk-forward, pipeline defaults, or UI.
```
