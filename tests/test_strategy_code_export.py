"""Tests for Python and NinjaTrader strategy code export."""

from __future__ import annotations

from core.models.strategy import Condition, Strategy, StrategyBlock
from reports.python_exporter import export_strategy_to_python
from reports.ninjatrader_exporter import export_strategy_to_ninjatrader


def test_export_strategy_to_python_contains_disclaimer():
    strategy = Strategy(name="Test Strategy")
    code = export_strategy_to_python(strategy)
    
    assert "Research/backtesting only" in code
    assert "Not financial advice" in code
    assert "Not live trading code" in code
    assert "Test Strategy" in code


def test_export_strategy_empty_blocks_are_false():
    strategy = Strategy(name="Empty")
    code = export_strategy_to_python(strategy)
    
    assert "df['long_entry'] = False" in code
    assert "df['long_exit'] = False" in code
    assert "df['short_entry'] = False" in code
    assert "df['short_exit'] = False" in code


def test_export_strategy_with_sma():
    strategy = Strategy(
        name="SMA Strategy",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20}, operator=">")]
        )
    )
    code = export_strategy_to_python(strategy)
    
    assert "df['sma_20'] = df['close'].rolling(window=20, min_periods=20).mean()" in code
    assert "(df['close'] > df['sma_20'])" in code


def test_export_strategy_with_multiple_indicators():
    strategy = Strategy(
        name="Mixed Strategy",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="RSI", params={"period": 14}, operator=">", right=70.0)]
        ),
        long_exit=StrategyBlock(
            conditions=[Condition(indicator="MACD", params={"fast": 12, "slow": 26, "signal": 9}, operator="<")]
        ),
        short_entry=StrategyBlock(
            conditions=[Condition(indicator="ATR", params={"period": 14}, operator=">", right=2.5)]
        )
    )
    code = export_strategy_to_python(strategy)
    
    # RSI
    assert "df['rsi_14'] = 100.0 - (100.0 / (1.0 + rs_14))" in code
    assert "(df['rsi_14'] > 70.0)" in code
    
    # MACD
    assert "df['macd_line'] = ema_fast_12 - ema_slow_26" in code
    assert "(df['macd_line'] < df['macd_signal'])" in code
    
    # ATR
    assert "df['atr_14'] = true_range_14.rolling(window=14, min_periods=14).mean()" in code
    assert "(df['atr_14'] > 2.5)" in code


def test_export_strategy_unsupported_operator():
    strategy = Strategy(
        name="Bad Op",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20}, operator="==")]
        )
    )
    code = export_strategy_to_python(strategy)
    
    assert "df['long_entry'] = False  # Unsupported operator" in code


def test_export_strategy_unsupported_indicator():
    strategy = Strategy(
        name="Bad Ind",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="UNKNOWN", params={}, operator=">")]
        )
    )
    code = export_strategy_to_python(strategy)
    
    assert "# Unsupported indicator: UNKNOWN" in code
    assert "df['long_entry'] = False  # Unsupported condition" in code


def test_export_strategy_logic_and_or():
    strategy = Strategy(
        name="Logic",
        long_entry=StrategyBlock(
            logic="AND",
            conditions=[
                Condition(indicator="SMA", params={"period": 10}, operator=">"),
                Condition(indicator="SMA", params={"period": 20}, operator=">")
            ]
        ),
        long_exit=StrategyBlock(
            logic="OR",
            conditions=[
                Condition(indicator="SMA", params={"period": 10}, operator="<"),
                Condition(indicator="SMA", params={"period": 20}, operator="<")
            ]
        )
    )
    code = export_strategy_to_python(strategy)
    
    assert "df['long_entry'] = (df['close'] > df['sma_10']) & (df['close'] > df['sma_20'])" in code
    assert "df['long_exit'] = (df['close'] < df['sma_10']) | (df['close'] < df['sma_20'])" in code


def test_export_strategy_no_live_trading_keywords():
    strategy = Strategy(name="Test Clean")
    code = export_strategy_to_python(strategy)
    
    # The code should NOT contain any of the following live trading / simulation keywords
    forbidden_keywords = [
        "place_order", "broker", "submit_order", "send_order", "account",
        "position sizing", "pnl", "equity", "fill", "trade simulator"
    ]
    
    code_lower = code.lower()
    for kw in forbidden_keywords:
        assert kw not in code_lower, f"Forbidden keyword '{kw}' found in generated code!"


