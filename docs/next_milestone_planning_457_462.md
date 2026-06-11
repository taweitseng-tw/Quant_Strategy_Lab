# Next Milestone Planning - Tasks 457-462

Planning and recommendation note. No production code changed.

Date: 2026-06-11

## Options Compared

### Option A: Event-Driven Backtest Performance / Correctness Hardening

Focus:
- Same-bar stop-loss / take-profit ambiguity handling.
- Tick-size and slippage alignment.
- Indicator caching and performance profiling for repeated strategy runs.

Pros:
- Directly improves backtest honesty and quant correctness.
- Reduces the risk of false positive strategies before adding larger features.
- Fits the project's conservative execution assumptions.

Cons:
- Requires careful engine-level review and deterministic tests.

### Option B: Data Workflow Polish

Focus:
- CSV schema detection refinements.
- Data quality messaging.
- Resampling and import workflow polish.

Pros:
- Improves day-to-day usability for messy user data.
- Lower architecture risk than engine work.

Cons:
- Data workflow is already usable enough for the next correctness slice.

### Option C: Technical Debt / Code Hygiene

Focus:
- Formatting standardization.
- Legacy documentation cleanup.
- Smaller organization and test hygiene work.

Pros:
- Reduces future review friction.
- Helps long-running multi-agent workflow quality.

Cons:
- Less direct product value than improving execution correctness.

## Recommendation

Recommended milestone:

**Option A - Event-Driven Backtest Performance / Correctness Hardening**

Reasons:

1. Backtest correctness is the highest-leverage next area after Strategy Quality acceptance.
2. Same-bar SL/TP ambiguity is directly tied to conservative, no-future-leak execution assumptions.
3. Tick-size/slippage handling affects realism across instruments and reports.
4. Indicator caching can improve repeated strategy runs after correctness behavior is pinned down.

## Recommended Next Tasks

1. **Tasks 463-468 - Same-Bar Stop-Loss / Take-Profit Ambiguity Handling**
   - Goal: audit current behavior, design the smallest correction if needed, and prove stop-loss-first behavior when SL and TP are both touched inside one bar.

2. **Tasks 469-474 - Slippage and Tick-Size Rounding Enforcement**
   - Goal: audit and harden execution price adjustments so they align with tick-size assumptions.

3. **Tasks 475-480 - Backtest Indicator Cache Optimization**
   - Goal: profile repeated indicator calculations and add a conservative cache only where behavior remains deterministic.

## Acceptance For This Planning Slice

- No production code changed.
- Next milestone selected.
- First next task is small and testable.
- Task board points to Tasks 463-468.
