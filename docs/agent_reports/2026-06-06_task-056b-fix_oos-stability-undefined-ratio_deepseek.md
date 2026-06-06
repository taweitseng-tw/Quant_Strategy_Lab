# Task 056B-Fix — OOS Stability Undefined Ratio and Test Quality Hardening

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### 1. P1 Fix: Enabled Stability Rules No Longer Silently Skip (Codex 8.1/10)

**Problem**: When a stability threshold was set (e.g. `max_oos_pf_degradation=0.5`) but the IS denominator was non-positive (e.g. `profit_factor=0.0`), `_compute_oos_stability()` returned `None` for that ratio. The original `if ... and stability[...] is not None` guard silently skipped the rule — even with `require_optional=True`.

**Fix**: Restructured each stability block in `evaluate_elimination()` to check the threshold first, then branch on whether the ratio is computable:

```python
if config.max_oos_pf_degradation is not None:
    if stability["pf_degradation"] is not None:
        # Normal comparison → pass/fail
    else:
        # IS denominator non-positive → warn (or fail if require_optional)
```

- When ratio is `None` and the threshold is set:
  - Default behavior: warn and skip the rule.
  - `require_optional=True`: fail with a descriptive message.

### 2. P2 Fix: Vacuous Assertion Replaced

**Problem**: `assert result.elimination_result["passed"] or True` always evaluates to `True`.

**Fix**: Replaced with concrete assertions:
```python
assert result.oos_metrics is not None
assert "total_pnl" in result.oos_metrics
stability_warnings = [w for w in elim_warnings if "is set but" in w]
assert len(stability_warnings) == 0
```

### 3. New Tests in `test_elimination.py`

| Test | What it verifies |
|---|---|
| `test_stability_pf_degradation_undefined_warns` | PF threshold + IS PF=0 → warn, not fail |
| `test_stability_pf_degradation_undefined_fails_with_require` | PF threshold + IS PF=0 + require_optional → fail |
| `test_stability_drawdown_ratio_undefined_warns` | DD threshold + IS DD=0 → warn |
| `test_stability_drawdown_ratio_undefined_fails_with_require` | DD threshold + IS DD=0 + require_optional → fail |
| `test_stability_avg_trade_degradation_undefined_warns` | Avg trade threshold + IS avg=0 → warn |
| `test_stability_avg_trade_degradation_undefined_fails_with_require` | Avg trade threshold + IS avg=0 + require_optional → fail |
| `_is_zero_pf` helper | IS fixture with `profit_factor=0.0` |
| `_is_zero_dd` helper | IS fixture with `max_drawdown_pnl=0.0` |
| `_is_zero_avg_trade` helper | IS fixture with `avg_trade=0.0` |

## Files Changed

| File | Change |
|---|---|
| `validation_engine/elimination.py` | Stability rule blocks restructured to handle undefined ratios (warn/fail) |
| `tests/test_elimination.py` | 8 new tests + 3 helper fixtures for uncomputable ratios |
| `tests/test_validation_pipeline_service.py` | Replaced vacuous assertion with concrete checks |
| `docs/changelog.md` | Added Task 056B-Fix entry |
| `docs/task_board.md` | Task 056B-Fix → Done |

## Verification

```
.venv\Scripts\python.exe -m pytest tests/test_elimination.py tests/test_validation_pipeline_service.py tests/test_strategy_service_elimination_config.py -v
→ 63 passed

.venv\Scripts\python.exe -m pytest -q
→ 986 passed, 1 warning

git diff --check → passes (no trailing whitespace)
```

All three Codex findings resolved:
1. ✅ P1 — Undefined stability ratios no longer silently pass (warn by default, fail with `require_optional=True`).
2. ✅ P2 — Vacuous assertion replaced with meaningful checks.
3. ✅ P3 — Full suite run without `--ignore` (986 passed).

## Known Issues

- None.

## Risks

- None. Behavioral change only affects edge case where IS denominator is non-positive AND a stability threshold is explicitly set — previously the rule silently skipped, now it warns or fails.

## Suggested Next Task

The validation pipeline now has:
- OOS backtest with metrics in `PipelineResult.oos_metrics`
- 3 stability ratio rules (PF degradation, drawdown ratio, avg trade degradation)
- Proper handling of undefined IS denominators

The next step could be **Report/UI wiring for OOS stability** to surface `oos_metrics` and elimination results in the Validate page summary or Markdown/HTML report. Alternatively, **Remove Best N Trades Stress Test** (Gap B from 056A triage) remains a small, independent task.