# --- NinjaTrader Exporter Tests ---

def test_ninjatrader_export_contains_disclaimer():
    strategy = Strategy(name="Test Strategy")
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "Research/backtesting only. Not financial advice. Not live trading code." in code
    assert "Test Strategy" in code


def test_ninjatrader_export_has_no_forbidden_order_keywords():
    strategy = Strategy(name="Test Clean")
    code = export_strategy_to_ninjatrader(strategy)
    
    # "Not live trading code" is in the disclaimer, so we strip the disclaimer line before checking
    disclaimer_line = "Research/backtesting only. Not financial advice. Not live trading code."
    code_body = code.replace(disclaimer_line, "")
    
    forbidden_keywords = [
        "enterlong", "entershort", "exitlong", "exitshort",
        "submitorder", "submitorderunmanaged", "account", "position",
        "atm", "atmstrategy", "broker", "live trading"
    ]
    
    code_lower = code_body.lower()
    for kw in forbidden_keywords:
        assert kw not in code_lower, f"Forbidden keyword '{kw}' found in generated C# code!"


def test_ninjatrader_export_contains_four_boolean_blocks():
    strategy = Strategy(name="Empty Blocks")
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "bool longEntry = false;" in code
    assert "bool longExit = false;" in code
    assert "bool shortEntry = false;" in code
    assert "bool shortExit = false;" in code


def test_ninjatrader_export_sma_condition():
    strategy = Strategy(
        name="SMA Strategy",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20}, operator=">")]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "bool longEntry = (Close[0] > SMA(Close, 20)[0]);" in code


def test_ninjatrader_export_rsi_condition():
    strategy = Strategy(
        name="RSI Strategy",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="RSI", params={"period": 14}, operator=">", right=70.0)]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "bool longEntry = (RSI(14, 3)[0] > 70.0);" in code


def test_ninjatrader_export_macd_condition():
    strategy = Strategy(
        name="MACD Strategy",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="MACD", params={"fast": 12, "slow": 26, "signal": 9}, operator="<")]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "bool longEntry = (MACD(12, 26, 9)[0] < MACD(12, 26, 9).Avg[0]);" in code


def test_ninjatrader_export_atr_condition():
    strategy = Strategy(
        name="ATR Strategy",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="ATR", params={"period": 14}, operator=">", right=2.5)]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "bool longEntry = (ATR(14)[0] > 2.5);" in code


def test_ninjatrader_export_and_or_logic():
    strategy = Strategy(
        name="Logic",
        long_entry=StrategyBlock(
            logic="AND",
            conditions=[
                Condition(indicator="SMA", params={"period": 10}, operator=">"),
                Condition(indicator="SMA", params={"period": 20}, operator=">")
            ]
        ),
        long_exit=StrategyBlock(
            logic="OR",
            conditions=[
                Condition(indicator="SMA", params={"period": 10}, operator="<"),
                Condition(indicator="SMA", params={"period": 20}, operator="<")
            ]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "bool longEntry = (Close[0] > SMA(Close, 10)[0]) && (Close[0] > SMA(Close, 20)[0]);" in code
    assert "bool longExit = (Close[0] < SMA(Close, 10)[0]) || (Close[0] < SMA(Close, 20)[0]);" in code


def test_ninjatrader_export_unsupported_indicator_safe_false():
    strategy = Strategy(
        name="Bad Ind",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="UNKNOWN", params={}, operator=">")]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "false /* Unsupported indicator: UNKNOWN */" in code
    assert "bool longEntry = false /* Unsupported indicator: UNKNOWN */;" in code


def test_ninjatrader_export_unsupported_operator_safe_false():
    strategy = Strategy(
        name="Bad Op",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20}, operator="==")]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "bool longEntry = false /* Unsupported operator */;" in code


def test_ninjatrader_export_does_not_import_or_reference_broker_account_position():
    strategy = Strategy(name="Clean")
    code = export_strategy_to_ninjatrader(strategy)
    code_lower = code.lower()
    for kw in ["broker", "account", "position"]:
        assert kw not in code_lower, f"Keyword {kw} found in generated code!"


