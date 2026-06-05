"""Tests for strategy serializer logic."""

import pytest
from core.models.strategy import Strategy, RiskManagement
from core.serialization.strategy_serializer import (
    strategy_from_dict,
    strategy_to_dict,
    risk_management_from_dict,
    SerializationError
)

def test_risk_management_from_dict_tolerant_missing_null():
    """Tolerant mode should fail safe to default RiskManagement for missing/null."""
    rm1 = risk_management_from_dict(None, strict=False)
    assert rm1.stop_loss_ticks is None
    
    rm2 = risk_management_from_dict({}, strict=False)
    assert rm2.stop_loss_ticks is None


def test_risk_management_from_dict_tolerant_invalid_types():
    """Tolerant mode should ignore invalid types or negative numbers and fail safe."""
    # Invalid overall type
    rm = risk_management_from_dict("not a dict", strict=False)
    assert rm.stop_loss_ticks is None
    
    # Invalid field type
    rm2 = risk_management_from_dict({"stop_loss_ticks": "twenty"}, strict=False)
    assert rm2.stop_loss_ticks is None
    
    # Negative number
    rm3 = risk_management_from_dict({"stop_loss_ticks": -5.0}, strict=False)
    assert rm3.stop_loss_ticks is None

    # Bool type (bool is a subclass of int, so we must test it explicitly)
    rm4 = risk_management_from_dict({"stop_loss_ticks": True}, strict=False)
    assert rm4.stop_loss_ticks is None


def test_risk_management_from_dict_strict_null():
    """Strict mode allows null risk_management."""
    rm = risk_management_from_dict(None, strict=True)
    assert rm.stop_loss_ticks is None


def test_risk_management_from_dict_strict_invalid_types():
    """Strict mode raises exceptions for invalid types."""
    with pytest.raises(SerializationError, match="must be an object or null"):
        risk_management_from_dict("not a dict", strict=True)
        
    with pytest.raises(SerializationError, match="must be a number or null"):
        risk_management_from_dict({"stop_loss_ticks": "twenty"}, strict=True)
        
    with pytest.raises(SerializationError, match="must be a number or null"):
        risk_management_from_dict({"stop_loss_ticks": True}, strict=True)
        
    with pytest.raises(SerializationError, match="cannot be negative"):
        risk_management_from_dict({"stop_loss_ticks": -5.0}, strict=True)


def test_strategy_from_dict_tolerant_malformed():
    """strategy_from_dict should tolerate malformed data when strict=False."""
    payload = {
        "name": "Tolerant Strat",
        "risk_management": "invalid_string"
    }
    
    strat = strategy_from_dict(payload, strict=False)
    assert strat.name == "Tolerant Strat"
    assert strat.risk_management is not None
    assert strat.risk_management.stop_loss_ticks is None


def test_strategy_to_dict_roundtrip():
    """Ensure strategy_to_dict and strategy_from_dict handle a full roundtrip."""
    original = Strategy(name="Roundtrip Strat")
    original.risk_management = RiskManagement(stop_loss_ticks=10.0, take_profit_pct=0.05)
    
    payload = strategy_to_dict(original)
    assert payload["name"] == "Roundtrip Strat"
    assert payload["risk_management"]["stop_loss_ticks"] == 10.0
    assert payload["risk_management"]["take_profit_pct"] == 0.05
    
    reloaded = strategy_from_dict(payload, strict=True)
    assert reloaded.name == original.name
    assert reloaded.risk_management.stop_loss_ticks == 10.0
    assert reloaded.risk_management.take_profit_pct == 0.05
    assert reloaded.risk_management.take_profit_ticks is None
