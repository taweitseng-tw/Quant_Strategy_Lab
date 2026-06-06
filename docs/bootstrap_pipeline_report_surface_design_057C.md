# Bootstrap Pipeline and Report Surface Design — Task 057C

> Design-only. No production code changed.

## 1. Current State

`run_bootstrap_monte_carlo()` produces `MonteCarloResult` with `confidence_intervals`. It is engine-only with no pipeline wiring, no display, and no report integration.

## 2. PipelineConfig Additions

```python
# In PipelineConfig:
run_bootstrap_monte_carlo: bool = False        # default off
bootstrap_iterations: int = 200
bootstrap_confidence_level: float = 0.95
```

All default off. Bootstrap is heavier than existing MC (200 iterations); user must opt in.

## 3. PipelineResult Field

```python
# In PipelineResult:
bootstrap_monte_carlo_result: dict | None = None
```

Serialized from `MonteCarloResult` via a new `_bootstrap_mc_to_dict()` helper (or extended `_mc_to_dict()`).

## 4. Serialization Strategy

New helper `_bootstrap_mc_to_dict()` in `validation_pipeline_service.py`:

```python
def _bootstrap_mc_to_dict(mc) -> dict | None:
    if mc is None:
        return None
    return {
        "test_name": mc.test_name,
        "iterations": mc.iterations,
        "percentile_summary": mc.percentile_summary,
        "worst_case": mc.worst_case,
        "confidence_intervals": mc.confidence_intervals,
        "assumptions": mc.assumptions,
        "stability_score": mc.stability_score,
    }
```

## 5. Pipeline Wiring

In `run_validation_pipeline()`, after existing MC (step 4):

```python
if cfg.run_bootstrap_monte_carlo:
    bootstrap = run_bootstrap_monte_carlo(
        baseline,
        iterations=cfg.bootstrap_iterations,
        base_seed=cfg.mc_base_seed,
        confidence_level=cfg.bootstrap_confidence_level,
    )
    result.bootstrap_monte_carlo_result = _bootstrap_mc_to_dict(bootstrap)
```

## 6. Display (Widget + Reports) — Deferred After Pipeline

- **Widget**: Add a "Bootstrap MC" card after existing MC card, showing CI values.
- **Markdown/HTML**: Add CI lines in validation evidence section.

Exact format TBD in a follow-up display task.

## 7. Non-Goals

- Not implemented in this design-only task.
- No pipeline/report/widget changes.
- No `worst_case_equity`.
- No UI controls for bootstrap.

## 8. Triage metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Dependencies**: 057A-Impl (engine) — Done
