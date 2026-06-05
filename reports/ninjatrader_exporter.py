"""NinjaTrader (C#) research code exporter for Strategy objects."""

from __future__ import annotations

from core.models.strategy import Strategy


import re

def _sanitize_comment_text(text: str) -> str:
    """Remove comment-breaking sequences, newlines, and forbidden keywords from strings."""
    if not isinstance(text, str):
        text = str(text)
    
    # Remove comment breaks and newlines
    text = text.replace("/*", "").replace("*/", "").replace("\n", " ").replace("\r", " ")
    
    # Redact forbidden keywords (case-insensitive)
    forbidden = [
        "enterlong", "entershort", "exitlong", "exitshort",
        "submitorder", "submitorderunmanaged", "account", "position",
        "atm", "atmstrategy", "broker", "live trading"
    ]
    for kw in forbidden:
        text = re.sub(re.escape(kw), "[REDACTED]", text, flags=re.IGNORECASE)
        
    return text.strip()


def _safe_int(val: any, default: int) -> int:
    try:
        res = int(val)
        return res if res > 0 else default
    except (TypeError, ValueError):
        return default


import math

def _safe_float(val: any, default: float) -> float:
    try:
        res = float(val)
        if math.isnan(res) or math.isinf(res):
            return default
        return res
    except (TypeError, ValueError):
        return default


def export_strategy_to_ninjatrader(strategy: Strategy) -> str:
    """Export a Strategy to a NinjaTrader/C# research pseudocode script.
    
    The resulting script strictly contains condition logic and indicator math.
    It does not contain live execution APIs.
    Includes a required disclaimer that it is for research/backtesting only.
    """
    safe_name = _sanitize_comment_text(strategy.name)

    lines = [
        "/*",
        f" * Strategy Name: {safe_name}",
        " *",
        " * Research/backtesting only. Not financial advice. Not live trading code.",
        " */",
        "",
        "namespace NinjaTrader.NinjaScript.Strategies",
        "{",
        "    public class ExportedResearchStrategy : Strategy",
        "    {",
        "        protected override void OnStateChange()",
        "        {",
        "            if (State == State.SetDefaults)",
        "            {",
        "                Description = @\"Exported from Quant Strategy Lab\";",
        "                Name = \"ExportedResearchStrategy\";",
        "                Calculate = Calculate.OnBarClose;",
        "            }",
        "            else if (State == State.Configure)",
        "            {",
        "            }",
        "        }",
        "",
        "        protected override void OnBarUpdate()",
        "        {",
        "            // This code is provided strictly as a reference for condition logic.",
        "            // It intentionally omits order execution and trade management.",
        "            if (CurrentBar < 20) return;",
        "",
    ]

    blocks = [
        ("longEntry", strategy.long_entry),
        ("longExit", strategy.long_exit),
        ("shortEntry", strategy.short_entry),
        ("shortExit", strategy.short_exit),
    ]

    for name, block in blocks:
        if not block.conditions:
            lines.append(f"            bool {name} = false;")
            continue

        cond_strs = []
        for cond in block.conditions:
            ind = str(cond.indicator).upper()
            op = cond.operator
            tf = cond.params.get("timeframe")
            
            if op not in (">", "<"):
                cond_strs.append("false /* Unsupported operator */")
                continue
                
            if tf is not None:
                cond_strs.append("false /* Unsupported multi-timeframe reference; manually review. */")
                continue

            if ind == "SMA":
                p = _safe_int(cond.params.get("period", 20), 20)
                cond_strs.append(f"(Close[0] {op} SMA(Close, {p})[0])")
            elif ind == "RSI":
                p = _safe_int(cond.params.get("period", 14), 14)
                thresh = _safe_float(cond.right, 0.0)
                cond_strs.append(f"(RSI({p}, 3)[0] {op} {thresh})")
            elif ind == "MACD":
                fast = _safe_int(cond.params.get("fast", 12), 12)
                slow = _safe_int(cond.params.get("slow", 26), 26)
                sig = _safe_int(cond.params.get("signal", 9), 9)
                cond_strs.append(f"(MACD({fast}, {slow}, {sig})[0] {op} MACD({fast}, {slow}, {sig}).Avg[0])")
            elif ind == "ATR":
                p = _safe_int(cond.params.get("period", 14), 14)
                thresh = _safe_float(cond.right, 0.0)
                cond_strs.append(f"(ATR({p})[0] {op} {thresh})")
            else:
                safe_ind = _sanitize_comment_text(ind)
                cond_strs.append(f"false /* Unsupported indicator: {safe_ind} */")

        logic_op = " && " if block.logic.upper() == "AND" else " || "
        combined = logic_op.join(cond_strs)
        lines.append(f"            bool {name} = {combined};")

    lines.extend([
        "        }",
        "    }",
        "}",
        ""
    ])

    return "\n".join(lines)
