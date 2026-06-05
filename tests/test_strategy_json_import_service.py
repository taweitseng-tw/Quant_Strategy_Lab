"""Tests for Strategy JSON import preview service (Task 039B)."""

import pytest
import json
from app.services.report_service import ReportService
from core.models.strategy import Strategy

@pytest.fixture
def report_service():
    return ReportService()

def test_preview_valid_strategy_json(report_service, tmp_path):
    valid_data = {
        "name": "Test Import Strat",
        "provenance": {"source": "test"},
        "long_entry": {
            "logic": "AND",
            "conditions": [
                {"indicator": "SMA", "params": {"period": 20}, "operator": ">"}
            ]
        },
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []}
    }
    file_path = tmp_path / "valid.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    result = report_service.preview_strategy_json(str(file_path))
    assert result["passed"] is True
    assert not result["errors"]
    assert isinstance(result["strategy"], Strategy)
    assert result["strategy"].name == "Test Import Strat"
    assert result["strategy"].long_entry.conditions[0].indicator == "SMA"
    assert result["provenance"] == {"source": "test"}

def test_preview_missing_name_and_block(report_service, tmp_path):
    invalid_data = {
        "long_entry": {"logic": "AND", "conditions": []}
    }
    file_path = tmp_path / "missing.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f)
        
    result = report_service.preview_strategy_json(str(file_path))
    assert result["passed"] is False
    assert "Missing required field: 'name'." in result["errors"]
    assert "Missing required block: 'long_exit'." in result["errors"]

def test_preview_malformed_json(report_service, tmp_path):
    file_path = tmp_path / "malformed.json"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("{ invalid json")
        
    result = report_service.preview_strategy_json(str(file_path))
    assert result["passed"] is False
    assert any("Malformed JSON" in e for e in result["errors"])

def test_preview_invalid_condition(report_service, tmp_path):
    invalid_data = {
        "name": "Test",
        "long_entry": {
            "logic": "AND",
            "conditions": [
                {"indicator": "SMA"} # Missing params, operator
            ]
        },
        "long_exit": {},
        "short_entry": {},
        "short_exit": {}
    }
    file_path = tmp_path / "bad_cond.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f)
        
    result = report_service.preview_strategy_json(str(file_path))
    assert result["passed"] is False
    assert any("missing fields" in e for e in result["errors"])


def test_preview_rejects_invalid_field_types(report_service, tmp_path):
    invalid_data = {
        "name": "",
        "provenance": "not-an-object",
        "long_entry": {
            "logic": "XOR",
            "conditions": [
                {"indicator": "", "params": [], "operator": ">"},
                {"indicator": "SMA", "params": [], "operator": ">"},
                {"indicator": "SMA", "params": {"period": 20}, "operator": ">="},
            ],
        },
        "long_exit": {"logic": "AND", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "AND", "conditions": []},
    }
    file_path = tmp_path / "invalid_types.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f)

    result = report_service.preview_strategy_json(str(file_path))

    assert result["passed"] is False
    assert "Field 'name' must be a non-empty string." in result["errors"]
    assert "Field 'provenance' must be an object if provided." in result["errors"]
    assert "Block 'long_entry' logic must be 'AND' or 'OR'." in result["errors"]
    assert any("field 'indicator' must be a non-empty string" in e for e in result["errors"])
    assert any("field 'params' must be an object" in e for e in result["errors"])
    assert any("field 'operator' must be '>' or '<'" in e for e in result["errors"])


def test_preview_rejects_non_object_root(report_service, tmp_path):
    file_path = tmp_path / "list_root.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump([], f)

    result = report_service.preview_strategy_json(str(file_path))

    assert result["passed"] is False
    assert "JSON root must be an object." in result["errors"]