# --- Malicious Injection Tests ---

def test_ninjatrader_export_malicious_strategy_name_cannot_escape_comment():
    strategy = Strategy(name="Hax */ \n public void EnterLong() { } /*")
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "*/" not in code.split("*/", 1)[0]  # The first */ should be the one we intentionally put at the end of the comment block
    assert "public void [REDACTED]() { }" in code
    assert "\n public void" not in code


def test_ninjatrader_export_malicious_sma_period_does_not_leak_forbidden_keyword():
    strategy = Strategy(
        name="Bad SMA",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": "20) { EnterLong(); } //"}, operator=">")]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "EnterLong" not in code
    # Falls back to 20
    assert "SMA(Close, 20)[0]" in code


def test_ninjatrader_export_malicious_rsi_threshold_does_not_leak_forbidden_keyword():
    strategy = Strategy(
        name="Bad RSI",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="RSI", params={"period": 14}, operator=">", right="70) { EnterLong(); } //")]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "EnterLong" not in code
    # Falls back to 0.0
    assert "RSI(14, 3)[0] > 0.0" in code


def test_ninjatrader_export_malicious_macd_params_do_not_leak_forbidden_keyword():
    strategy = Strategy(
        name="Bad MACD",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="MACD", params={"fast": "12); EnterLong(); //"}, operator=">")]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "EnterLong" not in code
    assert "MACD(12, 26, 9)" in code


def test_ninjatrader_export_malicious_unsupported_indicator_comment_is_sanitized():
    strategy = Strategy(
        name="Bad Ind",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="Hax */ EnterLong(); /*", params={}, operator=">")]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "EnterLong" not in code
    assert "[REDACTED]" in code


def test_ninjatrader_export_malicious_operator_comment_is_sanitized():
    strategy = Strategy(
        name="Bad Op",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20}, operator="*/ EnterLong(); /*")]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "EnterLong" not in code
    assert "Unsupported operator" in code


def test_ninjatrader_export_forbidden_keywords_absent_for_malicious_strategy():
    strategy = Strategy(
        name="Hax */ EnterLong() SubmitOrder() Account Position ATM broker live trading /*",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="Hax */ EnterLong() /*", params={"period": "EnterLong()"}, operator=">")]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    
    disclaimer_line = "Research/backtesting only. Not financial advice. Not live trading code."
    code_body = code.replace(disclaimer_line, "")
    
    forbidden_keywords = [
        "enterlong", "entershort", "exitlong", "exitshort",
        "submitorder", "submitorderunmanaged", "account", "position",
        "atm", "atmstrategy", "broker", "live trading"
    ]
    code_lower = code_body.lower()
    for kw in forbidden_keywords:
        assert kw not in code_lower, f"Forbidden keyword '{kw}' found in generated code despite sanitization!"


