# Task 056A-Fix — OOS Stability Triage Data Path Correction

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

1. Read required files: SOUL.md, AGENTS.md, docs/PRD.md, docs/architecture.md, docs/task_board.md, docs/changelog.md, `docs/next_validation_expansion_triage_056A.md`, `docs/review_notes/2026-06-06_task-056a_next-validation-expansion-triage_codex-review.md`, `app/services/validation_pipeline_service.py`, `validation_engine/elimination.py`.

2. Resolved **P1 — OOS data path** (Codex score 7.4):
   - Traced the current pipeline: `split_by_ratio()` → backtest on `split.train` only → `evaluate_elimination(baseline.metrics, elim_cfg)` with **no OOS metrics**.
   - Confirmed `split.oos` exists in memory but is never backtested.
   - Confirmed `evaluate_elimination()` already accepts `oos_metrics` parameter but is never called with OOS data.
   - **Decision**: Recommend single task (056B) that includes OOS backtest + pipeline wiring + stability rules, because OOS plumbing alone (~5 lines) is too small to split.

3. Resolved **P2 — wrong file references**:
   - `EliminationConfig` lives in `validation_engine/elimination.py`, not `core/models/validation.py`.
   - Corrected both the triage document and the handoff prompt guidance.

4. Revised `docs/next_validation_expansion_triage_056A.md`:
   - Added "Data Path Correction" section with pipeline trace diagram.
   - Corrected Task 056B scope to include OOS backtest in pipeline + `oos_metrics` pass-through + stability rules.
   - Corrected all file references.

## Files Changed

| File | Change |
|---|---|
| `docs/next_validation_expansion_triage_056A.md` | Revised — added OOS data path analysis, corrected scope, corrected file refs |
| `docs/changelog.md` | Added Task 056A-Fix entry |
| `docs/agent_reports/2026-06-06_task-056a-fix_oos-stability-data-path-correction_deepseek.md` | **Created** — this completion report |

## Verification

- **No production code changed** (design-only correction, per scope).
- **`git diff --check`**: ✅ passes.
- **Git status**: Dirty only with expected doc/report files.

## Known Issues

- None.

## Risks

- None (design-only task).

## Suggested Next Task

**Task 056B — IS/OOS Stability Gate Implementation** with corrected scope:

```python
# Pipeline: after baseline backtest (app/services/validation_pipeline_service.py)
oos_baseline = run_backtest(strategy, split.oos, instrument=instrument, **backtest_kwargs)
# Then in elimination call:
elim = evaluate_elimination(baseline.metrics, elim_cfg, oos_metrics=oos_baseline.metrics, ...)
```

Full corrected scope in `docs/next_validation_expansion_triage_056A.md` under "Corrected Proposed Scope for Task 056B".

## Handoff Prompt

```
Task 056B — IS/OOS Stability Gate Implementation.

Read:
1. SOUL.md
2. AGENTS.md
3. docs/PRD.md (§12.2 specifically)
4. docs/architecture.md
5. docs/task_board.md
6. docs/changelog.md
7. docs/next_validation_expansion_triage_056A.md (especially corrected scope)
8. app/services/validation_pipeline_service.py
9. validation_engine/elimination.py
10. tests/test_elimination.py (existing tests)

Scope:

=== app/services/validation_pipeline_service.py — OOS pipe ===
After the baseline IS backtest (around line 110), add:
    oos_baseline = run_backtest(strategy, split.oos, instrument=instrument, **backtest_kwargs)
Then in the elimination call (around line 212), pass:
    elim = evaluate_elimination(
        baseline.metrics, elim_cfg,
        oos_metrics=oos_baseline.metrics,
        ...
    )
Add oos_pnl warning for degenerate OOS segment (0 trades, too short).

=== validation_engine/elimination.py — stability rules ===
1. Add to EliminationConfig:
   max_oos_pf_degradation: float | None = None
   max_oos_drawdown_ratio: float | None = None
   max_oos_avg_trade_degradation: float | None = None

2. Add _compute_oos_stability(oos_metrics, is_metrics) -> dict helper:
   - pf_degradation = oos_pf / is_pf  (if is_pf > 0, else None)
   - drawdown_ratio = oos_dd / is_dd  (if is_dd > 0, else None)
   - avg_trade_degradation = oos_avg_trade / is_avg_trade (if is_avg_trade > 0, else None)

3. In evaluate_elimination(), when oos_metrics is provided:
   - Call _compute_oos_stability().
   - Check max_oos_pf_degradation: if None or pf_degradation < threshold → fail.
   - Check max_oos_drawdown_ratio: if None or drawdown_ratio > threshold → fail.
   - Check max_oos_avg_trade_degradation: if None or avg_trade_degradation < threshold → fail.

=== tests ===
Add focused test_elimination.py tests for each new rule:
- pf_degradation passes, pf_degradation fails
- drawdown_ratio passes, drawdown_ratio fails
- avg_trade_degradation passes, avg_trade_degradation fails
- OOS metrics absent → rules silently skipped (default None)

Do NOT touch backtest engine, stress tests, Monte Carlo, walk-forward, pipeline defaults, or UI.
```
