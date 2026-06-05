# Task 050A - MTF UI Integration Design Only

Date: 2026-06-04

Status: Design only. No production code changes.

## 1. Purpose

Task 049 completed engine, generator, report, JSON, and export support for
multi-timeframe (MTF) conditions. Task 050A defines how MTF controls should be
introduced into the desktop UI without moving strategy or backtest logic into
widgets and without mutating already-ranked strategies.

The design intentionally keeps the first UI step narrow:

- Let the user opt into generating MTF strategy candidates from the Build page.
- Keep existing Results selection, JSON import, Formula Editor, and report export
  flows stable.
- Do not allow direct editing of ranked strategy objects in place.

## 2. Files Inspected

- `docs/multi_timeframe_conditions_design_049A.md`
- `app/ui/main_window.py`
- `app/widgets/ga_build_panel.py`
- `app/widgets/strategy_detail.py`
- `app/widgets/formula_condition_editor.py`
- `app/services/strategy_service.py`
- `app/services/ga_service.py`
- `strategy_engine/ga.py`
- `strategy_engine/generator.py`
- Relevant GA, GP, strategy generator, report, and JSON wiring tests.

## 3. Current UI Findings

### Build Page

The Build page currently owns `GABuildPanel`, a passive PySide6 widget with:

- `btn_run_ga`
- `btn_run_gp`
- status label
- result display cards

It does not import services or engine modules. `MainWindow` wires button clicks to
`_handle_run_ga()` and `_handle_run_gp()`.

### Results Page

The Results page shows ranked strategies and details through:

- `RankingTable`
- `StrategyDetailWidget`
- `EquityCurveChart`
- `TradeListWidget`
- `ParameterHeatmapWidget`
- export controls
- elimination config widget

The Results page already supports safe create-copy behavior for Formula Editor
custom conditions. It should not be the first home for MTF generation controls,
because MTF is primarily a candidate-generation option, not a post-ranking edit.

### StrategyDetailWidget

`StrategyDetailWidget` is passive. It displays selected strategy information and
emits `add_custom_condition_requested` for Formula Editor integration.

It should display MTF tags in a future polish step, but it should not own MTF
generation settings or mutate strategies.

### Generator and Service Layer

`strategy_engine.generator.generate_strategies()` already accepts:

- `allowed_timeframes: tuple[int, ...] = ()`
- `mtf_probability: float = 0.0`

The defaults keep MTF disabled and preserve existing behavior.

`StrategyService.get_ranked_strategies()` still calls `generate_strategies()`
without MTF controls. `GASearchConfig` and `GAConfig` also do not yet expose MTF
fields, so GA initial population cannot yet opt into MTF from the UI.

## 4. Recommended MVP Placement

Recommended placement: **Build page, inside `GABuildPanel`, as a passive
"Multi-timeframe generation" options row.**

Do not place first MTF controls in:

- Results detail tool: too easy to imply direct mutation of ranked strategies.
- Data page: data page owns import/visualization, not generation policy.
- Modal dialog from Results: better suited for Formula Editor create-copy actions,
  not global generator configuration.
- Validate page: validation consumes strategies, it should not generate them.

## 5. Proposed Passive Widget Behavior

Add UI controls to `GABuildPanel` in a future implementation task:

- `QCheckBox` named conceptually `chk_enable_mtf`
  - Label: `Enable MTF candidates`
  - Default: unchecked
  - Tooltip: "Adds higher-timeframe conditions to generated strategies. Slower
    and requires enough data for higher-timeframe warmup."
- `QLineEdit` or compact token input named conceptually `le_allowed_timeframes`
  - Default text: `5,15`
  - Disabled when checkbox is unchecked
  - Accepts comma-separated positive integer minute values.
- `QDoubleSpinBox` named conceptually `spin_mtf_probability`
  - Range: `0.0` to `1.0`
  - Step: `0.05`
  - Default: `0.25`
  - Disabled when checkbox is unchecked

The widget should expose a primitive method:

```python
def get_mtf_config_dict(self) -> dict:
    return {
        "enabled": bool,
        "allowed_timeframes": list[int],
        "mtf_probability": float,
    }
```

The widget must not import:

- `strategy_engine`
- `backtest_engine`
- `validation_engine`
- `app.services`

Validation inside the widget should be shallow UI validation only:

- Parse comma-separated integers.
- Reject empty values when enabled.
- Reject bool-like/non-integer/zero/negative values.
- Return a primitive error state or disable the Run buttons.

The authoritative generator validation remains in `strategy_engine.generator`.
Runner compatibility with actual base timeframe remains in `backtest_engine.runner`.

## 6. Data Flow

Future implementation should use this flow:

```text
GABuildPanel passive controls
  -> MainWindow._handle_run_ga()
  -> GASearchConfig(...)
  -> ga_service.run_ga_search()
  -> GAConfig(...)
  -> strategy_engine.ga.create_initial_population()
  -> strategy_engine.generator.generate_strategies(...)
  -> run_backtest(...)
  -> Results ranking refresh
```

For mock/default Results generation:

```text
StrategyService.get_ranked_strategies()
  -> generate_strategies(count=10, seed=42)
```

This path should remain base-only by default. The first MVP MTF UI should affect
GA search from the Build page, not the default Results fallback list.

## 7. Required Service / Engine Config Extension

Future Task 050B should extend, in order:

1. `strategy_engine.ga.GAConfig`
   - add `allowed_timeframes: tuple[int, ...] = ()`
   - add `mtf_probability: float = 0.0`
   - pass these fields into `generate_strategies()` inside
     `create_initial_population()`