def test_ninjatrader_export_invalid_numeric_params_fallback_to_safe_defaults():
    strategy = Strategy(
        name="Fallbacks",
        long_entry=StrategyBlock(
            conditions=[
                Condition(indicator="SMA", params={"period": -5}, operator=">"),
                Condition(indicator="RSI", params={"period": 0}, operator=">", right="foo"),
                Condition(indicator="MACD", params={"fast": "x", "slow": -1, "signal": None}, operator=">"),
                Condition(indicator="ATR", params={"period": -10}, operator=">", right="bar"),
            ]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    
    assert "SMA(Close, 20)[0]" in code
    assert "RSI(14, 3)[0] > 0.0" in code
    assert "MACD(12, 26, 9)" in code
    assert "ATR(14)[0] > 0.0" in code


def test_ninjatrader_export_nan_threshold_falls_back_to_default():
    strategy = Strategy(
        name="NaN Right",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="RSI", params={"period": 14}, operator=">", right=float("nan"))]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    assert "RSI(14, 3)[0] > 0.0" in code


def test_ninjatrader_export_inf_threshold_falls_back_to_default():
    strategy = Strategy(
        name="Inf Right",
        long_entry=StrategyBlock(
            conditions=[
                Condition(indicator="RSI", params={"period": 14}, operator=">", right=float("inf")),
                Condition(indicator="ATR", params={"period": 14}, operator=">", right=float("-inf"))
            ]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    assert "RSI(14, 3)[0] > 0.0" in code
    assert "ATR(14)[0] > 0.0" in code


def test_ninjatrader_export_reference_only_comment_present():
    strategy = Strategy(name="Comment Check")
    code = export_strategy_to_ninjatrader(strategy)
    
    # Check for the mandatory disclaimer at the top
    assert "Research/backtesting only. Not financial advice. Not live trading code." in code
    
    # Check for the inner safety comment inside OnBarUpdate
    assert "// This code is provided strictly as a reference for condition logic." in code
    assert "// It intentionally omits order execution and trade management." in code


def test_ninjatrader_export_forbidden_keywords_absent_after_final_polish():
    strategy = Strategy(
        name="Final Polish Test",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20}, operator=">")]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    
    # Strip the mandatory disclaimer to verify the rest of the file
    disclaimer_line = "Research/backtesting only. Not financial advice. Not live trading code."
    code_body = code.replace(disclaimer_line, "")
    
    forbidden_keywords = [
        "enterlong", "entershort", "exitlong", "exitshort",
        "submitorder", "submitorderunmanaged", "account", "position",
        "atm", "atmstrategy", "broker", "live trading"
    ]
    
    code_lower = code_body.lower()
    for kw in forbidden_keywords:
        assert kw not in code_lower, f"Forbidden keyword '{kw}' found in generated output!"


# --- Report Service Export Routing Tests ---

def test_report_service_export_strategy_code_py_still_python(tmp_path):
    from app.services.report_service import ReportService
    service = ReportService()
    strategy = Strategy(name="Py Test")
    
    file_path = tmp_path / "test_strat.py"
    service.export_strategy_code(strategy, str(file_path))
    
    content = file_path.read_text(encoding="utf-8")
    assert "Strategy Name: Py Test" in content
    assert "def generate_signals" in content


def test_report_service_export_strategy_code_cs_uses_ninjatrader(tmp_path):
    from app.services.report_service import ReportService
    service = ReportService()
    strategy = Strategy(name="CS Test")
    
    file_path = tmp_path / "test_strat.cs"
    service.export_strategy_code(strategy, str(file_path))
    
    content = file_path.read_text(encoding="utf-8")
    assert "public class ExportedResearchStrategy : Strategy" in content
    assert "bool longEntry =" in content
    assert "def generate_signals" not in content


def test_report_service_export_strategy_code_cs_contains_disclaimer(tmp_path):
    from app.services.report_service import ReportService
    service = ReportService()
    strategy = Strategy(name="CS Test")
    
    file_path = tmp_path / "test_strat.cs"
    service.export_strategy_code(strategy, str(file_path))
    
    content = file_path.read_text(encoding="utf-8")
    assert "Research/backtesting only. Not financial advice. Not live trading code." in content


def test_report_service_export_strategy_code_cs_has_no_forbidden_keywords(tmp_path):
    from app.services.report_service import ReportService
    service = ReportService()
    strategy = Strategy(
        name="Malicious EnterLong() Account broker Position",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20}, operator=">")]
        )
    )
    
    file_path = tmp_path / "test_strat.cs"
    service.export_strategy_code(strategy, str(file_path))
    
    content = file_path.read_text(encoding="utf-8")
    disclaimer_line = "Research/backtesting only. Not financial advice. Not live trading code."
    code_body = content.replace(disclaimer_line, "")
    
    forbidden_keywords = [
        "enterlong", "entershort", "exitlong", "exitshort",
        "submitorder", "submitorderunmanaged", "account", "position",
        "atm", "atmstrategy", "broker", "live trading"
    ]
    
    code_lower = code_body.lower()
    for kw in forbidden_keywords:
        assert kw not in code_lower, f"Forbidden keyword '{kw}' found in exported CS file!"


def test_report_service_export_strategy_code_cs_does_not_affect_python_export(tmp_path):
    from app.services.report_service import ReportService
    service = ReportService()
    strategy = Strategy(name="Mixed Test")
    
    py_path = tmp_path / "test_strat.py"
    cs_path = tmp_path / "test_strat.cs"
    
    service.export_strategy_code(strategy, str(py_path))
    service.export_strategy_code(strategy, str(cs_path))
    
    py_content = py_path.read_text(encoding="utf-8")
    cs_content = cs_path.read_text(encoding="utf-8")
    
    assert "Strategy Name: Mixed Test" in py_content
    assert "public class ExportedResearchStrategy" in cs_content


