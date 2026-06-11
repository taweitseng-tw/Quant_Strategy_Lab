# Elimination Rule Configuration Design and Contract - Tasks 403-408

> Design artifact only. No production code was changed.
> Generated: 2026-06-11.

## Purpose

Define the smallest safe implementation slice for elimination rule configuration in the Strategy Quality / Robustness Expansion milestone.

The existing system already has an elimination engine, a service-level config object, a passive UI widget, ranking-table wiring, and focused tests. The next implementation should extend the existing contract instead of introducing a parallel validation design.

## Current Contract

| Layer | Current component | Review result |
|---|---|---|
| Engine | `validation_engine/elimination.py` | `EliminationConfig` and `evaluate_elimination()` already support core, OOS, stability, stress, Monte Carlo, and walk-forward thresholds. |
| Strategy service | `app/services/strategy_service.py` | Owns `DEFAULT_ELIMINATION_CONFIG`, accepts primitive dict updates, converts to `EliminationConfig`, and applies elimination during ranking. |
| Ranking UI | `app/widgets/elimination_config_widget.py` plus `app/ui/main_window.py` | Widget emits primitive dicts; `MainWindow._handle_elimination_config_changed()` updates `StrategyService` and refreshes ranking. |
| Validation pipeline | `app/services/validation_pipeline_service.py` | `PipelineConfig` already accepts `elimination_config`, and `run_validation_pipeline()` evaluates it with baseline and OOS metrics. |
| Validate page wiring | `app/ui/main_window.py` | Current `PipelineConfig(...)` construction does not pass `self.strategy_service.elimination_config`. This is a real integration gap. |
| Tests | `tests/test_elimination.py`, `tests/test_elimination_config_widget.py`, `tests/test_strategy_service_elimination_config.py` | Current focused tests pass: 55 passed. |

## Existing Config Fields

`EliminationConfig` currently supports these fields:

```python
min_total_pnl: float | None
min_profit_factor: float | None
max_drawdown_pnl: float | None
min_avg_trade: float | None
min_trade_count: int | None
min_win_rate: float | None
min_oos_total_pnl: float | None
min_oos_profit_factor: float | None
max_oos_pf_degradation: float | None
max_oos_drawdown_ratio: float | None
max_oos_avg_trade_degradation: float | None
min_stress_pass_rate: float | None
min_monte_carlo_p05_pnl: float | None
min_walk_forward_pass_rate: float | None
require_optional: bool
```

Rules:

- `None` means disabled.
- A numeric value activates the rule.
- Unknown keys are ignored by `StrategyService.update_elimination_config()`.
- UI widgets should emit primitive dictionaries, not engine objects.
- Engine and service layers own validation behavior; UI must not duplicate pass/fail logic.

## Backward-Compatible Defaults

`StrategyService.DEFAULT_ELIMINATION_CONFIG` currently enables only conservative ranking filters:

```python
EliminationConfig(
    min_trade_count=5,
    min_profit_factor=0.5,
    max_drawdown_pnl=50_000.0,
    min_avg_trade=-500.0,
)
```

Implementation must preserve these defaults unless the user explicitly approves a behavior change.

## Design Gaps

| Gap | Impact | Required next action |
|---|---|---|
| Widget lacks OOS stability controls for `max_oos_pf_degradation`, `max_oos_drawdown_ratio`, and `max_oos_avg_trade_degradation`. | Users cannot configure three existing engine-supported stability gates. | Add three disabled-by-default rows to `EliminationConfigWidget`. |
| Validate page does not pass current elimination config into `PipelineConfig`. | Ranking and Validate pipeline can use different elimination thresholds. | Wire `self.strategy_service.elimination_config` into `PipelineConfig(elimination_config=...)`. |
| Widget default values duplicate service defaults. | Future drift risk. | Defer unless implementation can safely inject defaults from service without broad UI churn. |
| Existing source files contain legacy mojibake comments. | Cosmetic/readability issue, not a behavior blocker. | Do not clean broadly in the implementation slice. Avoid unrelated encoding churn. |

## Next Implementation Slice

Tasks 409-414 should make only these changes:

1. Add OOS stability rows to `EliminationConfigWidget`:
   - `max_oos_pf_degradation`
   - `max_oos_drawdown_ratio`
   - `max_oos_avg_trade_degradation`
2. Keep all three disabled by default.
3. Ensure `get_config_dict()`, `set_config_dict()`, `clear_all()`, and `apply_defaults()` handle the new rows.
4. Pass current elimination config into Validate page `PipelineConfig`.
5. Add focused tests only.

Out of scope:

- Changing elimination formulas.
- Changing default thresholds.
- Moving the widget to another page.
- Adding new metrics not already present in `EliminationConfig`.
- Broad source comment encoding cleanup.

## Test Plan

Run and extend focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_elimination_config_widget.py tests/test_elimination.py tests/test_strategy_service_elimination_config.py -q
```

Current baseline:

```text
55 passed
```

Implementation should add deterministic tests for:

1. Widget includes all three OOS stability keys.
2. OOS stability rows are disabled by default and emit `None`.
3. Enabling each OOS stability row emits the expected float value.
4. `set_config_dict()` accepts partial dictionaries with only OOS stability keys.
5. `clear_all()` disables OOS stability rows.
6. `apply_defaults()` leaves OOS stability rows disabled.
7. Validate page pipeline config passes the current `StrategyService.elimination_config`.

## Acceptance Criteria For Tasks 409-414

- Focused tests pass.
- Default behavior remains backward compatible.
- UI remains passive and emits primitive dictionaries.
- Validation logic remains in engine/service layers.
- No unrelated source encoding cleanup.
- No changelog history rewrite.
