"""Python research code exporter for Strategy objects."""

from __future__ import annotations

from core.models.strategy import Strategy


def export_strategy_to_python(strategy: Strategy) -> str:
    """Export a Strategy to a pandas-based Python research script.
    
    The resulting script computes necessary indicators and evaluates the
    four strategy blocks (long_entry, long_exit, short_entry, short_exit).
    It includes a required disclaimer that it is for research/backtesting only.
    """
    lines = [
        '"""',
        f'Strategy Name: {strategy.name}',
        '',
        'Research/backtesting only. Not financial advice. Not live trading code.',
        '"""',
        '',
        'import pandas as pd',
        'import numpy as np',
        '',
        '',
        'def generate_signals(df: pd.DataFrame) -> pd.DataFrame:',
        '    """Generate trading signals for the strategy.',
        '    ',
        "    Expects a DataFrame with 'open', 'high', 'low', 'close', 'volume' columns.",
        '    Returns a copy of the DataFrame with signal columns added.',
        '    """',
        '    df = df.copy()',
        '',
    ]

    indicators_code = []
    seen_indicators = set()

    blocks = [
        ("long_entry", strategy.long_entry),
        ("long_exit", strategy.long_exit),
        ("short_entry", strategy.short_entry),
        ("short_exit", strategy.short_exit),
    ]

    # Pre-compute required indicators
    for name, block in blocks:
        for cond in block.conditions:
            ind = cond.indicator.upper()
            tf = cond.params.get("timeframe")
            if ind == "SMA":
                p = cond.params.get("period", 20)
                if tf is not None:
                    key = f"SMA_{p}_TF_{tf}"
                    if key not in seen_indicators:
                        indicators_code.extend([
                            f"    # SMA({p}) [TF: {tf}m]",
                            f"    # Multi-timeframe reference column expected: sma_{p}_tf_{tf}",
                        ])
                        seen_indicators.add(key)
                else:
                    key = f"SMA_{p}"
                    if key not in seen_indicators:
                        indicators_code.extend([
                            f"    # SMA({p})",
                            f"    df['sma_{p}'] = df['close'].rolling(window={p}, min_periods={p}).mean()",
                        ])
                        seen_indicators.add(key)
            elif ind == "RSI":
                p = cond.params.get("period", 14)
                if tf is not None:
                    key = f"RSI_{p}_TF_{tf}"
                    if key not in seen_indicators:
                        indicators_code.extend([
                            f"    # RSI({p}) [TF: {tf}m]",
                            f"    # Multi-timeframe reference column expected: rsi_{p}_tf_{tf}",
                        ])
                        seen_indicators.add(key)
                else:
                    key = f"RSI_{p}"
                    if key not in seen_indicators:
                        indicators_code.extend([
                            f"    # RSI({p})",
                            f"    delta_{p} = df['close'].diff()",
                            f"    gain_{p} = delta_{p}.clip(lower=0)",
                            f"    loss_{p} = (-delta_{p}).clip(lower=0)",
                            f"    avg_gain_{p} = gain_{p}.rolling(window={p}, min_periods={p}).mean()",
                            f"    avg_loss_{p} = loss_{p}.rolling(window={p}, min_periods={p}).mean()",
                            f"    rs_{p} = avg_gain_{p} / avg_loss_{p}.replace(0, np.nan)",
                            f"    df['rsi_{p}'] = 100.0 - (100.0 / (1.0 + rs_{p}))",
                        ])
                        seen_indicators.add(key)
            elif ind == "MACD":
                fast = cond.params.get("fast", 12)
                slow = cond.params.get("slow", 26)
                sig = cond.params.get("signal", 9)
                if tf is not None:
                    key = f"MACD_{fast}_{slow}_{sig}_TF_{tf}"
                    if key not in seen_indicators:
                        indicators_code.extend([
                            f"    # MACD({fast}, {slow}, {sig}) [TF: {tf}m]",
                            f"    # Multi-timeframe reference columns expected: macd_line_tf_{tf}, macd_signal_tf_{tf}",
                        ])
                        seen_indicators.add(key)
                else:
                    key = f"MACD_{fast}_{slow}_{sig}"
                    if key not in seen_indicators:
                        indicators_code.extend([
                            f"    # MACD({fast}, {slow}, {sig})",
                            f"    ema_fast_{fast} = df['close'].ewm(span={fast}, min_periods={fast}, adjust=False).mean()",
                            f"    ema_slow_{slow} = df['close'].ewm(span={slow}, min_periods={slow}, adjust=False).mean()",
                            f"    df['macd_line'] = ema_fast_{fast} - ema_slow_{slow}",
                            f"    df['macd_signal'] = df['macd_line'].ewm(span={sig}, min_periods={sig}, adjust=False).mean()",
                        ])
                        seen_indicators.add(key)
            elif ind == "ATR":
                p = cond.params.get("period", 14)
                if tf is not None:
                    key = f"ATR_{p}_TF_{tf}"
                    if key not in seen_indicators:
                        indicators_code.extend([
                            f"    # ATR({p}) [TF: {tf}m]",
                            f"    # Multi-timeframe reference column expected: atr_{p}_tf_{tf}",
                        ])
                        seen_indicators.add(key)
                else:
                    key = f"ATR_{p}"
                    if key not in seen_indicators:
                        indicators_code.extend([
                            f"    # ATR({p})",
                            f"    prev_close_{p} = df['close'].shift(1)",
                            f"    tr1_{p} = df['high'] - df['low']",
                            f"    tr2_{p} = (df['high'] - prev_close_{p}).abs()",
                            f"    tr3_{p} = (df['low'] - prev_close_{p}).abs()",
                            f"    true_range_{p} = pd.concat([tr1_{p}, tr2_{p}, tr3_{p}], axis=1).max(axis=1)",
                            f"    df['atr_{p}'] = true_range_{p}.rolling(window={p}, min_periods={p}).mean()",
                        ])
                        seen_indicators.add(key)
            elif ind == "VOLUME":
                if tf is not None:
                    key = f"VOLUME_TF_{tf}"
                    if key not in seen_indicators:
                        indicators_code.extend([
                            f"    # VOLUME [TF: {tf}m]",
                            f"    # Multi-timeframe reference column expected: volume_tf_{tf}",
                        ])
                        seen_indicators.add(key)
                else:
                    pass  # base volume is already present in DataFrame
            elif ind == "VOLUME_SMA":
                p = cond.params.get("period", 20)
                if tf is not None:
                    key = f"VOLUME_SMA_{p}_TF_{tf}"
                    if key not in seen_indicators:
                        indicators_code.extend([
                            f"    # VOLUME_SMA({p}) [TF: {tf}m]",
                            f"    # Multi-timeframe reference column expected: volume_sma_{p}_tf_{tf}",
                        ])
                        seen_indicators.add(key)
                else:
                    key = f"VOLUME_SMA_{p}"
                    if key not in seen_indicators:
                        indicators_code.extend([
                            f"    # VOLUME_SMA({p})",
                            f"    df['volume_sma_{p}'] = df['volume'].rolling(window={p}, min_periods={p}).mean()",
                        ])
                        seen_indicators.add(key)
            else:
                indicators_code.append(f"    # Unsupported indicator: {ind}" + (f" [TF: {tf}m]" if tf is not None else ""))

    if indicators_code:
        lines.append("    # --- Indicators ---")
        lines.extend(indicators_code)
        lines.append("")

    lines.append("    # --- Signal Blocks ---")
    for name, block in blocks:
        if not block.conditions:
            lines.append(f"    df['{name}'] = False")
            continue

        cond_strs = []
        for cond in block.conditions:
            ind = cond.indicator.upper()
            op = cond.operator
            tf = cond.params.get("timeframe")
            if op not in (">", "<"):
                cond_strs.append("False  # Unsupported operator")
                continue

            if ind == "SMA":
                p = cond.params.get("period", 20)
                col = f"sma_{p}_tf_{tf}" if tf is not None else f"sma_{p}"
                cond_strs.append(f"(df['close'] {op} df['{col}'])")
            elif ind == "RSI":
                p = cond.params.get("period", 14)
                try:
                    thresh = float(cond.right)
                except (TypeError, ValueError):
                    thresh = 0.0
                col = f"rsi_{p}_tf_{tf}" if tf is not None else f"rsi_{p}"
                cond_strs.append(f"(df['{col}'] {op} {thresh})")
            elif ind == "MACD":
                col_line = f"macd_line_tf_{tf}" if tf is not None else "macd_line"
                col_sig = f"macd_signal_tf_{tf}" if tf is not None else "macd_signal"
                cond_strs.append(f"(df['{col_line}'] {op} df['{col_sig}'])")
            elif ind == "ATR":
                p = cond.params.get("period", 14)
                try:
                    thresh = float(cond.right)
                except (TypeError, ValueError):
                    thresh = 0.0
                col = f"atr_{p}_tf_{tf}" if tf is not None else f"atr_{p}"
                cond_strs.append(f"(df['{col}'] {op} {thresh})")
            elif ind == "VOLUME":
                try:
                    thresh = float(cond.right)
                except (TypeError, ValueError):
                    thresh = 0.0
                col = f"volume_tf_{tf}" if tf is not None else "volume"
                cond_strs.append(f"(df['{col}'] {op} {thresh})")
            elif ind == "VOLUME_SMA":
                p = cond.params.get("period", 20)
                col = f"volume_sma_{p}_tf_{tf}" if tf is not None else f"volume_sma_{p}"
                col_vol = f"volume_tf_{tf}" if tf is not None else "volume"
                cond_strs.append(f"(df['{col_vol}'] {op} df['{col}'])")
            else:
                cond_strs.append("False  # Unsupported condition")

        logic_op = " & " if block.logic.upper() == "AND" else " | "
        combined = logic_op.join(cond_strs)
        lines.append(f"    df['{name}'] = {combined}")

    lines.append("")
    lines.append("    return df")
    lines.append("")

    return "\n".join(lines)
