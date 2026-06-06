# Task 056B — IS/OOS Stability Gate Implementation

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### 1. IS/OOS Stability Rules (`validation_engine/elimination.py`)

- Added `_compute_oos_stability(oos_metrics: dict, is_metrics: dict) -> dict` helper that computes three stability ratios:
  - `pf_degradation` = OOS PF / IS PF (fraction of PF retained OOS)
  - `drawdown_ratio` = OOS DD / IS DD (how many × larger OOS drawdown is)
  - `avg_trade_degradation` = OOS avg trade / IS avg trade (fraction retained OOS)
  - Returns `None` for each when the IS baseline is non-positive (guard against division-by-zero).

- Added 3 optional fields to `EliminationConfig`:
  - `max_oos_pf_degradation: float | None = None` — e.g. 0.5 means OOS PF must be ≥50% of IS PF.
  - `max_oos_drawdown_ratio: float | None = None` — e.g. 2.0 means OOS DD must be ≤2× IS DD.
  - `max_oos_avg_trade_degradation: float | None = None` — e.g. 0.5 means OOS avg trade ≥50% of IS avg trade.
  - All default to `None` (disabled) → fully backward-compatible.

- Wired rules into `evaluate_elimination()`:
  - Only fire when `oos_metrics` is provided AND the config threshold is set.
  - Missing OOS data with thresholds set → warning (default) or fail (`require_optional=True`).

### 2. OOS Metrics Plumbing (`app/services/validation_pipeline_service.py`)

- Added **step 2.5**: OOS backtest on `split.oos` when the segment exists and has rows.
  ```python
  oos_baseline = run_backtest(strategy, split.oos, instrument=instrument, **backtest_kwargs)
  ```
- Passes `oos_metrics=oos_baseline.metrics` into `evaluate_elimination()`.
- Added `oos_metrics: dict | None` field to `PipelineResult` dataclass for UI/report inspection.
- Graceful handling: empty/None OOS segment produces a warning, no crash.
- Default `PipelineConfig` has no stability thresholds → the new pipeline behavior is benign by default.

### 3. Focused Tests

**`tests/test_elimination.py`** — 13 new tests:
- `test_stability_pf_degradation_passes` / `test_stability_pf_degradation_fails`
- `test_stability_drawdown_ratio_passes` / `test_stability_drawdown_ratio_fails`
- `test_stability_avg_trade_degradation_passes` / `test_stability_avg_trade_degradation_fails`
- `test_stability_all_three_pass` — combined pass
- `test_stability_metrics_missing_warns_by_default` — no OOS → warn
- `test_stability_metrics_missing_fails_when_required` — require_optional → fail
- `test_stability_thresholds_none_by_default` — default None
- `test_stability_all_none_skips_rules` — all None → rules skipped

**`tests/test_validation_pipeline_service.py`** — 4 new tests:
- `test_pipeline_includes_oos_metrics` — result has OOS metrics dict
- `test_pipeline_oos_metrics_passed_to_elimination` — no OOS warnings in elimination
- `test_pipeline_oos_metrics_stability_default_skipped` — default config safe
- `test_pipeline_oos_metrics_empty_segment_warning` — empty OOS → warning, no crash

**`tests/test_strategy_service_elimination_config.py`** — 1 fix:
- Updated expected_keys set to include 3 new stability fields.

## Files Changed

| File | Change |
|---|---|
| `validation_engine/elimination.py` | Added `_compute_oos_stability` helper, 3 config fields, stability rule wiring |
| `app/services/validation_pipeline_service.py` | Added OOS backtest (step 2.5), `oos_metrics` pass-through, `PipelineResult.oos_metrics` |
| `tests/test_elimination.py` | 13 new stability rule tests |
| `tests/test_validation_pipeline_service.py` | 4 new OOS data path tests |
| `tests/test_strategy_service_elimination_config.py` | Updated expected_keys for 3 new fields |
| `docs/changelog.md` | Added Task 056B entry |
| `docs/task_board.md` | Task 056B → Done |
| `docs/agent_reports/2026-06-06_task-056b_is-oos-stability-gate_deepseek.md` | **Created** — this report |

## Verification

```
.venv\Scripts\python.exe -m pytest tests/test_elimination.py tests/test_validation_pipeline_service.py -v
→ 47 passed

.venv\Scripts\python.exe -m pytest -q (--ignore=tests/test_ga_build_wiring.py)
→ 964 passed, 1 pre-existing warning

git diff --check → passes (no trailing whitespace)
```

## Known Issues

- None.

## Risks

- None. All new rules are opt-in (default `None`) and backward-compatible.
- The pre-existing Qt segfault in `test_ga_build_wiring.py` is unrelated to this task.

## Suggested Next Task

With the IS/OOS stability gate now implemented and the OOS metrics flowing through the pipeline, the natural next step would be **report/UI visualization of OOS stability**. The `PipelineResult.oos_metrics` field now exposes this data for Validate page dashboards and Markdown/HTML reports. Alternatively, a task to add the "Remove Best N Trades" stress test (Gap B from the 056A triage) would be a small, complementary addition.