def test_json_import_preview_preserves_condition_timeframe(report_service, tmp_path):
    valid_data = {
        "name": "Test MTF Strat",
        "provenance": {},
        "long_entry": {
            "logic": "AND",
            "conditions": [
                {"indicator": "SMA", "params": {"period": 20, "timeframe": 15}, "operator": ">"}
            ]
        },
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []}
    }
    file_path = tmp_path / "mtf.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    result = report_service.preview_strategy_json(str(file_path))
    assert result["passed"] is True
    assert result["strategy"].long_entry.conditions[0].params["timeframe"] == 15


# ---------------------------------------------------------------------------
# Task 053B-Fix: RiskManagement JSON import validation
# ---------------------------------------------------------------------------

def test_json_import_preview_preserves_risk_management(report_service, tmp_path):
    valid_data = {
        "name": "Test RM Strat",
        "long_entry": {"logic": "AND", "conditions": []},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []},
        "risk_management": {
            "stop_loss_ticks": 10.0,
            "take_profit_pct": 0.05
        }
    }
    file_path = tmp_path / "rm.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    result = report_service.preview_strategy_json(str(file_path))
    assert result["passed"] is True
    assert result["strategy"].risk_management is not None
    assert result["strategy"].risk_management.stop_loss_ticks == 10.0
    assert result["strategy"].risk_management.take_profit_pct == 0.05

def test_json_import_preview_rejects_invalid_risk_management_types(report_service, tmp_path):
    invalid_data = {
        "name": "Test Bad RM",
        "long_entry": {"logic": "AND", "conditions": []},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []},
        "risk_management": {
            "stop_loss_ticks": "not-a-number",
            "take_profit_ticks": True
        }
    }
    file_path = tmp_path / "bad_rm.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f)
        
    result = report_service.preview_strategy_json(str(file_path))
    assert result["passed"] is False
    assert any("must be a number or null" in e for e in result["errors"])
    
    # Also explicitly test boolean rejection
    invalid_data["risk_management"] = {"stop_loss_ticks": True}
    file_path2 = tmp_path / "bad_rm_bool.json"
    with open(file_path2, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f)
        
    result2 = report_service.preview_strategy_json(str(file_path2))
    assert result2["passed"] is False
    assert any("must be a number or null" in e for e in result2["errors"])

def test_json_import_preview_rejects_negative_sl_tp(report_service, tmp_path):
    invalid_data = {
        "name": "Test Negative RM",
        "long_entry": {"logic": "AND", "conditions": []},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []},
        "risk_management": {
            "stop_loss_ticks": -5.0
        }
    }
    file_path = tmp_path / "neg_rm.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f)
        
    result = report_service.preview_strategy_json(str(file_path))
    assert result["passed"] is False
    assert any("cannot be negative" in e for e in result["errors"])

def test_json_import_preview_handles_null_risk_management(report_service, tmp_path):
    valid_data = {
        "name": "Test Null RM",
        "long_entry": {"logic": "AND", "conditions": []},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []},
        "risk_management": None
    }
    file_path = tmp_path / "null_rm.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    result = report_service.preview_strategy_json(str(file_path))
    assert result["passed"] is True
    assert result["strategy"].risk_management is not None
    assert result["strategy"].risk_management.stop_loss_ticks is None
    assert result["strategy"].risk_management.take_profit_pct is None

def test_json_import_preview_handles_missing_risk_management(report_service, tmp_path):
    valid_data = {
        "name": "Test Missing RM",
        "long_entry": {"logic": "AND", "conditions": []},
        "long_exit": {"logic": "OR", "conditions": []},
        "short_entry": {"logic": "AND", "conditions": []},
        "short_exit": {"logic": "OR", "conditions": []}
    }
    file_path = tmp_path / "missing_rm.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
        
    result = report_service.preview_strategy_json(str(file_path))
    assert result["passed"] is True
    assert result["strategy"].risk_management is not None
    assert result["strategy"].risk_management.stop_loss_ticks is None
    assert result["strategy"].risk_management.take_profit_pct is None

