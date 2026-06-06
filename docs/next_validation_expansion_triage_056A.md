# Next Validation Expansion Triage — Task 056A

> Design-only triage. No production code changed.

## Current Validation State (after 053-series)

The validation pipeline now runs these steps in order:

| Step | Status | Detail |
|---|---|---|
| IS/Val/OOS Split | ✅ | `split_by_ratio` (60/20/20 default) |
| Baseline backtest | ✅ | IS segment only |
| Commission ×2 stress | ✅ | `stress_commission_multiplier` |
| Slippage ×2 stress | ✅ | `stress_slippage_multiplier` |
| One-bar delay stress | ✅ | `stress_one_bar_delay` |
| Parameter perturbation | ✅ | `stress_parameter_perturbation` |
| Monte Carlo (missed-trade) | ✅ | `run_missed_trade_monte_carlo` |
| Walk-forward | ✅ | `walk_forward` with auto-sized windows |
| Walk-forward Matrix | ✅ | `walk_forward_matrix` (opt-in, `run_matrix=False` by default) |
| Elimination rules | ✅ | `evaluate_elimination` with configurable thresholds |

The full suite passes **965 tests** (1 pre-existing warning).

---

## Gaps Identified

### Gap A: IS/OOS Stability Checks (PRD §12.2, SOUL §3.3)

The PRD specifies several OOS pass criteria that are **not fully implemented**:

| Required criteria | Status | Implementation needed |
|---|---|---|
| OOS Net Profit > 0 | ✅ In elimination engine | — |
| OOS Profit Factor > threshold | ✅ In elimination engine | — |
| OOS Max Drawdown ≤ IS ratio | ❌ Missing | New rule in elimination engine |
| OOS Trade Count minimum | ❌ Missing | New rule + validation pipeline metric |
| IS/OOS metric gap stability | ❌ Missing | Gap % comparison across all core metrics |
| OOS equity curve direction check | ❌ Missing | Simple monotonic degradation check |

**Why this matters (SOUL §3.3)**: "OOS is Sacred. Always make IS/OOS degradation visible." Currently the pipeline runs OOS validation but does not systematically **quantify IS→OOS degradation** as a first-class check. The elimination engine has a few OOS thresholds but lacks the stability-gap analysis that would flag strategies whose IS performance masks OOS failure.

**Effort estimate**: Small-moderate (2-3 files, mostly new elimination rules + 1 metric helper).

---

### Gap B: Remove Best N Trades Stress Test (PRD §12.3 deferred)

PRD §12.3 lists "移除最佳 N 筆交易" (remove best N trades) as a deferred stress test. The idea: surgically remove the strategy's N best-performing trades and re-evaluate — if a strategy only passes because of 1-2 lucky outliers, it should be flagged.

This is distinct from `stress_random_missed_trades` (which drops random trades) — it's a **worst-case** rather than average-case analysis.

**Why this matters**: Complements parameter perturbation and one-bar delay as an additional "attack surface" on strategy robustness. Drops trades ranked by PnL, not randomly.

**Effort estimate**: Small (1 new function in `stress_test.py` + wiring in pipeline).

---

### Gap C: Monte Carlo Bootstrap + Confidence Intervals (PRD §12.4 Alpha)

PRD §12.4 specifies for Alpha: bootstrap sampling, confidence intervals, and worst-case equity curve. Current Monte Carlo supports missed-trade and slippage perturbation, but does **not**:
- Resample trade sequences with replacement (bootstrap)
- Compute 95% CI for key metrics
- Generate a worst-case equity curve projection

**Why this matters**: These are standard quant validation tools. The current MC produces percentile summaries but not formal confidence intervals.

**Effort estimate**: Moderate (new module or new functions in `monte_carlo.py` + report rendering + pipeline wiring).

---

### Gap D: IS Baseline Quality Gate

Current pipeline: split → backtest IS → run all stress/MC/WF regardless of baseline quality.

If the baseline IS strategy is already terrible (negative PnL, zero trades, degenerate parameters), running the full validation suite wastes compute and generates misleading "passed vacuously" results. A **pre-check gate** before step 3 would short-circuit with an early "reject" and clear diagnostics.

**Why this matters**: Efficiency and clarity. The parameter perturbation stress test already has a "no trades → vacuously passed" edge case that this gate would make explicit earlier.

**Effort estimate**: Small (validation pipeline config field + early-return logic).

---

## Candidate Comparison

