"""Strategy serialization helper."""

from core.models.strategy import Strategy, RiskManagement, StrategyBlock, Condition
from typing import Any

class SerializationError(ValueError):
    """Raised when strict parsing fails."""
    pass


def risk_management_from_dict(payload: Any, *, strict: bool) -> RiskManagement:
    """
    Parses RiskManagement rules.
    If strict=True (e.g., JSON import), raises SerializationError for validation errors.
    If strict=False (e.g., DB load), fails safe to RiskManagement().
    """
    if payload is None:
        return RiskManagement()
        
    if not isinstance(payload, dict):
        if strict:
            raise SerializationError("Field 'risk_management' must be an object or null.")
        return RiskManagement()
        
    rm_kwargs = {}
    valid_keys = ["stop_loss_ticks", "take_profit_ticks", "stop_loss_pct", "take_profit_pct"]
    
    for f in valid_keys:
        val = payload.get(f)
        if val is not None:
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                if strict:
                    raise SerializationError(f"RiskManagement field '{f}' must be a number or null.")
                continue
            if val < 0:
                if strict:
                    raise SerializationError(f"RiskManagement field '{f}' cannot be negative.")
                continue
            rm_kwargs[f] = float(val)
            
    return RiskManagement(**rm_kwargs)


def _condition_from_dict(d: dict, strict: bool) -> Condition:
    if not isinstance(d, dict):
        if strict:
            raise SerializationError("Condition must be a dictionary")
        d = {}
    return Condition(
        indicator=d.get("indicator", "SMA"),
        params=d.get("params", {}),
        operator=d.get("operator", ">"),
        left=d.get("left", "close"),
        right=d.get("right", 0.0)
    )


def _block_from_dict(d: dict, strict: bool) -> StrategyBlock:
    if not isinstance(d, dict):
        if strict:
            raise SerializationError("StrategyBlock must be a dictionary")
        return StrategyBlock()
        
    conds = []
    for c in d.get("conditions", []):
        try:
            conds.append(_condition_from_dict(c, strict))
        except SerializationError:
            if strict:
                raise
                
    return StrategyBlock(
        conditions=conds,
        logic=d.get("logic", "AND")
    )


def strategy_from_dict(payload: dict, *, strict: bool = False, source: str = "unknown") -> Strategy:
    """Parses a Strategy from a dictionary, delegating sub-components like RiskManagement."""
    if not isinstance(payload, dict):
        if strict:
            raise SerializationError("Strategy payload must be a dictionary")
        return Strategy(name="Invalid Strategy")
        
    name = payload.get("name", "Unknown Strategy")
    if not name and strict:
        # Strict mode might enforce a non-empty name, but for now we fallback
        name = "Unknown Strategy"
        
    le = _block_from_dict(payload.get("long_entry", {}), strict)
    lx = _block_from_dict(payload.get("long_exit", {}), strict)
    se = _block_from_dict(payload.get("short_entry", {}), strict)
    sx = _block_from_dict(payload.get("short_exit", {}), strict)
    
    rm = risk_management_from_dict(payload.get("risk_management"), strict=strict)
    
    return Strategy(
        name=name,
        long_entry=le,
        long_exit=lx,
        short_entry=se,
        short_exit=sx,
        risk_management=rm
    )


def _condition_to_dict(c: Condition) -> dict:
    return {
        "indicator": c.indicator,
        "params": c.params,
        "operator": c.operator,
        "left": c.left,
        "right": c.right
    }


def _block_to_dict(b: StrategyBlock) -> dict:
    return {
        "logic": b.logic,
        "conditions": [_condition_to_dict(c) for c in b.conditions]
    }


def strategy_to_dict(strategy: Strategy) -> dict:
    """Serializes a Strategy to a standard dictionary payload."""
    d = {
        "name": strategy.name,
        "long_entry": _block_to_dict(strategy.long_entry),
        "long_exit": _block_to_dict(strategy.long_exit),
        "short_entry": _block_to_dict(strategy.short_entry),
        "short_exit": _block_to_dict(strategy.short_exit),
    }
    
    rm_dict = None
    rm = strategy.risk_management
    has_rm = (
        rm.stop_loss_ticks is not None or 
        rm.take_profit_ticks is not None or 
        rm.stop_loss_pct is not None or 
        rm.take_profit_pct is not None
    )
    if has_rm:
        rm_dict = {}
        if rm.stop_loss_ticks is not None: rm_dict["stop_loss_ticks"] = rm.stop_loss_ticks
        if rm.take_profit_ticks is not None: rm_dict["take_profit_ticks"] = rm.take_profit_ticks
        if rm.stop_loss_pct is not None: rm_dict["stop_loss_pct"] = rm.stop_loss_pct
        if rm.take_profit_pct is not None: rm_dict["take_profit_pct"] = rm.take_profit_pct
    
    d["risk_management"] = rm_dict
    return d
