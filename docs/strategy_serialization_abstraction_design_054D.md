# Task 054D — Strategy Serialization Service Abstraction Design

## 1. Current State Summary
Currently, Strategy parsing and `RiskManagement` instantiation logic are duplicated across two primary areas of the codebase:
1. **`repository/strategy_repo.py`**:
   - `_dict_to_risk_management()` is used by `_dict_to_strategy()` when loading strategies from the SQLite database.
   - It acts in a **tolerant mode**, safely falling back to a default `RiskManagement()` instance if the `risk_management` key is missing, null, or malformed.
2. **`app/services/report_service.py`**:
   - `preview_strategy_json()` parses imported JSON payloads from external files.
   - It acts in a **strict mode**, manually inspecting the `risk_management` payload, validating types, rejecting negative numeric values, and collecting errors for malformed structures.

This duplication causes technical debt and introduces the risk of parsing behavior diverging between the persistence layer and the JSON import layer.

## 2. Proposed Abstraction

**Module Location:**
The proposed abstraction should reside in a new service layer component: `core/serialization/strategy_serializer.py`.
- **Why this location?** The abstraction bridges `core/models` with both `repository` and `app/services`. Placing it in `core/serialization/` avoids circular imports because it sits at the bottom of the architecture hierarchy (below `app/` and `repository/`), making it globally accessible to both data engines and UI services.

**Public API:**
```python
from core.models.strategy import Strategy, RiskManagement
from typing import Any

def strategy_from_dict(payload: dict, *, strict: bool = False, source: str = "unknown") -> Strategy:
    """Parses a Strategy from a dictionary, delegating sub-components like RiskManagement."""
    pass

def strategy_to_dict(strategy: Strategy) -> dict:
    """Serializes a Strategy to a standard dictionary payload."""
    pass

def risk_management_from_dict(payload: Any, *, strict: bool) -> RiskManagement:
    """
    Parses RiskManagement rules.
    If strict=True (e.g., JSON import), raises ValueError or collects validation errors.
    If strict=False (e.g., DB load), fails safe to RiskManagement().
    """
    pass
```

**Ownership Boundary:**
- `strategy_serializer.py` owns the conversion of dictionaries to/from model objects.
- `strategy_repo.py` owns the SQL-to-dictionary fetching and saves.
- `report_service.py` owns the file-to-dictionary reading and UI error collection.

**Strict vs Tolerant Modes:**
- `strict=True` is used by the JSON importer to enforce schema validity and type safety.
- `strict=False` is used by the repository to ensure backward compatibility and prevent DB loading crashes.

## 3. Behavior Matrix

| Input Condition | `strict=False` (Repository Legacy) | `strict=True` (JSON Import) |
| --- | --- | --- |
| Missing `risk_management` key | Returns default `RiskManagement()` | Returns default `RiskManagement()` |
| `risk_management: null` | Returns default `RiskManagement()` | Returns default `RiskManagement()` |
| Empty dict `{}` | Returns default `RiskManagement()` | Returns default `RiskManagement()` |
| Valid positive values | Returns parsed `RiskManagement` | Returns parsed `RiskManagement` |
| Negative numeric values | Clamps to 0 or ignores (tolerant) | Rejects payload as invalid |
| Wrong type (e.g., bool/string) | Returns default `RiskManagement()` | Rejects payload as invalid |
| Unknown extra fields | Ignores extra fields | Ignores extra fields |

## 4. Migration Plan

**Phase 1: Introduce Helper without Behavior Change**
- Create `core/serialization/strategy_serializer.py`.
- Replicate existing validation logic into `strict` and `tolerant` modes without wiring it up.

**Phase 2: Route Repository**
- Refactor `repository/strategy_repo.py` to use `strategy_from_dict(..., strict=False)`.
- Ensure round-trip legacy tests pass.

**Phase 3: Route Report Service**
- Refactor `app/services/report_service.py` to use `strategy_from_dict(..., strict=True)`.
- Map raised errors to the existing UI error collector format.

**Phase 4: Cleanup**
- Remove duplicated local parsing logic.
- Ensure test parity.

## 5. Test Plan

A robust `054D-Implementation` test suite must be built to verify parity:
1. **Repository Round-Trip Tests**: Assert that legacy SQL loads still resolve to `RiskManagement()`.
2. **JSON Preview Tests**: Ensure the UI correctly flags invalid strings, negative numbers, and null types in `strict=True` mode.
3. **Legacy Fallback Tests**: explicitly feed legacy missing/null payloads through `strict=False` to ensure no crashes.
4. **Backtest Consistency Tests**: After deserialization via the new helper, ensure the backtest engine still treats `RiskManagement()` as "disabled" (has no precedence effect on `assumptions`).

## 6. Risks and Tradeoffs

- **Backward Compatibility Risk**: The main risk lies in inadvertently switching a tolerant repository load into a strict mode, breaking old saved projects. This must be verified by tests.
- **Error Collection Architecture**: `preview_strategy_json` currently populates an `errors` list for UI display. The serializer will likely need to raise a specific `ValidationError` exception that `report_service.py` catches and formats, which is a known tradeoff in cleanly separating serialization from UI messaging.
- **Circular Import Risk**: Placed inside `core/serialization/`, the risk is minimal as long as it only imports `core/models`. It must avoid importing any services or repository layers.

## 7. Explicit Non-Goals
- No schema overhaul or new features.
- No third-party dependencies (e.g., `pydantic`).
- No database migrations.
- No production behavior changes.
