# Task 051A — GP MTF Integration Design

## 1. Existing Flows Review

### 1.1 Existing GA MTF Integration (Task 050)
- **UI:** `GABuildPanel` provides passive controls (checkbox, timeframes string, probability spinbox). `get_mtf_config_dict()` returns primitive values.
- **Wiring:** `MainWindow._handle_run_ga` calls `get_mtf_config_dict()` and passes `allowed_timeframes` and `mtf_probability` to `GASearchConfig`.
- **Engine:** `GASearchConfig` forwards to `GAConfig`, which is consumed by `generate_strategies`. `generate_strategies` internally calls `_maybe_add_timeframe(cond, rng, config)` to randomly append `"timeframe"` to condition parameters based on `mtf_probability`.
- **State Isolation:** The resulting `Strategy` objects are distinct. Backtests run via the runner which uses `_precompute_indicators` for any condition containing a `"timeframe"` parameter.

### 1.2 Existing GP Build/Config Path
- **UI:** The same `GABuildPanel` has a `Run GP Search` button.
- **Wiring:** `MainWindow._handle_run_gp` initializes `GPSearchConfig` (with hardcoded base defaults) and spins up `GPWorker`. It currently ignores `get_mtf_config_dict()`.
- **Service:** `GPSearchConfig` translates to `GPConfig` in `app/services/gp_service.py`.
- **Engine:** `strategy_engine/gp_evolution.py` orchestrates GP. Trees are built via `generate_tree` and `_generate_random_condition` in `strategy_engine/gp.py`. Currently, `_generate_random_condition` only generates base-timeframe indicators.

## 2. Proposed Design

### 2.1 Configuration Routing
- **UI Wiring:** In `MainWindow._handle_run_gp`, read `mtf_config = self.ga_build_panel.get_mtf_config_dict()`.
- **Service Layer:** Extend `GPSearchConfig` and `GPConfig` to include:
  - `allowed_timeframes: tuple[int, ...] = field(default_factory=tuple)`
  - `mtf_probability: float = 0.0`
- **Engine Layer:** Modify `_generate_random_condition` (and callers `generate_tree`, `crossover_tree`, `mutate_tree` in `gp.py`) to accept `config: GPConfig`. 
- **Tree Generation:** Inside `_generate_random_condition`, after constructing the base `Condition`, execute logic equivalent to GA's `_maybe_add_timeframe`:
  ```python
  if config and config.mtf_probability > 0.0 and config.allowed_timeframes:
      if rng.random() < config.mtf_probability:
          cond.params["timeframe"] = rng.choice(config.allowed_timeframes)
  ```

### 2.2 Preserving Strict Isolation
- **No Shared Mutable State:** GP will maintain its own `GPConfig` instance. GA and GP do not share any global state or singleton configurations.
- **Ranked Data Immutability:** Generated GP strategies are instantiated as entirely new `Strategy` objects. They will be passed to `StrategyService.get_ranked_strategies(injected_strategies=[...])` just like GA strategies, guaranteeing no mutation of existing `ranked_data`.
- **RNG Determinism:** By consuming `rng.random()` only when `mtf_probability > 0.0` (or `len(allowed_timeframes) > 0`), we ensure that backward compatibility for base-timeframe GP runs is preserved perfectly (the RNG stream sequence remains unchanged when MTF is disabled).

### 2.3 Required File Changes for 051B (Implementation)
- `app/ui/main_window.py`: Update `_handle_run_gp` to read and forward `mtf_config`.
- `app/services/gp_service.py`: Add MTF fields to `GPSearchConfig`.
- `strategy_engine/gp_evolution.py`: Add MTF fields to `GPConfig`.
- `strategy_engine/gp.py`: Propagate `config: GPConfig` down through tree generation functions and apply MTF parameters to generated leaves.
- `tests/test_gp_core.py` and `tests/test_gp_evolution.py`: Add deterministic MTF tests.

### 2.4 Test Plan for 051B
- `test_gp_mtf_disabled_does_not_consume_rng`: Prove that when MTF is disabled, `rng.random()` is not called for timeframes, preserving legacy seeds.
- `test_gp_mtf_injection`: Prove that when `mtf_probability = 1.0`, generated tree leaves contain the `timeframe` parameter.
- `test_gp_mutation_mtf`: Prove that a structural "grow" mutation or leaf replacement applies the MTF configuration safely.
- `test_gp_build_wiring_mtf`: Spy on `GPSearchConfig` in `_handle_run_gp` to ensure the config makes it across the UI-service boundary.

## 3. Assumptions and Risks
- **Assumption:** The backtest engine is completely agnostic to whether a `timeframe` key originated from GA or GP, meaning no runner modifications are needed.
- **Risk:** Missing `config` propagation. If `crossover_tree` or `mutate_tree` forgets to pass `config` down to `_generate_random_condition`, mutations might lose the MTF capability or break determinism. Mitigated by strict typing and the test plan.
