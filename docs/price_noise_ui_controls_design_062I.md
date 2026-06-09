# Price-Noise UI Config Controls Design — Task 062I

> Design-only. No production code changed.

## 1. Target File

`app/ui/main_window.py` — Validate page, after existing stress test controls (remove-best-N group).

## 2. Controls

```
☐ Price-Noise Stress
  Noise fraction: [0.005]   Iterations: [50]   Seed: [42]
```

| Control | Type | Default | Range | Tooltip |
|---|---|---|---|---|
| Enable checkbox | `QCheckBox` | Unchecked | — | "Adds Gaussian noise to OHLC prices. Helps detect overfit strategies. Off by default." |
| Noise fraction | `QDoubleSpinBox` | 0.005 | 0.001–0.05, step 0.001, decimals 3 | "Standard deviation of Gaussian noise as fraction of price; 0.005 = 0.5%." |
| Iterations | `QSpinBox` | 50 | 10–500, step 10 | "Number of noise-sampled backtests." |
| Seed | `QSpinBox` | 42 | 1–9999 | "Deterministic seed for reproducibility." |

## 3. PipelineConfig Mapping

```python
config = PipelineConfig(
    ...
    run_price_noise_stress=self.price_noise_checkbox.isChecked(),
    price_noise_pct=self.price_noise_pct_spin.value(),
    price_noise_iterations=self.price_noise_iter_spin.value(),
    price_noise_seed=self.price_noise_seed_spin.value(),
)
```

## 4. Focused Tests (Future)

| # | Test |
|---|---|
| 1 | Controls exist with correct defaults |
| 2 | Spinboxes disabled when unchecked |
| 3 | Spinboxes enabled when checked |
| 4 | Unchecked passes `run_price_noise_stress=False` |
| 5 | Checked with custom values passes config fields |

## 5. Out of Scope

- Report rendering of price-noise results (deferred).
- Price-noise UI controls for the Run page (same as Validate).

## 6. Next Two-Task Batch

**Batch 062J-Impl + 062K-Design — Price-Noise UI Controls Implementation + Report Price-Noise Display Design.**

## 7. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-08
