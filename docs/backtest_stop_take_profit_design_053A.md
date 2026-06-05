# Task 053A: Backtest Stop-Loss / Take-Profit Execution Design

## 1. Context and Current Gap
A correctness gap exists in the current event-driven backtest engine (`backtest_engine/runner.py`). The engine evaluates entry and exit conditions strictly at the close of a bar and executes the trade at the open of the next bar. 

While this accurately models signal confirmation delays, it completely misses intra-bar price action for active position management. Currently, if an open position experiences a massive adverse swing intra-bar (where a real-world stop-loss order would trigger), the engine ignores it until the bar close. This allows strategies to survive drawdowns they would not survive in live trading, leading to unrealistic survival rates and potential overfitting.

This document defines the precise architecture for inserting Stop-Loss (SL) and Take-Profit (TP) logic into the event loop.

## 2. Event-Loop Insertion Point
The execution loop in `runner.py` must distinguish between "entry signal timing" (next-bar open) and "active position management" (intra-bar).

**Proposed Execution Loop Flow:**
1. **Queue Execution (Bar Open)**: Execute pending entry/exit signals from the previous bar's close. 
2. **[NEW] Active Risk Management (Intra-Bar)**: If a position is open (either carried over from the previous bar or just opened in Step 1), evaluate the current bar's `high` and `low` against the calculated SL and TP price levels.
   - If triggered, the position is closed immediately, generating an exit trade.
3. **Mark-to-Market (Bar Close)**: Calculate equity using the current `close` (if the position is still open) or cash balance (if closed by SL/TP).
4. **Signal Evaluation (Bar Close)**: Evaluate rule-based exit or entry conditions. If the position was already closed in Step 2, rule-based exits are skipped.

## 3. Risk Management Configuration Model
To represent SL and TP constraints without cluttering the base strategy logic, a new `RiskManagement` configuration block should be introduced into the `Strategy` model.

```python
@dataclass
class RiskManagement:
    """Intra-bar risk management constraints."""
    stop_loss_ticks: float | None = None
    take_profit_ticks: float | None = None
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None
```
The `Strategy` model will be updated to include `risk_management: RiskManagement = field(default_factory=RiskManagement)`.
If all fields are `None`, SL/TP checks are bypassed (preserving baseline performance). Future extensions can add ATR-based trailing stops here.

## 4. Long and Short Execution Logic
The SL/TP price thresholds are calculated once at the moment of entry, based on the `entry_price`.

### Long Position
- **Stop-Loss Trigger**: Current bar's `low <= SL_Price`.
- **Take-Profit Trigger**: Current bar's `high >= TP_Price`.

### Short Position
- **Stop-Loss Trigger**: Current bar's `high >= SL_Price`.
- **Take-Profit Trigger**: Current bar's `low <= TP_Price`.

### Execution Price and Slippage
- **Standard Trigger**: The trade is assumed to fill exactly at the `SL_Price` or `TP_Price`.
- **Gap Trigger**: If the bar's `open` is already beyond the SL/TP price (e.g., gap down below long SL), the trade must execute at the `open` price, NOT the SL/TP price.
- Slippage is applied against the trader (exiting long SL/TP fills slightly lower; exiting short SL/TP fills slightly higher).

## 5. Same-Bar Ambiguity Handling
When both the SL and TP levels are breached within the exact same bar (e.g., high exceeds TP and low breaches SL), the engine cannot definitively know which occurred first based solely on OHLC data.

**Policy: Conservative Default**
- If both SL and TP are triggered on the same bar, **Stop-Loss always wins**.
- This enforces the most conservative assumption for backtesting to prevent survival bias.
- The `assumptions` dictionary in the `BacktestResult` must clearly log: `{"same_bar_ambiguity": "stop_loss_first"}`.

## 6. Interaction with Rule-Based Signals
- **Priority**: Intra-bar SL/TP checks happen before rule-based exit evaluations. An SL/TP hit preempts any rule-based exit for that bar.
- **Same Bar Conflict**: If a rule-based exit was queued from the previous bar (to execute at this bar's open), it executes at the open (Step 1) and the SL/TP check (Step 2) is entirely bypassed since the position is closed.

## 7. Implications for Trade and BacktestResult
- `Trade.exit_reason`: Must be populated with `"stop_loss"`, `"take_profit"`, `"signal"`, or `"end_of_data"`.
- `Trade.exit_time`: Remains as the current bar's `pd.Timestamp` (the datetime of the bar where the SL/TP was hit).
- `BacktestResult.warnings`: Log if gap-execution occurs (where fill price is worse than requested SL due to market gap).
- **Reports**: Exported reports must clearly state the SL/TP assumptions (e.g., "Conservative same-bar stop-loss-first execution"). No financial advice language.

## 8. Test Plan for Phase 053B Implementation
Before implementing the SL/TP logic in `runner.py`, the following tests must be authored to enforce correctness:

1. **Long Stop-Loss Hit**: Assert position closes at SL price mid-bar with `exit_reason="stop_loss"`.
2. **Long Take-Profit Hit**: Assert position closes at TP price mid-bar with `exit_reason="take_profit"`.
3. **Short Stop-Loss Hit**: Assert correct short SL trigger and exit price.
4. **Short Take-Profit Hit**: Assert correct short TP trigger and exit price.
5. **Same-Bar Ambiguity**: Construct a bar that breaches both SL and TP; assert that SL executes and TP is ignored.
6. **Gap Execution**: Construct a bar that opens completely beyond the SL level; assert the exit price is the `open` price, not the `SL_Price`.
7. **Baseline Equivalence**: Run `test_backtest_accounting_identity` and exhaustive GA tests with SL/TP disabled, asserting byte-for-byte identical behavior to pre-053B logic.
8. **Next-Bar Open Integrity**: Assert that rule-based entry at next-bar-open remains unchanged.
9. **Final-Bar Integrity**: Assert final-bar open positions correctly exit as `"end_of_data"`.
10. **Type Verification**: Assert trade timestamps remain `pd.Timestamp`.
