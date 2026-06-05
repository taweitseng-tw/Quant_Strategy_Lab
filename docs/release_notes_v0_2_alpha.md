# v0.2 Alpha Release Notes

## Overview
v0.2 Alpha introduces major expansions to the validation layer, strategy generation capabilities, and external ecosystem integrations, establishing Quant Strategy Lab as a more robust research tool while maintaining strict no-future-leak guarantees and testability.

## Accepted Features

1. **Genetic Programming (GP)**
   - Tree-based strategy condition generation supporting crossover and mutation.
   - Fully integrated into the UI and ranking flow without polluting the flat evaluation engine.
2. **Multi-Instrument Backtest Engine**
   - Service-level orchestration allowing strategies to be tested across multiple datasets and instrument profiles simultaneously.
   - Aggregate metrics computation while gracefully handling missing data and exceptions on individual instruments.
3. **Strategy Code Export**
   - Safe Python (`.py`) and NinjaTrader C# (`.cs`) strategy skeleton generation.
   - Strict architectural constraints ensure only condition logic is exported—preventing accidental generation of live execution or broker APIs.
4. **Report / PDF Export Chain**
   - Advanced reporting including HTML, Markdown, and PDF document generation containing equity curves, trade lists, metrics, and strategy provenance.
5. **Volume Conditions**
   - Evaluator and generator support for absolute Volume thresholds and relative Volume SMAs.
6. **Custom Elimination Rules UI**
   - Dynamic threshold configuration via a dedicated UI panel to filter out strategies that fail to meet user-defined net profit, max drawdown, or trade count rules.
7. **Monte Carlo Simulation Enhancements**
   - Combined deterministic slippage and missed-trade simulations.
   - Configurable percentile distributions and cross-run stability scoring.
8. **Walk-Forward Partial Enhancements**
   - Robustness matrix simulation to validate strategy performance across multiple overlapping walk-forward window sizes and step overlaps.
9. **Formula Condition Editor**
   - A safe, strictly whitelisted string formula parser (rejecting `eval()` and `exec()`).
   - Integrated UI allowing users to manually append custom expressions (e.g., `RSI(14) > 70 AND SMA(50) > SMA(200)`) to existing strategies.

10. **Walk-Forward Efficiency (WFE)**
   - Full diagnostic implementation of Walk-Forward Efficiency calculation (in-sample vs out-of-sample).
   - Graceful markdown/HTML/PDF reporting and strict UI opt-in integration to preserve backward compatibility.

## Safety Boundaries Verified
- **No Future Leak**: Evaluation rules strictly compute signals on current/past bar close and execute on next open.
- **Whitelist Enforcement**: Formula parsing safely maps text to `StrategyBlock` / `Condition` objects without arbitrary code execution risk.
- **Passivity**: UI Widgets (`StrategyDetailWidget`, `EliminationConfigWidget`, `FormulaConditionEditor`) do not import or mutate core engine logic. 
- **Determinism**: Random strategy generators and GP operators remain strictly deterministic based on provided seeds.

## Known Deferred Items
The following items were pushed out of the v0.2 milestone and will be targeted in a future release:
- **Proposed Task 049: Multi-timeframe conditions** — Support for querying larger timeframes (e.g., daily trends on an hourly chart).

## 048A Post-WFE Verification Results Summary
- 823 regression tests ran with **100% success rate** (1 known benign pandas warning).
- PySide6 Application smoke test confirmed a clean and responsive boot.

## 047A Verification Results Summary
- 805 regression tests ran with **100% success rate**.
- Targeted component test suites confirmed total pass rates for GP, Exporters, Validation modules, and Formula parsing.
- PySide6 Application smoke test confirmed a clean and responsive boot.
- Documentation states (Task board and Changelog) are fully reconciled.

---

## Tag Preparation Checklist

*(For the human maintainer/user to execute when ready to finalize the tag)*

```bash
# 1. Ensure working directory is clean
git status

# 2. Add all updated docs and run tests one final time
python -m compileall app core strategy_engine backtest_engine validation_engine reports repository tests
python -m pytest tests/ -q

# 3. Commit the release prep
git add .
git commit -m "chore: prepare v0.2 alpha release"

# 4. Create the annotated git tag
git tag -a v0.2-alpha -m "v0.2 Alpha Release"

# 5. Push tags to remote (if applicable)
git push origin main --tags
```
