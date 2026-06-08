# Price-Noise Stress Test Contract - Task 062B

> Design-only. No production code changed.

## 1. Purpose

Define a stress test that adds controlled price noise to OHLCV data and re-runs
the backtest, measuring whether a strategy is overly sensitive to small data
perturbations. This is a research diagnostic only. It does not prove live
trading robustness.

## 2. Input Data Shape

| Element | Source |
|---|---|
| OHLCV DataFrame | Existing in-memory DataFrame used by the validation pipeline |
| Strategy | `Strategy` object |
| Instrument profile | `InstrumentProfile`, passed through to `run_backtest` when available |
| Execution config | Existing commission, slippage, and execution assumptions |

Required OHLCV columns:

```text
open, high, low, close, volume
```

## 3. Price Perturbation Model

Use an OHLC-preserving multiplicative perturbation. The implementation must not
emit invalid bars.

| Parameter | Default | Range |
|---|---|---|
| `noise_pct` | 0.005 (0.5%) | 0.001 to 0.05 |
| `base_seed` | 42 | Any int |
| `iterations` | 50 | 10 to 500 |

Each iteration draws a different noise sample using `base_seed + i`. Noise is
generated independently per bar. No future bars influence current or past bars.

### Required OHLC Reconstruction

For each bar:

1. Perturb `open` and `close` with independent clipped multiplicative noise.
2. Preserve the original high/low wick distances from the noisy body:
   - `upper_wick = max(0, high - max(open, close))`
   - `lower_wick = max(0, min(open, close) - low)`
3. Perturb wick lengths with non-negative multipliers.
4. Reconstruct:
   - `high = max(open_noisy, close_noisy) + upper_wick_noisy`
   - `low = min(open_noisy, close_noisy) - lower_wick_noisy`
5. Leave `volume` unchanged.

This guarantees:

```text
high >= max(open, close)
low <= min(open, close)
high >= low
```

## 4. Deterministic Behavior

```python
rng = np.random.default_rng(base_seed + iteration_index)
body_noise = np.clip(rng.normal(0.0, noise_pct, size=(len(df), 2)), -0.20, 0.20)
wick_noise = np.clip(rng.normal(0.0, noise_pct, size=(len(df), 2)), -0.95, 5.00)

open_noisy = df["open"] * (1.0 + body_noise[:, 0])
close_noisy = df["close"] * (1.0 + body_noise[:, 1])
upper_wick = (df["high"] - np.maximum(df["open"], df["close"])).clip(lower=0.0)
lower_wick = (np.minimum(df["open"], df["close"]) - df["low"]).clip(lower=0.0)
high_noisy = np.maximum(open_noisy, close_noisy) + upper_wick * (1.0 + wick_noise[:, 0])
low_noisy = np.minimum(open_noisy, close_noisy) - lower_wick * (1.0 + wick_noise[:, 1])
```

Results are deterministic given the same `(base_seed, noise_pct, iterations, df)`.

## 5. Pass/Fail Metrics

| Metric | Meaning |
|---|---|
| `median_total_pnl` | Median PnL across noisy iterations |
| `median_profit_factor` | Median profit factor across noisy iterations |
| `worst_total_pnl` | Worst PnL across noisy iterations |
| `worst_max_drawdown_pnl` | Worst max drawdown across noisy iterations |
| `pnl_degradation_ratio` | `median_total_pnl / baseline_pnl`; defined only when `baseline_pnl > 0` |
| `win_rate_change` | `median_noise_win_rate - baseline_win_rate` |
| `survival_rate` | Share of iterations still satisfying configured minimum gates |

Suggested flags:

- If `baseline_pnl > 0`, flag when `pnl_degradation_ratio < 0.8` or `win_rate_change < -0.1`.
- If `baseline_pnl <= 0`, do not compute `pnl_degradation_ratio`; emit an undefined-ratio warning and evaluate survival/failure counts only.
- A non-positive baseline must not be upgraded to a pass because noisy runs happen to improve it.

## 6. Pipeline Integration

The stress test should follow the existing `validation_pipeline_service.py`
stress-result pattern:

```python
if cfg.run_price_noise_stress:
    result = stress_price_noise(...)
    stress_results.append(result)
```

Proposed `PipelineConfig` fields:

```python
run_price_noise_stress: bool = False
price_noise_pct: float = 0.005
price_noise_iterations: int = 50
price_noise_seed: int = 42
```

Default behavior must remain unchanged.

## 7. Assumptions and Warnings

| Assumption | Detail |
|---|---|
| Gaussian noise model | Approximate diagnostic; not a market microstructure model |
| OHLC-preserving reconstruction | Bar-level high/low constraints must be preserved |
| No slippage model change | Noise is applied to data before the backtest; existing execution settings still apply |
| Research-only output | Results must not be described as live-trading robustness |

Required warning:

```text
Price-noise stress test is an approximate robustness diagnostic. It does not prove live-trading robustness.
```

## 8. Focused Tests (Future)

| # | Test | Scope |
|---|---|---|
| 1 | `stress_price_noise` returns expected structure | Happy path |
| 2 | Same seed returns identical noisy metrics | Reproducibility |
| 3 | Different seeds produce different noisy samples | Noise variance |
| 4 | `noise_pct=0` returns baseline-equivalent metrics | Identity |
| 5 | Perturbed data preserves `high >= max(open, close)` and `low <= min(open, close)` | Data integrity |
| 6 | Non-positive baseline PnL emits undefined degradation-ratio warning | Edge case |
| 7 | `run_price_noise_stress=False` does not run stress | Pipeline default |
| 8 | Invalid `noise_pct` or `iterations` raises a clear validation error | Config validation |

## 9. Metadata

- Author: DeepSeek V4, amended by Codex review
- Date: 2026-06-08
