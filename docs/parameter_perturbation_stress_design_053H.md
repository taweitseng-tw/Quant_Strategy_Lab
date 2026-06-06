# Parameter Perturbation Stress Test Design (Task 053H)

## 1. Overview
The final MVP stress test is **Parameter Perturbation**. Over-optimized (curve-fit) strategies tend to collapse when their parameters are slightly altered. A robust strategy should survive small changes to its indicator periods, thresholds, or stop-loss limits.

## 2. Perturbable Parameters
The perturbation engine will target numeric parameters deeply embedded in the `Strategy` definition:
1. **Indicator Periods**: e.g., SMA period, RSI period (typically integers).
2. **Thresholds & Levels**: e.g., RSI overbought boundary (float or integer).
3. **Trade Management Limits**: e.g., Stop Loss (SL) ticks, Take Profit (TP) ticks, holding bars limit.

## 3. Perturbation Model
Because parameters have different scales and types, the perturbation model will apply type-specific shifts:

- **Integers (Additive Model)**:
  - Justification: Integer parameters often represent discrete bars or periods (e.g., period=10). A multiplicative shift on a small integer (e.g., period=3) might yield no change or too large a change.
  - Method: Random additive shift within a range `[-N, +N]` (excluding 0).
  - Safety: Values will be clamped to a logical minimum (e.g., `max(1, original + shift)` for periods).

- **Floats (Multiplicative Model)**:
  - Justification: Floats usually represent prices, ratios, or tight thresholds where scale matters.
  - Method: Random multiplicative shift by `±P%` (e.g., ±5%).

## 4. Perturbation Variants (N Random vs. Grid)
- **N Random Variants**: We will use a Monte Carlo-style generation of `N` random variants (default `N = 5`) rather than a systematic grid.
- **Justification**: A strategy with 5 parameters would require $3^5 = 243$ runs in a simple grid search (`[-1, 0, +1]`), which is too slow for the validation pipeline. Random sampling of the parameter space keeps the backtest engine fast while successfully exposing brittle strategies.

## 5. API Signature & Flow

### Signature
```python
def stress_parameter_perturbation(
    strategy: Strategy,
    data: pd.DataFrame,
    baseline: BacktestResult,
    instrument: InstrumentProfile | None = None,
    variants_count: int = 5,
    int_shift_range: tuple[int, int] = (-2, 2),
    float_shift_pct: float = 0.05,
    degradation_threshold: float = 0.50,
) -> StressTestResult:
```

### Flow
1. Verify the strategy actually has parameters to perturb. If no numeric parameters exist, return an automatic pass.
2. Generate `variants_count` mutated copies of the strategy.
3. Run `run_backtest` for each variant.
4. Calculate the average Net Profit across all variants.
5. Compare the average variant Net Profit to the baseline Net Profit.

### Pass/Fail Threshold
- The test **FAILS** if the average variant Net Profit is less than `baseline.total_pnl * (1 - degradation_threshold)` (e.g., average profit drops by more than 50%).
- The test **FAILS** if the average variant Net Profit becomes negative.

## 6. No-Future-Leak & Baseline Preservation
- **Preservation**: The original `Strategy` object must be deep-copied before any perturbation. The stress test must not mutate the original strategy reference, ensuring downstream pipeline steps test the unmodified strategy.
- **No-Future-Leak**: Perturbation strictly mutates internal strategy logic parameters. The data (`data`) fed into the backtest remains exactly the `train` split. No out-of-sample data is touched, preventing future leaks.

## 7. Deterministic Test Cases
To verify the engine, we will implement the following deterministic tests in `tests/test_parameter_perturbation.py`:
1. **Mock Variant Generator Check**: Assert that given a seed, the parameters shift predictably (integers additive, floats multiplicative).
2. **Robust Strategy Survival**: A mock strategy that returns the exact same trades despite shifted parameters. It must return a 0% degradation and pass.
3. **Overfit Strategy Collapse**: A mock dataset where a strategy with `period=10` perfectly captures profit, but `period=9` and `period=11` generate huge losses. The stress test must accurately average the losses and mark the test as **FAILED**.
4. **No-Mutation Guarantee**: Assert that the baseline `Strategy` object's parameters remain exactly the same after `stress_parameter_perturbation` completes.
