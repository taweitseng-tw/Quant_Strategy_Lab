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


def test_risk_management_from_dict_session_end():
    """Test parsing of session end fields."""
    payload = {"close_end_of_session": True, "session_end_time": "15:45:00"}
    rm = risk_management_from_dict(payload, strict=True)
    assert rm.close_end_of_session is True
    assert rm.session_end_time == "15:45:00"


def test_strategy_to_dict_roundtrip_session_end():
    """Ensure session end fields roundtrip correctly."""
    original = Strategy(name="Session End Strat")
    original.risk_management = RiskManagement(close_end_of_session=True, session_end_time="16:00")

    payload = strategy_to_dict(original)
    assert payload["risk_management"]["close_end_of_session"] is True
    assert payload["risk_management"]["session_end_time"] == "16:00"


    reloaded = strategy_from_dict(payload, strict=True)
    assert reloaded.risk_management.close_end_of_session is True
    assert reloaded.risk_management.session_end_time == "16:00"

def test_risk_management_from_dict_session_end_strict_format():
    """Ensure strict validation rejects malformed session_end_time."""
    payload = {"close_end_of_session": True, "session_end_time": "invalid_time"}
    with pytest.raises(SerializationError, match="must be HH:MM or HH:MM:SS format"):
        risk_management_from_dict(payload, strict=True)

    payload_num = {"close_end_of_session": True, "session_end_time": 1600}
    with pytest.raises(SerializationError, match="must be a string or null"):
        risk_management_from_dict(payload_num, strict=True)

def test_risk_management_from_dict_session_end_strict_range():
    """Ensure strict validation rejects invalid clock ranges but accepts valid ones."""
    invalid_times = ["24:00", "99:99", "12:60", "09:30:60"]
    for inv in invalid_times:
        payload = {"close_end_of_session": True, "session_end_time": inv}
        with pytest.raises(SerializationError, match="must be HH:MM or HH:MM:SS format"):
            risk_management_from_dict(payload, strict=True)

    valid_times = ["00:00", "09:30", "16:00:00", "23:59:59"]
    for val in valid_times:
        payload = {"close_end_of_session": True, "session_end_time": val}
        rm = risk_management_from_dict(payload, strict=True)
        assert rm.session_end_time == val
