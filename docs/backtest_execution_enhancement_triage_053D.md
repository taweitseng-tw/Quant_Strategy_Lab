# Task 053D - Backtest Execution Enhancements Triage

## 1. Overview
This document evaluates the current backtest execution model implemented in `backtest_engine/runner.py` (which currently features next-bar open execution and intra-bar Stop-Loss/Take-Profit management). It identifies the highest-value execution enhancements, triages their implementation risks, and recommends a single next step.

## 2. Candidate Enhancements

### Candidate A: Session-End Exit Behavior (Day Trading Enforcement)
- **Current Behavior**: Positions remain open overnight indefinitely until a rule-based exit or SL/TP triggers.
- **Desired Behavior**: Add an optional `RiskManagement` configuration (e.g., `close_end_of_session: bool = False` and `session_end_time: str | None = None`) to force-close any open positions at the close of the configured session. Defaults must preserve existing behavior (no session-end exit) for old strategies and serialized JSON.
- **Risk Level**: Medium.
- **Future-leak / Same-bar Ambiguity Risk**: Low, provided the implementation is strictly based on the configured session rules. **Crucially, the engine must NOT discover the day's final bar by scanning or grouping the full dataset**, as this would leak future knowledge into the current bar.
- **Files Likely Involved**: `backtest_engine/runner.py`, `core/models/strategy.py`.
- **Required Tests**: 
  - Assert no future-row dependency (session-end behavior does not depend on future rows being present).
  - Assert missing final bars / early close behavior (e.g., exiting when `bar_datetime.time() >= session_end_time`).
  - Assert long and short session-end exits.
  - Assert appropriate slippage/commission is applied on session-end exits.
  - Assert assumptions reporting cleanly captures session-end logic.
  - Assert backward-compatible import/repository/serializer handling for strategies lacking the new `RiskManagement` fields.
- **Recommended Implementation Order**: 1

### Candidate B: One-Bar Execution Delay Stress Test Integration
- **Current Behavior**: Execution always happens exactly at the next bar's open (`T+1`).
- **Desired Behavior**: Introduce an execution delay parameter (e.g., `execution_delay_bars=1`) to simulate severe latency or signal degradation, executing at `T+2` open. This fulfills the AGENTS.md requirement for a "One-bar execution delay test".
- **Risk Level**: Low to Medium.
- **Future-leak / Same-bar Ambiguity Risk**: None. Delaying execution makes the backtest strictly worse and uses older signals.
- **Files Likely Involved**: `backtest_engine/runner.py` (to buffer pending actions), `validation_engine/stress_test.py`.
- **Required Tests**: 
  - Assert entry and exit fills occur exactly `execution_delay_bars` later.
  - Assert SL/TP logic correctly adapts or ignores the delayed entry period until filled.
- **Recommended Implementation Order**: 2

### Candidate C: Same-Bar Ambiguity Refinement
- **Current Behavior**: When both Stop-Loss and Take-Profit are hit in the exact same bar, Stop-Loss is hardcoded to win (conservative default).
- **Desired Behavior**: Expose this as a configuration in `RiskManagement.same_bar_ambiguity`. Options: `stop_loss_first` (default), `take_profit_first` (optimistic), or `random` (Monte Carlo stress testing).
- **Risk Level**: Medium.
- **Future-leak / Same-bar Ambiguity Risk**: This feature explicitly manages ambiguity. The risk is that exposing `take_profit_first` allows users to create optimistic, curve-fitted backtests.
- **Files Likely Involved**: `backtest_engine/runner.py`, `core/models/strategy.py`.
- **Required Tests**: 
  - Assert the engine respects the selected ambiguity resolution mode.
  - Assert assumptions dict explicitly logs if optimistic mode is used.
- **Recommended Implementation Order**: 3

### Candidate D: Slippage / Commission Stress Interaction
- **Current Behavior**: Slippage and commission are static values per-instrument or per-run.
- **Desired Behavior**: Allow dynamic slippage modifiers (e.g., ATR-based slippage to simulate market impact during high volatility) and stress-test pipelines that programmatically multiply slippage/commission across iterations.
- **Risk Level**: High (complexity in the hot loop, performance impact).
- **Future-leak / Same-bar Ambiguity Risk**: Low, provided ATR/volatility metrics use strictly backward-looking windows.
- **Files Likely Involved**: `backtest_engine/runner.py`, `validation_engine/stress_test.py`.
- **Required Tests**: 
  - Assert slippage scales correctly with the defined volatility metric.
- **Recommended Implementation Order**: 4

### Candidate E: Trade Assumption Reporting
- **Current Behavior**: Trade execution assumptions (slippage, tick size, SL precedence) are embedded in a dictionary inside `BacktestResult.assumptions`.
- **Desired Behavior**: Expose these assumptions prominently in the UI and markdown reports so users cannot unknowingly accept unrealistic parameters.
- **Risk Level**: Low.
- **Future-leak / Same-bar Ambiguity Risk**: None (UI/reporting only).
- **Files Likely Involved**: `reports/generator.py`, `app/widgets/strategy_detail.py`, `app/ui/main_window.py`.
- **Required Tests**: 
  - Assert assumptions dictionary renders in HTML/Markdown exports.
- **Recommended Implementation Order**: 5

## 3. Recommendation for Next Implementation Task

**Recommended Task: Candidate A - Session-End Exit Behavior**

**Justification:** 
The lack of a session-end exit mechanic is a major functional gap for any intraday trading strategy. Without it, intraday strategies inadvertently hold positions overnight, exposing them to massive gap risks that a day trader would never take. Implementing this feature fundamentally unlocks accurate intraday strategy generation and backtesting.

**Next Steps for Implementation:**
1. Define the configuration schema in `RiskManagement` (e.g., `close_end_of_session: bool = False`, `session_end_time: str | None = None`) and ensure backward compatibility in serialization.
2. Implement the end-of-session detection logic in `runner.py` strictly using the configured session boundaries and `bar_datetime.time()`, without looking ahead to future bars.
3. Author rigorous tests covering long/short exits, missing final bars, backward compatibility, and the prohibition of future-leaking dataset grouping.
