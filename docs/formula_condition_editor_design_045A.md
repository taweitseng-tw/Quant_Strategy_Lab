# Task 045A — Formula Condition Editor Design

## 1. Overview
The Formula Condition Editor will provide a UI allowing users to construct strategy rules via a simple formula text syntax (e.g., `close > SMA(20)`). To maintain security and execution stability, this feature will map text directly to the existing `Condition` and `StrategyBlock` data models without executing arbitrary Python code.

## 2. Forbidden Operations
To ensure the system remains deterministic, secure, and compatible with the C++ / genetic programming roadmap, the following are strictly **FORBIDDEN**:
- `eval()`, `exec()`, or `compile()` evaluating to runtime code.
- Arbitrary Python functions, built-ins, or methods (e.g., `getattr`, `__import__`, `print`).
- Loops, list comprehensions, or control flow logic (`if/else` inside the formula).
- File, network, or OS access.
- Any direct references to `backtest_engine`, `broker`, or UI states.

*Instead, the parser will parse the formula text (using `ast.parse` strictly checking node types, or a custom regex/tokenizer) and map it deterministically to `Condition` objects.*

## 3. Allowed Tokens & Operators
- **Market Data Fields**: `close`, `open`, `high`, `low`, `volume`
- **Supported Indicators**: `SMA`, `RSI`, `MACD`, `ATR`, `VOLUME_SMA`, `VOLUME`
- **Comparison Operators**: `>`, `<` (MVP focuses on inequality, matching existing engine capabilities).
- **Arithmetic Modifiers**: `*` (Used exclusively for `VOLUME_SMA` multiplier in MVP, e.g., `VOLUME_SMA(20) * 1.5`).
- **Literals**: Numeric constants (integers and floats).
- **Logic Gates**: `AND`, `OR` (Used to split conditions into `StrategyBlock.conditions` array).

## 4. Model Mapping (MVP)
Formulas will compile directly into the existing `Condition` dataclass. No new `FormulaCondition` model is needed for MVP, keeping the `evaluator.py` completely unchanged.

**Mapping Examples:**
1. `close > SMA(20)`
   - `indicator`: "SMA"
   - `params`: `{"period": 20}`
   - `operator`: ">"
   - `left`: "close"

2. `RSI(14) < 30`
   - `indicator`: "RSI"
   - `params`: `{"period": 14}`
   - `operator`: "<"
   - `right`: 30.0

3. `volume > VOLUME_SMA(20) * 1.5`
   - `indicator`: "VOLUME_SMA"
   - `params`: `{"period": 20}`
   - `operator`: ">"
   - `right`: 1.5

4. `close > SMA(20) AND RSI(14) < 30`
   - Returns a `StrategyBlock` with `logic="AND"` and the two `Condition` objects above.

## 5. UI/UX Concept
- **Editor Widget (`FormulaEditorWidget`)**:
  - A plain text entry box (`QLineEdit` or `QPlainTextEdit`).
  - A real-time validation label beneath it (`QLabel`) indicating syntax correctness.
  - A visual "Cheat Sheet" or auto-complete popup showing available tokens.
  - Action buttons: "Add to Long Entry", "Add to Short Exit", etc.
- **Feedback**: The "Add" buttons remain disabled until the validation label reports a successful parse.

## 6. Validation Behavior & Errors
Real-time parsing will catch errors before submission:
- **Syntax Error**: "Syntax Error: Unclosed parenthesis or missing operator."
- **Unsupported Token**: "Error: 'EMA' is not a supported indicator."
- **Invalid Comparison**: "Error: Cannot compare two indicators directly in MVP."
- **Security Rejection**: "Error: Invalid token detected. Only basic conditions are allowed."

## 7. Test Plan (Future Implementation)
When the parser and UI are implemented, the following tests are mandatory:
1. **Parser Unit Tests**:
   - Correct mapping of all supported indicators to `Condition` objects.
   - Successful `AND`/`OR` splitting.
   - Rejection of unknown indicators or typos.
   - Strict rejection of malicious AST nodes (`Call`, `Attribute`, `Import`).
2. **Widget Tests**:
   - Emitting parsed `StrategyBlock` via signals.
   - Disabling submit buttons on parse failure.
   - Updating UI validation text seamlessly.