2. `app.services.ga_service.GASearchConfig`
   - add matching primitive fields
   - pass them through `to_ga_config()`
   - include them in `to_dict()` automatically via dataclass serialization

3. `app.ui.main_window.MainWindow._handle_run_ga()`
   - read passive config from `GABuildPanel`
   - construct `GASearchConfig(..., allowed_timeframes=..., mtf_probability=...)`
   - do not parse or mutate strategy conditions in MainWindow

## 8. Why Not Results-Page Mutation?

Ranked strategies are outputs of a run. Directly changing their condition params
would make the metrics, equity curve, trade list, and provenance stale until the
strategy is re-run. That creates a high risk of UI inconsistency.

Therefore:

- MTF generation settings should create new candidate strategies through the
  generator path.
- Manual condition edits should continue to use the existing create-copy pattern.
- Existing ranked entries must not be mutated in place.

## 9. Strategy Detail Display

Future UI polish may update `StrategyDetailWidget._format_condition()` to render
MTF params as a clearer label:

```text
close > SMA(period=20) [TF: 15m]
```

This is display-only. It must not parse or evaluate MTF logic.

Recommended follow-up task: include this display polish in 050B or 050C only if
it can be done without changing Results selection behavior.

## 10. Formula Editor Scope

Formula parser MTF syntax remains deferred.

Do not add syntax like:

```text
close > SMA(20, tf=15)
```

until a separate parser design and safety review is completed. The current Formula
Editor is already safe and accepted; do not expand grammar casually inside the UI
wiring task.

## 11. Data Page Scope

The Data page should not grow MTF generation controls in the MVP.

Potential future Data page MTF work:

- show base timeframe inference
- show available resample targets
- warn when data is too short for selected higher timeframes

For 050, keep Data page read-only with respect to MTF controls.

## 12. UX Rules

The UI should communicate three facts clearly:

1. MTF candidates are optional and off by default.
2. MTF can be slower because each higher timeframe requires resampling and
   precompute.
3. MTF needs enough data for higher-timeframe indicator warmup; early bars may
   evaluate false.

Suggested tooltip text:

```text
Adds higher-timeframe conditions to generated strategies. Off by default.
Requires enough data for higher-timeframe warmup and may run slower.
```

## 13. Future Test Plan

### Widget Tests

- `test_ga_build_panel_mtf_controls_default_disabled`
- `test_ga_build_panel_mtf_controls_enable_disable_state`
- `test_ga_build_panel_get_mtf_config_disabled_returns_empty`
- `test_ga_build_panel_get_mtf_config_parses_timeframes`
- `test_ga_build_panel_rejects_invalid_timeframes`
- `test_ga_build_panel_has_no_engine_or_service_imports`

### Service Config Tests

- `test_ga_search_config_defaults_mtf_disabled`
- `test_ga_search_config_to_ga_config_passes_mtf_fields`
- `test_ga_search_config_snapshot_includes_mtf_fields`
- `test_create_initial_population_passes_mtf_to_generator`
- `test_ga_mtf_disabled_preserves_existing_population_behavior`

### MainWindow Wiring Tests

- `test_main_window_ga_mtf_unchecked_uses_defaults`
- `test_main_window_ga_mtf_checked_passes_allowed_timeframes`
- `test_main_window_ga_mtf_checked_passes_probability`
- `test_main_window_does_not_import_generator_or_runner_for_mtf_ui`
- `test_mtf_ui_does_not_mutate_ranked_data`

### Integration Tests

- `test_ga_search_with_mtf_config_produces_backtestable_result`
- `test_ga_best_mtf_strategy_appears_in_results_ranking`
- `test_mtf_generated_strategy_report_export_safe`

## 14. Acceptance Criteria for Future Implementation

1. MTF UI controls are off by default.
2. Passive widget returns primitive config only.
3. Widget imports no engine or service modules.
4. MainWindow routes config through service dataclasses, not direct generator calls.
5. GA initial population can receive MTF generator config.
6. Existing GA/GP buttons still work.
7. Existing Results selection behavior remains unchanged.
8. Ranked strategies are never mutated in place.
9. Full suite passes.
10. App launches cleanly.

## 15. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Users choose timeframes incompatible with loaded data | Medium | Let runner raise clear validation error; later add Data page hints |
| MTF settings silently affect default Results fallback | Medium | Scope first UI to GA Build only |
| UI widget becomes too smart | Medium | Passive widget, primitive dict only, no services/engines |
| GA mutation/crossover may not preserve or mutate timeframe policy intentionally | Low | MTF is attached in initial generation; later review mutation behavior separately |
| Too much UI clutter in Build panel | Low | Use compact row or collapsible "Advanced generation" section |

## 16. Deferred Items

- Formula parser MTF syntax.
- Data page available-timeframe hints.
- Manual create-copy MTF condition editor.
- NinjaTrader real MTF export.
- GP-specific MTF controls.
- Explicit base timeframe selector.

## 17. Recommended Next Task

Task 050B - MTF GA Config and Passive UI Controls Implementation.

Suggested implementation order:

1. Extend `GAConfig` and `GASearchConfig`.
2. Pass MTF fields through `create_initial_population()`.
3. Add passive MTF controls to `GABuildPanel`.
4. Wire `MainWindow._handle_run_ga()` to read the passive config.
5. Add focused tests before running the full suite.

## 18. Mandatory Checklist

| Question | Answer |
|----------|--------|
| Did this design keep widgets passive? | Yes |
| Did this design avoid mutating ranked strategies? | Yes |
| Did this design avoid Results-page first wiring? | Yes |
| Did this design define safe data flow through service/config objects? | Yes |
| Did this design avoid formula parser grammar expansion? | Yes |
| Did this design avoid production code changes? | Yes |
