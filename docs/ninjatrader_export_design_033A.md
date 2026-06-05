# Task 033A: NinjaTrader Strategy Export Design

## 1. Goal
Design a safe NinjaTrader (NinjaScript / C#) export approach for `Strategy` objects. The output must serve strictly as research/backtesting reference code (pseudocode) and must explicitly prevent the generation of executable live-trading code.

## 2. Safety Boundaries & Exporter Philosophy
Quant Strategy Lab is an offline research tool. Exported strategy scripts must never be readily deployable into a live broker environment without deliberate, manual user translation. 
To enforce this:
- We will export the **logic and conditions** only.
- We will **not** export order routing commands.

### Allowed Concepts
- Indicator instantiations and calculations (e.g., `SMA(Close, 20)`).
- Boolean condition blocks (e.g., evaluating `bool longEntry = ...`).
- Research and backtesting comments explaining the strategy intent.
- C# boilerplate structure containing only `State.Configure` and `OnBarUpdate()`.

### Forbidden Concepts / Keywords
The exporter and its tests must strictly forbid generating the following NinjaTrader execution methods and concepts:
- `EnterLong`, `EnterShort`, `ExitLong`, `ExitShort`
- `SubmitOrder`, `SubmitOrderUnmanaged`
- `Account`, `Position`
- `ATM`, `AtmStrategy`
- Words: "live trading", "broker"

## 3. Mandatory Disclaimer
Every generated file must contain the following exact string in the header comments:
> "Research/backtesting only. Not financial advice. Not live trading code."

## 4. Code Generation Mapping (MVP)

A NinjaTrader export will follow a rigid template where conditions are mapped to boolean variables in `OnBarUpdate()`.

### Strategy Blocks
The 4 strategy blocks (`long_entry`, `long_exit`, `short_entry`, `short_exit`) will translate into local boolean assignments:
```csharp
bool longEntry = false;
bool longExit = false;
bool shortEntry = false;
bool shortExit = false;
```

### Supported Indicators
The MVP evaluator supports `SMA`, `RSI`, `MACD`, and `ATR`. The translation to NinjaScript syntax will be:
- **SMA**: `Close[0] > SMA(Close, {period})[0]`
- **RSI**: `RSI({period}, 3)[0] > {threshold}`
- **MACD**: `MACD({fast}, {slow}, {signal})[0] > MACD({fast}, {slow}, {signal}).Avg[0]`
- **ATR**: `ATR({period})[0] > {threshold}`

*Note on RSI parameters: NinjaTrader RSI defaults to a 3-period smoothing. We will pass the smoothing parameter statically or note it in a comment.*

### Unsupported Indicators & Fallback
If an unknown indicator or unsupported operator is encountered (e.g. `==`), the exporter will output a fallback block:
```csharp
// Unsupported indicator/operator: UNKNOWN
bool longEntry = false;
```

### Condition Logic (AND / OR)
Conditions within a block will be joined using C# logical operators:
- `AND` maps to `&&`
- `OR` maps to `||`

## 5. Test Plan for Future Implementation (Task 033B)
When implementing `reports/ninjatrader_exporter.py`, the following tests must be included:
1. `test_export_ninjatrader_contains_disclaimer`: Asserts the exact mandatory disclaimer is present.
2. `test_export_ninjatrader_no_live_trading_keywords`: Asserts none of the forbidden keywords (`EnterLong`, `SubmitOrder`, `Account`, etc.) are present in the output.
3. `test_export_ninjatrader_sma`: Verifies C# syntax for `SMA` translation.
4. `test_export_ninjatrader_multiple_indicators`: Verifies `RSI`, `MACD`, and `ATR` generation.
5. `test_export_ninjatrader_logic_and_or`: Verifies `&&` and `||` mapping.
6. `test_export_ninjatrader_unsupported`: Verifies the safe fallback for unknown indicators.

## 6. Integration Boundaries
- `ReportService` will eventually call the new `export_strategy_to_ninjatrader` method if the file extension is `.cs`.
- The `UI` will invoke `ReportService` with a `.cs` path.
- The `strategy_engine` and `evaluator.py` will **not** be modified to support this exporter. The exporter will consume the existing `Strategy` model.
