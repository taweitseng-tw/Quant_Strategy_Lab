"""Formula Parser — Safely parse simple string formulas into StrategyBlock/Condition.

This parser strictly uses regular expressions and string matching.
It does NOT use eval(), exec(), or ast.parse().
Arbitrary code execution is impossible by design.
"""

from __future__ import annotations

import re

from core.models.strategy import Condition, StrategyBlock


class FormulaParseError(Exception):
    """Raised when a formula cannot be parsed safely."""
    pass


# Strict regex patterns
# SMA: close > SMA(20)
SMA_PATTERN = re.compile(r"^\s*close\s*([<>])\s*SMA\s*\(\s*(\d+)\s*\)\s*$", re.IGNORECASE)
# RSI: RSI(14) > 70
RSI_PATTERN = re.compile(r"^\s*RSI\s*\(\s*(\d+)\s*\)\s*([<>])\s*([0-9.]+)\s*$", re.IGNORECASE)
# MACD: MACD(12,26,9) > signal
MACD_PATTERN = re.compile(r"^\s*MACD\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)\s*([<>])\s*signal\s*$", re.IGNORECASE)
# ATR: ATR(14) > 2.5
ATR_PATTERN = re.compile(r"^\s*ATR\s*\(\s*(\d+)\s*\)\s*([<>])\s*([0-9.]+)\s*$", re.IGNORECASE)
# VOLUME: volume > 1000
VOLUME_PATTERN = re.compile(r"^\s*volume\s*([<>])\s*([0-9.]+)\s*$", re.IGNORECASE)
# VOLUME_SMA: volume > VOLUME_SMA(20) * 1.5
VOLUME_SMA_PATTERN = re.compile(r"^\s*volume\s*([<>])\s*VOLUME_SMA\s*\(\s*(\d+)\s*\)\s*\*\s*([0-9.]+)\s*$", re.IGNORECASE)


def parse_condition(cond_str: str) -> Condition:
    """Parse a single condition string into a Condition object."""
    cond_str = cond_str.strip()
    if not cond_str:
        raise FormulaParseError("Empty condition string.")

    # SMA
    match = SMA_PATTERN.match(cond_str)
    if match:
        op = match.group(1)
        period = int(match.group(2))
        _validate_period(period)
        return Condition(indicator="SMA", params={"period": period}, operator=op, left="close")

    # RSI
    match = RSI_PATTERN.match(cond_str)
    if match:
        period = int(match.group(1))
        _validate_period(period)
        op = match.group(2)
        right = float(match.group(3))
        return Condition(indicator="RSI", params={"period": period}, operator=op, right=right)

    # MACD
    match = MACD_PATTERN.match(cond_str)
    if match:
        fast = int(match.group(1))
        slow = int(match.group(2))
        signal = int(match.group(3))
        _validate_period(fast)
        _validate_period(slow)
        _validate_period(signal)
        if fast >= slow:
            raise FormulaParseError("MACD fast period must be strictly less than slow period.")
        op = match.group(4)
        return Condition(indicator="MACD", params={"fast": fast, "slow": slow, "signal": signal}, operator=op)

    # ATR
    match = ATR_PATTERN.match(cond_str)
    if match:
        period = int(match.group(1))
        _validate_period(period)
        op = match.group(2)
        right = float(match.group(3))
        return Condition(indicator="ATR", params={"period": period}, operator=op, right=right)
        
    # VOLUME_SMA (must check before VOLUME to avoid partial match)
    match = VOLUME_SMA_PATTERN.match(cond_str)
    if match:
        op = match.group(1)
        period = int(match.group(2))
        _validate_period(period)
        multiplier = float(match.group(3))
        if multiplier <= 0:
            raise FormulaParseError("VOLUME_SMA multiplier must be strictly positive.")
        return Condition(indicator="VOLUME_SMA", params={"period": period}, operator=op, left="volume", right=multiplier)

    # VOLUME
    match = VOLUME_PATTERN.match(cond_str)
    if match:
        op = match.group(1)
        right = float(match.group(2))
        return Condition(indicator="VOLUME", params={}, operator=op, left="volume", right=right)

    # If we fall through, the syntax or indicator is unsupported.
    raise FormulaParseError(f"Unsupported condition syntax or unknown token: '{cond_str}'")


def _validate_period(period: int) -> None:
    if period <= 0:
        raise FormulaParseError("Period must be strictly positive.")


def _contains_dangerous_tokens(formula: str) -> bool:
    """Pre-scan to aggressively reject any suspicious Python tokens."""
    f_lower = formula.lower()
    if "__" in f_lower:
        return True
    
    # We use word boundaries to avoid matching "os" inside "close"
    dangerous_pattern = r"\b(import|eval|exec|open|os|sys|subprocess|lambda|while|for|class|def|compile)\b"
    if re.search(dangerous_pattern, f_lower):
        return True
    
    return False


def parse_formula_to_block(formula: str) -> StrategyBlock:
    """Parse a formula string into a StrategyBlock containing Condition objects.
    
    Supports single conditions or multiple conditions joined by AND / OR.
    Raises FormulaParseError for any invalid syntax, logic, or unsupported tokens.
    """
    if not isinstance(formula, str):
        raise FormulaParseError("Formula must be a string.")
        
    formula = formula.strip()
    if not formula:
        raise FormulaParseError("Empty formula.")
        
    if _contains_dangerous_tokens(formula):
        raise FormulaParseError("Dangerous tokens detected.")

    has_and = " AND " in formula.upper()
    has_or = " OR " in formula.upper()

    if has_and and has_or:
        raise FormulaParseError("Mixed AND/OR logic in the same formula is not supported.")

    logic = "AND"
    split_token = None

    if has_and:
        # standard python split doesn't do case-insensitive, we use re.split
        split_token = r"\s+AND\s+"
        logic = "AND"
    elif has_or:
        split_token = r"\s+OR\s+"
        logic = "OR"

    if split_token:
        parts = re.split(split_token, formula, flags=re.IGNORECASE)
    else:
        parts = [formula]
        
    conditions = []
    for part in parts:
        part = part.strip()
        if not part:
            raise FormulaParseError("Empty condition part found.")
        cond = parse_condition(part)
        conditions.append(cond)
        
    return StrategyBlock(conditions=conditions, logic=logic)
