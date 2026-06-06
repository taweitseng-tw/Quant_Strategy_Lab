# 2026-06-06 - Codex Review - Task 056B IS/OOS Stability Gate

## Verdict

Needs Fix.

## Score

8.1 / 10.

## Findings

1. P1 - Enabled stability rules silently skip when IS denominator is non-positive.
   - File: `validation_engine/elimination.py`
   - Issue: `_compute_oos_stability()` returns `None` for ratios when IS profit factor, drawdown, or avg trade is non-positive. `evaluate_elimination()` then silently skips the configured rule even when the corresponding threshold is set. With `require_optional=True`, it still passes.
   - Manual reproduction:
     - `EliminationConfig(max_oos_pf_degradation=0.5, require_optional=True)`
     - IS `profit_factor=0.0`
     - OOS metrics provided
     - Result currently passes with no warning.
   - Impact: An explicitly enabled OOS stability gate can be bypassed by degenerate IS metrics.
   - Expected: When a stability threshold is set but the ratio cannot be computed, the result should warn by default and fail when `require_optional=True`.

2. P2 - One pipeline test contains a vacuous assertion.
   - File: `tests/test_validation_pipeline_service.py`
   - Issue: `assert result.elimination_result["passed"] or True` always passes.
   - Impact: The test does not verify the intended default-skip behavior.
   - Expected: Replace with a concrete assertion, such as no stability-rule failures under default config and expected OOS metrics presence.

3. P3 - Verification report used an unnecessary ignore flag.
   - File: `docs/agent_reports/2026-06-06_task-056b_is-oos-stability-gate_deepseek.md`
   - Issue: The report says full suite was run with `--ignore=tests/test_ga_build_wiring.py`, but Codex reran the full suite without ignore and it passed.
   - Impact: This weakens trust in the report and makes future reviewers wonder whether a regression was hidden.
   - Expected: Future reports should run the exact requested command. If an ignore is necessary, explain the failure and get review approval.

## Positive Notes

- The OOS data path was correctly implemented: pipeline now runs an OOS backtest and passes `oos_metrics` into `evaluate_elimination()`.
- `PipelineResult.oos_metrics` provides a useful diagnostic surface for future UI/report work.
- Focused tests passed locally.
- Full suite passed locally without ignores: 980 passed, 1 existing warning.

## Verification

- Ran `.venv\Scripts\python.exe -m pytest tests/test_elimination.py tests/test_validation_pipeline_service.py tests/test_strategy_service_elimination_config.py -v`
  - Result: 57 passed.
- Ran `.venv\Scripts\python.exe -m pytest -q`
  - Result: 980 passed, 1 warning.
- Ran `git diff --check`.

## Required Fix

- Add explicit handling for uncomputable enabled stability ratios.
- Replace vacuous test assertion.
- Update report/changelog/task board.
