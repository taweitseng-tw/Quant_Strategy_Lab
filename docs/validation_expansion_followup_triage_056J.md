# Validation Expansion Follow-Up Triage — Task 056J

> Design-only. No production code changed.

## 1. Current Validation Coverage (After 056 Series)

### Full Suite: 1024 passed, 1 pre-existing warning

| Category | Capability | Status | Task |
|---|---|---|---|
| **Split** | IS/Val/OOS by ratio | Done | 013 |
| **Baseline** | IS backtest | Done | 005 |
| **OOS** | OOS backtest + metrics in pipeline | Done | 056B |
| **Stress** | Commission 2x | Done | 014 |
| | Slippage 2x | Done | 014 |
| | One-bar execution delay | Done | 053F |
| | Parameter perturbation | Done | 053H |
| | **Remove best N trades** | Done | 056E-Impl |
| **Monte Carlo** | Missed-trade simulation | Done | 015 |
| | Slippage perturbation | Done | 042B2 |
| | Combined missed + slippage | Done | 042B2 |
| **Walk-forward** | Fixed window | Done | 016 |
| | Walk-forward matrix | Done | 030A |
| | WFE (Walk-Forward Efficiency) | Done | 044B |
| **Elimination** | Core thresholds (PnL, PF, DD, trades, win rate) | Done | 017 |
| | OOS thresholds (PnL, PF) | Done | — |
| | **IS/OOS stability ratios** (PF deg, DD ratio, avg trade deg) | Done | 056B |
| | Stress pass rate | Done | — |
| | Monte Carlo p05 | Done | — |
| | Walk-forward pass rate | Done | — |
| **Display** | ValidationSummary widget | Done | 026 |
| | Markdown/HTML report validation section | Done | 027 |
| | OOS metrics display | Done | 056D |
| | Stress result detail sub-lines | Done | 056G-Impl |
| **Config** | WFE checkbox | Done | 044E |
| | Remove-best-N controls | Done | 056H-Impl |

## 2. Remaining Validation Gaps

### Gap A: IS Baseline Quality Gate (Recommended)

Current pipeline: split -> backtest IS -> run ALL stress/MC/WF regardless of baseline quality.

If IS baseline is already terrible (zero trades, negative PnL), running the full suite wastes compute and generates misleading "passed vacuously" results at individual stress-test level. A pre-check gate before step 3 would short-circuit with an early-reject marker.

- **Rationale**: Operational efficiency. The pipeline already handles zero-trade edge cases in individual stress tests (parameter perturbation, remove-best-N), but each test independently re-checks. Consolidating at the pipeline entry avoids redundant work and makes early-rejection explicit.
- **Current mitigation**: None at pipeline level. Individual stress tests handle zero-trade vacuously.

### Gap B: Monte Carlo Bootstrap + Confidence Intervals

PRD Section 12.4 (Alpha) specifies bootstrap sampling, confidence intervals, and worst-case equity curve. Current MC does per-iteration random missed-trade and slippage perturbation, but does not resample trade sequences with replacement, compute formal 95% confidence intervals, or produce a worst-case equity curve projection.

- **PRD reference**: Section 12.4 — "Bootstrap sampling. Multiple simulation confidence intervals. 95% worst-case equity curve."
- **Scope risk**: Moderate engineering with statistical nuance. Bootstrap on trade sequences needs careful handling of time-series dependency assumptions.

### Gap C: Walk-Forward Per-Window Equity Curves

Walk-forward produces aggregate metrics and pass rates, but does not store per-window equity curves. This prevents per-window drawdown visualization and makes it hard to debug why a specific window failed.

- **PRD reference**: Section 12.5 (Alpha) — "Walk-forward results table. Walk-forward charts."
- **Risk**: Adds memory/disk overhead; requires model/schema changes to `WalkForwardResult`.

## 3. Candidate Comparison (Top 3)

| Candidate | Effort | Files | Risk | User impact |
|---|---|---|---|---|
| **A: IS Baseline Quality Gate** | Small | 2 (pipeline + tests) | Low | High — saves compute on dead strategies |
| **B: MC Bootstrap + CI** | Moderate | 3-4 (engine + tests + report) | Medium | Medium — formal confidence metrics |
| **C: WF Per-Window Equity** | Moderate | 3-4 (engine + model + tests + report) | Medium | Medium — debugging/visualization |

## 4. Recommendation: Candidate A — IS Baseline Quality Gate

### Rationale

1. **Smallest scope** — pipeline config field + early-return metadata. Only 2 files.
2. **Highest ROI** — every validation run benefits from skipping dead strategies.
3. **Lowest risk** — no engine changes, no new math, no schema changes.
4. **Complements recent work** — individual stress tests already handle zero-trade edge cases. This consolidates the check at pipeline entry.
5. **Clear acceptance criteria** — "zero-trade strategies skip stress/MC/WF with explicit metadata," "user-visible report/log shows the skip reason."

### Short-Circuit Visibility (Required for Acceptance)

To prevent users from mistaking skipped validation for passing validation:

1. `PipelineResult` gains a `precheck_failed: bool` field (default `False`).
2. When precheck triggers, `PipelineResult` is returned early with:
   - `stress_results = []`
   - `monte_carlo_summary = None`
   - `walk_forward_summary = None`
   - `precheck_failed = True`
   - `warnings` includes "Validation precheck failed: strategy has zero trades."
3. ValidationSummary widget already handles `No stress results.` display.
4. Log panel prints `"Validation precheck failed: strategy has zero trades — stress/MC/WF skipped."`
5. Report generator already handles `No validation evidence` placeholder for missing sections.

### Proposed Scope (Task 056J-Impl)

```
Do:
- Add PipelineConfig field: is_baseline_quality_precheck: bool = False (opt-in)
- When enabled, after baseline IS backtest:
  - total_trades == 0 -> early return with precheck_failed=True + warning
  - total_pnl <= 0 -> same (separate configurable flag, conservative: off by default)
- Add precheck_failed: bool = False to PipelineResult
- Add 3 focused pipeline tests (disabled, enabled with trades, enabled without trades)
- Verify widget/report handle missing stress/MC/WF sections
- Update changelog + task_board

Do Not:
- Change engine, elimination rules, report format, UI, or existing stress tests
- Force the check on by default
- Change how individual stress tests handle zero trades
```

### Why NOT B or C?

- B requires statistical design decisions best made with user input. Not a "small next step."
- C requires model/schema changes and architecture-level review. Defer to dedicated design task.

## 5. Triage metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Dependencies**: 056-series (stress engine + pipeline + display + config) — Done
- **Blocked by**: Nothing
