import pytest
import os
import ast

from core.models.strategy import Condition, StrategyBlock
from strategy_engine.formula_parser import parse_formula_to_block, FormulaParseError


def test_parse_sma_condition():
    block = parse_formula_to_block("close > SMA(20)")
    assert block.logic == "AND"
    assert len(block.conditions) == 1
    c = block.conditions[0]
    assert c.indicator == "SMA"
    assert c.params == {"period": 20}
    assert c.operator == ">"
    assert c.left == "close"

def test_parse_rsi_condition():
    block = parse_formula_to_block("RSI(14) < 30")
    c = block.conditions[0]
    assert c.indicator == "RSI"
    assert c.params == {"period": 14}
    assert c.operator == "<"
    assert c.right == 30.0

def test_parse_macd_condition():
    block = parse_formula_to_block("MACD(12,26,9) > signal")
    c = block.conditions[0]
    assert c.indicator == "MACD"
    assert c.params == {"fast": 12, "slow": 26, "signal": 9}
    assert c.operator == ">"

def test_parse_atr_condition():
    block = parse_formula_to_block("ATR(14) > 2.5")
    c = block.conditions[0]
    assert c.indicator == "ATR"
    assert c.params == {"period": 14}
    assert c.operator == ">"
    assert c.right == 2.5

def test_parse_volume_threshold_condition():
    block = parse_formula_to_block("volume > 1000")
    c = block.conditions[0]
    assert c.indicator == "VOLUME"
    assert c.params == {}
    assert c.operator == ">"
    assert c.left == "volume"
    assert c.right == 1000.0

def test_parse_volume_sma_multiplier_condition():
    block = parse_formula_to_block("volume > VOLUME_SMA(20) * 1.5")
    c = block.conditions[0]
    assert c.indicator == "VOLUME_SMA"
    assert c.params == {"period": 20}
    assert c.operator == ">"
    assert c.left == "volume"
    assert c.right == 1.5

def test_parse_and_conditions():
    block = parse_formula_to_block("close > SMA(20) AND RSI(14) < 30")
    assert block.logic == "AND"
    assert len(block.conditions) == 2
    assert block.conditions[0].indicator == "SMA"
    assert block.conditions[1].indicator == "RSI"

def test_parse_or_conditions():
    block = parse_formula_to_block("volume > 1000 OR ATR(14) > 2.5")
    assert block.logic == "OR"
    assert len(block.conditions) == 2
    assert block.conditions[0].indicator == "VOLUME"
    assert block.conditions[1].indicator == "ATR"

def test_parse_mixed_and_or_rejected():
    with pytest.raises(FormulaParseError, match="Mixed AND/OR"):
        parse_formula_to_block("close > SMA(20) AND RSI(14) < 30 OR volume > 1000")

def test_parse_eval_exec_rejected():
    with pytest.raises(FormulaParseError, match="Dangerous tokens"):
        parse_formula_to_block("eval('import os')")
    with pytest.raises(FormulaParseError, match="Dangerous tokens"):
        parse_formula_to_block("exec('print(1)')")

def test_parse_unknown_indicator_rejected():
    with pytest.raises(FormulaParseError, match="Unsupported condition syntax"):
        parse_formula_to_block("close > EMA(20)")

def test_parse_arbitrary_python_rejected():
    with pytest.raises(FormulaParseError, match="Unsupported condition syntax"):
        parse_formula_to_block("close > SMA(20) + SMA(10)")

def test_formula_parser_has_no_eval_exec_usage():
    import strategy_engine.formula_parser
    parser_path = strategy_engine.formula_parser.__file__
    with open(parser_path, "r", encoding="utf-8") as f:
        source = f.read()
    
    # We parse the AST of the formula parser to verify it doesn't call eval or exec
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in ("eval", "exec"), f"Found forbidden {node.func.id} call in parser!"
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in ("eval", "exec"), f"Found forbidden attribute call in parser!"