| Candidate | PRD alignment | Effort | User impact | Risk |
|---|---|---|---|---|
| **A: IS/OOS Stability Checks** | Direct (§12.2, SOUL §3.3) | Small | High: catches IS/OOS divergence early | Low |
| **B: Remove Best N Trades** | Deferred (§12.3) | Small | Medium: attacks outlier-dependent strategies | Low |
| **C: MC Bootstrap + CI** | Alpha (§12.4) | Moderate | Medium: formal confidence stats | Medium |
| **D: IS Baseline Quality Gate** | Implied | Small | Medium: saves time on dead strategies | Low |

---

## Data Path Correction — OOS Metrics Must Reach Elimination

### Current Pipeline Trace (`app/services/validation_pipeline_service.py`)

```
split = split_by_ratio(df, train_ratio, val_ratio, oos_ratio)
          ↓
baseline = run_backtest(strategy, split.train, ...)    ← IS only
          ↓
stress tests → MC → WF
          ↓
evaluate_elimination(baseline.metrics, elim_cfg)        ← NO oos_metrics passed
```

The pipeline **already** holds `split.oos` (the OOS segment) but **never backtests it** and **never passes OOS metrics** to `evaluate_elimination()`. The existing `oos_metrics` parameter on `evaluate_elimination()` works correctly when called — it is simply never called with OOS data.

### Elimination Side (`validation_engine/elimination.py`)

`evaluate_elimination(metrics, config, *, oos_metrics=None, ...)` already accepts `oos_metrics` and checks two OOS fields:
- `min_oos_total_pnl` (uses `oos_metrics["total_pnl"]`)
- `min_oos_profit_factor` (uses `oos_metrics["profit_factor"]`)

But no stability-gap rules (`max_oos_pf_degradation`, etc.) exist yet.

### Required Fix for Next Task

The next implementation task **must** include:

1. **OOS backtest in the pipeline** — one extra `run_backtest(...)` call on `split.oos`.
2. **Pass oos_metrics into elimination** — call `evaluate_elimination(..., oos_metrics=oos_baseline.metrics)`.
3. **New stability-gap rules** — config fields + compute helper + wiring in `evaluate_elimination()`.

---

## Recommendation

### Task 056B — IS/OOS Stability Gate Implementation (corrected scope)

**Rationale**:

1. **Best PRD alignment**: Directly implements §12.2 pass criteria that are currently missing.
2. **Single task is better than split**: OOS metrics plumbing alone (~5 lines) is too small for a separate task; adding stability rules in the same task is still narrow and reviewable.
3. **Highest integrity impact**: Closes the most significant gap in the "OOS is Sacred" principle (SOUL §3.3).

### Corrected Proposed Scope for Task 056B

```
Do:
- In app/services/validation_pipeline_service.py:
  - Add OOS backtest: oos_baseline = run_backtest(strategy, split.oos, ...)
    (after baseline IS backtest, before stress tests; store result for step 6)
  - Pass oos_metrics=oos_baseline.metrics to evaluate_elimination()
- In validation_engine/elimination.py:
  - Add _compute_oos_stability(oos_metrics: dict, is_metrics: dict) -> dict helper
    computing these gap ratios:
    - pf_degradation = oos_pf / is_pf (ratio; < 1.0 means degradation)
    - drawdown_ratio = oos_dd / is_dd (ratio; > 1.0 means worse)
    - avg_trade_degradation = oos_avg_trade / is_avg_trade
  - Add config fields to EliminationConfig:
    - max_oos_pf_degradation: float | None = None (ratio floor; e.g. 0.5)
    - max_oos_drawdown_ratio: float | None = None (ratio ceiling; e.g. 2.0)
    - max_oos_avg_trade_degradation: float | None = None (ratio floor; e.g. 0.5)
  - Wire new rules into evaluate_elimination(), consuming oos_metrics
- Add focused tests for each new rule (pass and fail cases)
- Update changelog and task board
- Write completion report

Do Not:
- Change backtest engine
- Add new stress tests
- Modify Monte Carlo or Walk-forward
- Modify pipeline defaults
- Add UI components
```

---

## Files Changed (projected for Task 056B)

| File | Change |
|---|---|
| `app/services/validation_pipeline_service.py` | Add OOS backtest + pass oos_metrics to elimination |
| `validation_engine/elimination.py` | New config fields + `_compute_oos_stability` helper + rule wiring |
| `tests/` | `test_elimination.py` + possibly `test_validation_pipeline_service.py` |
| `docs/changelog.md` | Entry for Task 056B |
| `docs/task_board.md` | Task 056B → Done |

---

## Triage metadata

- **Triage author**: DeepSeek V4 Pro
- **Date**: 2026-06-06 (revised 2026-06-06)
- **Dependencies**: None (standalone)
- **Blocked by**: Nothing
