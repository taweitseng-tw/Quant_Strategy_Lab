# Report Price-Noise Display Design - Task 062K

> Design-only. No production code changed.

## 1. Current State

Price-noise stress results are serialized in `stress_results` as a dict with `test_name="price_noise"`. They should be displayed in Markdown and HTML reports only when the result exists.

## 2. Markdown Display

In `reports/generator.py`, after the existing stress test line, add price-noise detail and warning sub-lines:

```markdown
- **Stress (price_noise)**: OK PnL d=-5.2%
  - noise_pct=0.5%, iterations=50, method=ohlc_preserving_gaussian_noise, research_only=True
  - WARNING: Price-noise stress test is an approximate robustness diagnostic. It does not prove live-trading robustness.
```

## 3. HTML Display

After the existing stress test line:

```html
<p><b>Stress (price_noise):</b> PnL d=-5.2%</p>
<div class="stress-detail">noise_pct=0.5%, iterations=50, method=ohlc_preserving_gaussian_noise, research_only=True</div>
<div class="warning-item">Price-noise stress test is an approximate robustness diagnostic. It does not prove live-trading robustness.</div>
```

All dynamic detail and warning values must be HTML-escaped.

## 4. Visibility Rules

| Condition | Report displays price-noise? |
|---|---|
| `run_price_noise_stress=False` (default) | No |
| Stress result `test_name` != "price_noise" | No |
| Stress result exists with `test_name="price_noise"` | Yes |

## 5. Focused Tests

| # | Test | File |
|---|---|---|
| 1 | Markdown includes price-noise when opt-in | `test_report_export.py` |
| 2 | Markdown omits price-noise when default | `test_report_export.py` |
| 3 | HTML includes price-noise when opt-in | `test_report_export.py` |
| 4 | HTML omits price-noise when default | `test_report_export.py` |
| 5 | HTML escapes price-noise assumptions and warnings | `test_report_export.py` |

## 6. Next Batch

Batch 062L-Impl - Report Price-Noise Display plus Price-Noise Widget Display design.

## 7. Metadata

- Author: DeepSeek V4
- Date: 2026-06-08
