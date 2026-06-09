# Price-Noise Widget Display Design - Task 062M

> Design-only. No production code changed.

## 1. Current State

Price-noise stress results (`test_name="price_noise"`) are serialized in the pipeline output but are not yet displayed with dedicated detail lines in the `ValidationSummary` widget.

## 2. Widget Display

In `app/widgets/validation_summary.py`, in the stress section, add price-noise detail lines after the main stress line when `test_name == "price_noise"`.

Expected text shape:

```text
price_noise: OK PnL d=-5.2%
  - Noise: 0.5%, Iterations: 50, Method: ohlc_preserving_gaussian_noise, Research only: True
  - WARNING: Price-noise stress test is an approximate robustness diagnostic. It does not prove live-trading robustness.
```

## 3. Visibility Rules

| Condition | Widget displays price-noise detail? |
|---|---|
| `run_price_noise_stress=False` and no `price_noise` stress result exists | No |
| Stress result with `test_name="price_noise"` exists | Yes |

## 4. Focused Tests

| # | Test | File |
|---|---|---|
| 1 | Widget shows price-noise detail when opt-in | `test_validation_summary.py` |
| 2 | Widget omits price-noise detail when default | `test_validation_summary.py` |
| 3 | Widget shows noise_pct, iterations, method, and research_only | `test_validation_summary.py` |
| 4 | Widget shows price-noise warnings | `test_validation_summary.py` |

## 5. Next Batch

Batch 062N-Impl - Price-Noise Widget Display Implementation.

## 6. Metadata

- Author: DeepSeek V4
- Date: 2026-06-08