# --- Task 049F: MTF Export Safety Tests ---

def test_python_export_base_strategy_unchanged():
    strategy = Strategy(
        name="Base",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20}, operator=">")]
        )
    )
    code = export_strategy_to_python(strategy)
    assert "sma_20_tf_" not in code
    assert "Multi-timeframe reference column expected" not in code

def test_python_export_mtf_condition_references_tf_column():
    strategy = Strategy(
        name="MTF Py",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20, "timeframe": 15}, operator=">")]
        )
    )
    code = export_strategy_to_python(strategy)
    assert "(df['close'] > df['sma_20_tf_15'])" in code
    assert "df['sma_20'] =" not in code  # The base logic shouldn't evaluate here since it is MTF

def test_python_export_mtf_comment_present():
    strategy = Strategy(
        name="MTF Py Comment",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20, "timeframe": 15}, operator=">")]
        )
    )
    code = export_strategy_to_python(strategy)
    assert "# Multi-timeframe reference column expected: sma_20_tf_15" in code
    assert "# SMA(20) [TF: 15m]" in code

def test_ninjatrader_export_mtf_condition_safe_false():
    strategy = Strategy(
        name="MTF NT",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20, "timeframe": 15}, operator=">")]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    assert "bool longEntry = false /* Unsupported multi-timeframe reference; manually review. */;" in code
    assert "SMA(Close, 20)[0]" not in code

def test_ninjatrader_export_mtf_comment_present():
    strategy = Strategy(
        name="MTF NT Comment",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20, "timeframe": 15}, operator=">")]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    assert "Unsupported multi-timeframe reference; manually review." in code

def test_ninjatrader_export_mtf_still_has_no_forbidden_keywords():
    strategy = Strategy(
        name="MTF NT Forbidden",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 20, "timeframe": 15}, operator=">")]
        )
    )
    code = export_strategy_to_ninjatrader(strategy)
    disclaimer_line = "Research/backtesting only. Not financial advice. Not live trading code."
    code_body = code.replace(disclaimer_line, "")
    forbidden = ["enterlong", "submitorder", "account", "position", "atm", "broker", "live trading"]
    for kw in forbidden:
        assert kw not in code_body.lower()


def test_python_export_volume_base_behavior():
    strategy = Strategy(
        name="Vol Base",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="VOLUME", params={}, operator=">", right=1000)]
        )
    )
    code = export_strategy_to_python(strategy)
    assert "(df['volume'] > 1000.0)" in code

def test_python_export_volume_mtf_behavior():
    strategy = Strategy(
        name="Vol MTF",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="VOLUME", params={"timeframe": 15}, operator=">", right=1000)]
        )
    )
    code = export_strategy_to_python(strategy)
    assert "(df['volume_tf_15'] > 1000.0)" in code
    assert "# VOLUME [TF: 15m]" in code
    assert "# Multi-timeframe reference column expected: volume_tf_15" in code

def test_python_export_volume_sma_base_behavior():
    strategy = Strategy(
        name="Vol SMA Base",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="VOLUME_SMA", params={"period": 20}, operator=">")]
        )
    )
    code = export_strategy_to_python(strategy)
    assert "df['volume_sma_20'] = df['volume'].rolling(window=20, min_periods=20).mean()" in code
    assert "(df['volume'] > df['volume_sma_20'])" in code

def test_python_export_volume_sma_mtf_behavior():
    strategy = Strategy(
        name="Vol SMA MTF",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="VOLUME_SMA", params={"period": 20, "timeframe": 15}, operator=">")]
        )
    )
    code = export_strategy_to_python(strategy)
    assert "df['volume_sma_20'] =" not in code  # Base indicator not computed
    assert "(df['volume_tf_15'] > df['volume_sma_20_tf_15'])" in code
    assert "# VOLUME_SMA(20) [TF: 15m]" in code
    assert "# Multi-timeframe reference column expected: volume_sma_20_tf_15" in code
