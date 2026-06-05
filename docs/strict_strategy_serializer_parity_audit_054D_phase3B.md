# Strict Strategy Serializer Parity Audit (Task 054D - Phase 3B)

## Overview
This document compares the current `strict=True` behavior in `core.serialization.strategy_serializer.strategy_from_dict()` against the comprehensive JSON import validation logic currently embedded in `app.services.report_service.ReportService.preview_strategy_json()`.

The goal is to identify all validation and structural gaps before attempting to replace `preview_strategy_json()` entirely with the serialization helper.

## Parity Analysis

| Validation Area | `ReportService.preview_strategy_json()` | `strategy_serializer.strategy_from_dict(strict=True)` | Gap Status |
| :--- | :--- | :--- | :--- |
| **JSON Root Object** | Errors if root is not an object. | Errors if payload is not a dictionary. | **Parity** (Minor string difference) |
| **Strategy Name** | Required. Must be a non-empty string. | No strict enforcement. Falls back to `"Unknown Strategy"`. | **Gap** |
| **Provenance Object** | Validates as dictionary if present. | Ignored entirely. Not parsed or returned. | **Gap** |
| **Required Blocks** | Enforces presence of all 4 blocks (`long_entry`, etc.). | Uses `.get(..., {})`, allowing missing blocks. | **Gap** |
| **Block Type** | Enforces block is a dictionary. | Enforces block is a dictionary. | **Parity** |
| **Block Logic** | Enforces `logic` is exactly `"AND"` or `"OR"`. | No enforcement. Falls back to `"AND"`. | **Gap** |
| **Condition List** | Enforces `conditions` is a list. | No enforcement (duck typing). | **Gap** |
| **Condition Type** | Enforces condition is a dictionary. | Enforces condition is a dictionary. | **Parity** |
| **Condition Required Fields** | Enforces presence of `indicator`, `params`, `operator`. | No enforcement. Falls back to defaults. | **Gap** |
| **Indicator String** | Enforces non-empty string. | No enforcement. | **Gap** |
| **Params Object** | Enforces dictionary type. | No enforcement. | **Gap** |
| **Operator Enum** | Enforces exactly `">"` or `"<"`. | No enforcement. Falls back to `">"`. | **Gap** |
| **RiskManagement** | Uses strict serializer (since Phase 3A). | Strict mode enforces types, booleans, and negative checks. | **Parity** |
| **Error Handling** | Accumulates all errors into a list. | Fails fast, raising `SerializationError` on the first error. | **Gap** |
| **Contextual Errors** | Error messages include block names and condition indices. | Error messages lack block/index context. | **Gap** |

## Findings
The `strategy_from_dict(..., strict=True)` function is currently severely underpowered compared to the UI-facing `preview_strategy_json` function. While `RiskManagement` was hardened in Phase 3A, the core `Strategy`, `StrategyBlock`, and `Condition` parsers still act as forgiving fallback parsers rather than strict validators.

Furthermore, `preview_strategy_json` accumulates all validation errors at once to present a complete diagnostic report to the user, whereas the serializer currently fails fast by raising exceptions.

## Recommendation

**Recommendation: Split and Proceed to Implementation (with Caveats)**

Replacing `preview_strategy_json()` with `strategy_from_dict()` right now would severely degrade the JSON import experience by removing critical validation and error accumulation.

I recommend splitting the remaining effort into two distinct follow-up tasks:

1. **Task 054D-Impl-Phase3B-Code**: Upgrade `core/serialization/strategy_serializer.py`.
   - Add strict typing, required field checks, and enum enforcement for blocks and conditions.
   - Implement an error accumulation pattern (e.g., passing an `errors: list` down the call stack, or raising a custom `ValidationError` that holds a list of messages) so that the UI can still show all errors at once.
   - Parse and return `provenance`.

2. **Task 054D-Impl-Phase3C**: The final wiring.
   - Only once Phase 3B-Code is complete and perfectly mirrors the accumulated error strings of `ReportService`, we can replace the inline logic in `preview_strategy_json()`.