def test_formula_parser_rejects_dangerous_keywords():
    dangerous = ["import os", "open('file.txt')", "sys.exit", "subprocess.call", "lambda x: x", "while True:", "for i in range"]
    for d in dangerous:
        with pytest.raises(FormulaParseError):
            parse_formula_to_block(d)

def test_formula_parser_rejects_dunder():
    with pytest.raises(FormulaParseError, match="Dangerous tokens"):
        parse_formula_to_block("__import__('os')")

def test_formula_parser_rejects_invalid_period_zero():
    with pytest.raises(FormulaParseError):
        parse_formula_to_block("close > SMA(0)")

def test_formula_parser_rejects_invalid_period_negative():
    # regex won't even match negative, it'll raise Unsupported condition syntax
    with pytest.raises(FormulaParseError):
        parse_formula_to_block("close > SMA(-5)")

def test_formula_parser_rejects_macd_fast_greater_equal_slow():
    with pytest.raises(FormulaParseError, match="fast period must be strictly less than slow"):
        parse_formula_to_block("MACD(26,12,9) > signal")
    with pytest.raises(FormulaParseError, match="fast period must be strictly less than slow"):
        parse_formula_to_block("MACD(26,26,9) > signal")

def test_formula_parser_rejects_volume_sma_nonpositive_multiplier():
    # regex matches floats, but -1.5 won't match the regex. 0.0 matches regex but fails validation
    with pytest.raises(FormulaParseError, match="multiplier must be strictly positive"):
        parse_formula_to_block("volume > VOLUME_SMA(20) * 0.0")

def test_formula_parser_rejects_unsupported_math():
    with pytest.raises(FormulaParseError):
        parse_formula_to_block("RSI(14) > 70 + 5")

def test_formula_parser_empty_formula_rejected():
    with pytest.raises(FormulaParseError):
        parse_formula_to_block("")
    with pytest.raises(FormulaParseError):
        parse_formula_to_block("   ")

def test_formula_parser_rejects_trailing_garbage():
    with pytest.raises(FormulaParseError, match="Unsupported condition syntax"):
        parse_formula_to_block("close > SMA(20) garbage")

def test_formula_parser_rejects_semicolon_payload():
    with pytest.raises(FormulaParseError):
        parse_formula_to_block("close > SMA(20); import os")

def test_formula_parser_rejects_newline_payload():
    with pytest.raises(FormulaParseError):
        parse_formula_to_block("close > SMA(20)\nimport os")

def test_formula_parser_rejects_case_mixed_dangerous_tokens():
    with pytest.raises(FormulaParseError, match="Dangerous tokens"):
        parse_formula_to_block("close > SMA(20) OR ImPoRt OS")
    with pytest.raises(FormulaParseError, match="Dangerous tokens"):
        parse_formula_to_block("EvAl('os')")

def test_formula_parser_rejects_comment_payload():
    with pytest.raises(FormulaParseError):
        parse_formula_to_block("close > SMA(20) # import os")

def test_formula_parser_uses_full_match_not_partial_match():
    # Because of ^ and $, it shouldn't match partial strings
    with pytest.raises(FormulaParseError, match="Unsupported condition syntax"):
        parse_formula_to_block("some close > SMA(20)")

def test_formula_parser_outputs_exact_condition_fields_for_all_supported_types():
    # Re-verifying exactly what's expected for evaluator mapping
    block = parse_formula_to_block("close > SMA(20) AND RSI(14) < 30")
    
    cond1 = block.conditions[0]
    assert cond1.indicator == "SMA"
    assert cond1.params == {"period": 20}
    assert cond1.operator == ">"
    assert cond1.left == "close"
    
    cond2 = block.conditions[1]
    assert cond2.indicator == "RSI"
    assert cond2.params == {"period": 14}
    assert cond2.operator == "<"
    assert cond2.right == 30.0
