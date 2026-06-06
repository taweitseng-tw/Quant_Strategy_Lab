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

### 6.1 ValidationSummary Widget

After the existing MC card, add a "Bootstrap MC" card when `bootstrap_monte_carlo_result` is present:

```
Bootstrap MC (200 iterations)
Total PnL: 95% CI [1,200 — 9,800] mean=5,400
Profit Factor: 95% CI [1.15 — 2.80] mean=1.95
Max Drawdown: 95% CI [500 — 12,000] mean=4,200
Stability Score: 0.85
```

Fields: `test_name`, `iterations`, `confidence_intervals` (PnL, PF, MaxDD), `stability_score`. Each CI line shows `ci_lower`, `ci_upper`, `ci_mean`.

### 6.2 Markdown Report (`_format_markdown_validation()`)

After MC line, add:

```markdown
- **Bootstrap MC** (200 iter): PnL 95% CI [1,200 — 9,800] mean=5,400
  - PF CI [1.15 — 2.80] mean=1.95
  - Max DD CI [500 — 12,000] mean=4,200
  - Stability: 0.85
```

### 6.3 HTML Report (`_format_html_validation()`)

After MC paragraph, add:

```html
<p><b>Bootstrap MC</b> (200 iter): PnL 95% CI [1,200 — 9,800] mean=5,400</p>
<div class="stress-detail">PF CI [1.15 — 2.80] mean=1.95</div>
<div class="stress-detail">Max DD CI [500 — 12,000] mean=4,200</div>
<div class="stress-detail">Stability: 0.85</div>
```

Numeric values from `confidence_intervals` dict; all other text is static. No HTML escaping needed for numeric values (all are float). `stability_score` uses existing rendering convention.

### 6.4 Implementation Surface (Future Display Task)

| File | Change |
|---|---|
| `app/widgets/validation_summary.py` | Bootstrap MC card after existing MC card |
| `reports/generator.py` | Bootstrap lines in both formatters |
| `tests/test_validation_summary.py` | Widget test |
| `tests/test_report_export.py` | Report tests |

All display implementation deferred to a separate task.

## 7. Non-Goals

- Not implemented in this design-only task.
- No pipeline/report/widget changes.
- No `worst_case_equity`.
- No UI controls for bootstrap.

## 8. Triage metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Dependencies**: 057A-Impl (engine) — Done
