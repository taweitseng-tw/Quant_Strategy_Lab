"""Report generation engine — formats backtest results into Markdown and HTML reports."""

from __future__ import annotations

import html
import logging
from datetime import datetime
import pandas as pd

from core.models.strategy import Strategy, StrategyBlock
from core.models.backtest_result import BacktestResult, Trade

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.services.multi_instrument_service import MultiInstrumentBacktestResult

# Set up logging
logger = logging.getLogger(__name__)


def format_block_desc(block: StrategyBlock) -> str:
    """Format a StrategyBlock conditions list into a readable description string."""
    if not block.conditions:
        return "Inactive"
    
    cond_strs = []
    for c in block.conditions:
        tf = c.params.get("timeframe")
        params_str = ", ".join(f"{k}={v}" for k, v in c.params.items() if k != "timeframe")
        
        base_str = f"{c.left} {c.operator} {c.indicator}({params_str})"
        if tf is not None:
            base_str += f" [TF: {tf}m]"
            
        cond_strs.append(base_str)
        
    return f" {block.logic} ".join(cond_strs)


def generate_markdown_report(
    strategy: Strategy,
    result: BacktestResult,
    provenance: dict | None = None,
    is_mock: bool = False,
    validation_result: dict | None = None,
    multi_instrument_result: "MultiInstrumentBacktestResult" | None = None,
) -> str:
    """Generate a clean, highly structured Markdown report of the backtest result."""
    # Metadata extraction
    prov = provenance or {}
    gen_version = prov.get("generator_version", "N/A")
    seed = prov.get("random_seed", "N/A")
    rule_versions = ", ".join(f"{k}: {v}" for k, v in prov.get("rule_block_versions", {}).items()) or "N/A"
    generated_at = prov.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Metrics
    m = result.metrics
    total_pnl = m.get("total_pnl", 0.0)
    profit_factor = m.get("profit_factor", 0.0)
    max_drawdown = m.get("max_drawdown_pnl", 0.0)
    win_rate = m.get("win_rate", 0.0)
    total_trades = m.get("total_trades", 0)
    winning_trades = m.get("winning_trades", 0)
    losing_trades = m.get("losing_trades", 0)
    avg_trade = m.get("avg_trade", 0.0)

    # Assumptions
    a = result.assumptions
    exec_model = a.get("execution_model", "next_bar_open")
    sig_conf = a.get("signal_confirmation", "bar_close")
    init_cap = a.get("initial_capital", 100_000.0)
    comm = a.get("commission_per_side", 0.0)
    slip = a.get("slippage_per_side_ticks", 0.0)
    tick_sz = a.get("tick_size", 1.0)

    # Strategy conditions description
    long_entry_desc = format_block_desc(strategy.long_entry)
    long_exit_desc = format_block_desc(strategy.long_exit)
    short_entry_desc = format_block_desc(strategy.short_entry)
    short_exit_desc = format_block_desc(strategy.short_exit)

    # Formatting warnings
    if result.warnings:
        warnings_str = "\n".join(f"- **WARNING**: {w}" for w in result.warnings)
    else:
        warnings_str = "*No warnings were generated during this backtest.*"

    # Formatting detailed trades table
    if not result.trades:
        trade_rows = "| *No trades were executed during this backtest.* | | | | | | | |"
    else:
        rows = []
        for i, t in enumerate(result.trades):
            entry_t = t.entry_time.strftime("%Y-%m-%d %H:%M") if hasattr(t.entry_time, "strftime") else str(t.entry_time)
            exit_t = t.exit_time.strftime("%Y-%m-%d %H:%M") if hasattr(t.exit_time, "strftime") else str(t.exit_time)
            rows.append(
                f"| {i + 1} | **{t.direction.upper()}** | {entry_t} | ${t.entry_price:,.2f} | "
                f"{exit_t} | ${t.exit_price:,.2f} | ${t.pnl:,.2f} | {t.exit_reason} |"
            )
        trade_rows = "\n".join(rows)

    title_header = "Quant Strategy Lab — Sample / Mock Report (No Project Loaded)" if is_mock else "Quant Strategy Lab — Backtest Performance Report"

    md = f"""# {title_header}

## [Financial Safety Notice]
> [!WARNING]
> This report is for research and backtesting purposes only.
> Backtested performance does not guarantee future results.

## Strategy Profile
- **Strategy Name**: `{strategy.name}`
- **Generator Version**: `{gen_version}`
- **Random Seed**: `{seed}`
- **Rule Block Versions**: `{rule_versions}`
- **Report Generated At**: `{generated_at}`

### Strategy Logic
- **Long Entry**: `{long_entry_desc}`
- **Long Exit**: `{long_exit_desc}`
- **Short Entry**: `{short_entry_desc}`
- **Short Exit**: `{short_exit_desc}`

## Performance Metrics Summary
| Metric | Value |
| :--- | :--- |
| **Total Net Profit** | **${total_pnl:,.2f}** |
| **Profit Factor** | **{"N/A" if profit_factor == 999.0 else f"{profit_factor:.2f}"}** |
| **Max Drawdown** | **${max_drawdown:,.2f}** |
| **Win Rate** | **{win_rate * 100:.1f}%** |
| **Total Trades** | **{total_trades}** |
| **Winning Trades** | {winning_trades} |
| **Losing Trades** | {losing_trades} |
| **Average Trade PnL** | ${avg_trade:,.2f} |

## Backtest Assumptions
- **Execution Model**: `{exec_model}`
- **Signal Confirmation**: `{sig_conf}`
- **Initial Capital**: `${init_cap:,.2f}`
- **Commission per Side**: `${comm:,.2f}`
- **Slippage per Side (Ticks)**: `{slip}`
- **Tick Size**: `{tick_sz}`

## Warnings & Log Items
{warnings_str}

## Detailed Transaction Log
| # | Direction | Entry Time | Entry Price | Exit Time | Exit Price | PnL | Exit Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{trade_rows}
"""
    # ── validation evidence section ──────────────────────────────────────
    if validation_result:
        md += _format_markdown_validation(validation_result)
    else:
        md += "\n## Validation Evidence\n\n*No validation evidence was included in this report.*\n"

    # ── multi-instrument evidence section ────────────────────────────────
    if multi_instrument_result:
        md += _format_markdown_multi_instrument(multi_instrument_result)

    return md


def generate_html_report(
    strategy: Strategy,
    result: BacktestResult,
    provenance: dict | None = None,
    is_mock: bool = False,
    validation_result: dict | None = None,
    multi_instrument_result: "MultiInstrumentBacktestResult" | None = None,
) -> str:
    """Generate a premium, modern, and responsive HTML backtest performance report."""
    # Metadata extraction
    prov = provenance or {}
    gen_version = prov.get("generator_version", "N/A")
    seed = prov.get("random_seed", "N/A")
    rule_versions = ", ".join(f"{k}: {v}" for k, v in prov.get("rule_block_versions", {}).items()) or "N/A"
    generated_at = prov.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Metrics
    m = result.metrics
    total_pnl = m.get("total_pnl", 0.0)
    profit_factor = m.get("profit_factor", 0.0)
    max_drawdown = m.get("max_drawdown_pnl", 0.0)
    win_rate = m.get("win_rate", 0.0)
    total_trades = m.get("total_trades", 0)
    winning_trades = m.get("winning_trades", 0)
    losing_trades = m.get("losing_trades", 0)
    avg_trade = m.get("avg_trade", 0.0)

    # Assumptions
    a = result.assumptions
    exec_model = a.get("execution_model", "next_bar_open")
    sig_conf = a.get("signal_confirmation", "bar_close")
    init_cap = a.get("initial_capital", 100_000.0)
    comm = a.get("commission_per_side", 0.0)
    slip = a.get("slippage_per_side_ticks", 0.0)
    tick_sz = a.get("tick_size", 1.0)

    # HTML escaping for all dynamic text fields to prevent injection
    strategy_name_esc = html.escape(strategy.name)
    gen_version_esc = html.escape(str(gen_version))
    seed_esc = html.escape(str(seed))
    rule_versions_esc = html.escape(rule_versions)
    generated_at_esc = html.escape(generated_at)
    
    exec_model_esc = html.escape(str(exec_model))
    sig_conf_esc = html.escape(str(sig_conf))

    # Strategy conditions description
    long_entry_desc = format_block_desc(strategy.long_entry)
    long_exit_desc = format_block_desc(strategy.long_exit)
    short_entry_desc = format_block_desc(strategy.short_entry)
    short_exit_desc = format_block_desc(strategy.short_exit)

    long_entry_desc_esc = html.escape(long_entry_desc)
    long_exit_desc_esc = html.escape(long_exit_desc)
    short_entry_desc_esc = html.escape(short_entry_desc)
    short_exit_desc_esc = html.escape(short_exit_desc)

    # Formatting warnings
    warnings_list_html = ""
    if result.warnings:
        for w in result.warnings:
            warnings_list_html += f'<div class="warning-item">⚠ {html.escape(w)}</div>'
    else:
        warnings_list_html = '<div class="no-warnings">No warnings generated during this backtest.</div>'

    # Formatting detailed trades table
    trade_rows_html = ""
    if not result.trades:
        trade_rows_html = '<tr><td colspan="8" class="no-trades">No trades executed during this backtest.</td></tr>'
    else:
        for i, t in enumerate(result.trades):
            entry_t = t.entry_time.strftime("%Y-%m-%d %H:%M") if hasattr(t.entry_time, "strftime") else str(t.entry_time)
            exit_t = t.exit_time.strftime("%Y-%m-%d %H:%M") if hasattr(t.exit_time, "strftime") else str(t.exit_time)
            pnl_class = "pnl-positive" if t.pnl > 0 else "pnl-negative" if t.pnl < 0 else ""
            pnl_sign = "+" if t.pnl > 0 else ""
            
            direction_value = str(t.direction)
            direction_lower = direction_value.lower()
            direction_class = direction_lower if direction_lower in {"long", "short"} else "unknown"
            direction_esc = html.escape(direction_value.upper())
            exit_reason_esc = html.escape(t.exit_reason)
            
            trade_rows_html += f"""
            <tr>
                <td>{i + 1}</td>
                <td><span class="direction-badge {direction_class}">{direction_esc}</span></td>
                <td>{entry_t}</td>
                <td>${t.entry_price:,.2f}</td>
                <td>{exit_t}</td>
                <td>${t.exit_price:,.2f}</td>
                <td class="{pnl_class}">{pnl_sign}${t.pnl:,.2f}</td>
                <td>{exit_reason_esc}</td>
            </tr>
            """

    # Color definitions based on values
    pnl_color_class = "positive" if total_pnl > 0 else "negative" if total_pnl < 0 else ""
    pf_str = "N/A" if profit_factor == 999.0 else f"{profit_factor:.2f}"

    title_header = "Quant Strategy Lab — Sample / Mock Report (No Project Loaded)" if is_mock else "Quant Strategy Lab"
    report_type_label = "Sample / Mock Backtest Performance" if is_mock else "Backtest Performance"

    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quant Strategy Lab — Backtest Report ({strategy_name_esc})</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #121214;
            --card-bg: #1e1e24;
            --border-color: #2a2a2e;
            --text-main: #e0e0e3;
            --text-secondary: #8e8e93;
            --primary: #26a69a;
            --primary-glow: rgba(38, 166, 154, 0.15);
            --danger: #ef5350;
            --danger-glow: rgba(239, 83, 80, 0.1);
            --warning: #ffb300;
            --warning-glow: rgba(255, 179, 0, 0.1);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}

        /* Header Style */
        header {{
            background: linear-gradient(135deg, #1a1a2e, #162421);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            position: relative;
            overflow: hidden;
        }}

        header::before {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, var(--primary-glow) 0%, transparent 70%);
            z-index: 1;
        }}

        .header-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 28px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 8px;
        }}

        .header-meta {{
            color: var(--text-secondary);
            font-size: 13px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}

        .header-meta span strong {{
            color: var(--text-main);
        }}

        /* KPI Panel Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}

        .kpi-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s, border-color 0.2s;
        }}

        .kpi-card:hover {{
            transform: translateY(-2px);
            border-color: var(--primary);
        }}

        .kpi-title {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }}

        .kpi-value {{
            font-family: 'Outfit', sans-serif;
            font-size: 22px;
            font-weight: 700;
            color: #ffffff;
        }}

        .kpi-card.positive .kpi-value {{
            color: var(--primary);
        }}

        .kpi-card.negative .kpi-value {{
            color: var(--danger);
        }}

        /* Columns Grid */
        .details-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 24px;
            margin-bottom: 24px;
        }}

        @media (max-width: 600px) {{
            .details-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .panel {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 24px;
            height: 100%;
        }}

        .panel-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 18px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
        }}

        /* Lists */
        .info-list {{
            list-style: none;
        }}

        .info-list li {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px dashed #2a2a2e;
            font-size: 14px;
        }}

        .info-list li:last-child {{
            border-bottom: none;
        }}

        .info-list li .label {{
            color: var(--text-secondary);
        }}

        .info-list li .value {{
            font-weight: 500;
            font-family: 'Courier New', Courier, monospace;
        }}

        /* Strategy rules styling */
        .rules-container {{
            margin-top: 10px;
        }}

        .rule-item {{
            background-color: rgba(0, 0, 0, 0.2);
            border-left: 3px solid var(--primary);
            border-radius: 0 4px 4px 0;
            padding: 10px 14px;
            margin-bottom: 12px;
            font-size: 13px;
        }}

        .rule-item.inactive {{
            border-left-color: var(--text-secondary);
            color: var(--text-secondary);
        }}

        .rule-name {{
            font-weight: bold;
            color: #ffffff;
            margin-bottom: 4px;
        }}

        .rule-code {{
            font-family: 'Courier New', Courier, monospace;
            color: var(--primary);
        }}

        .rule-item.inactive .rule-code {{
            color: var(--text-secondary);
        }}

        /* Disclaimer Alert */
        .disclaimer-card {{
            background: linear-gradient(to right, rgba(239, 83, 80, 0.05), rgba(239, 83, 80, 0.01));
            border: 1px solid var(--danger);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 24px;
            display: flex;
            gap: 16px;
            align-items: center;
        }}

        .disclaimer-icon {{
            font-size: 24px;
            color: var(--danger);
        }}

        .disclaimer-text {{
            font-size: 13px;
            color: var(--text-main);
        }}

        .disclaimer-text strong {{
            color: #ffffff;
            display: block;
            margin-bottom: 2px;
        }}

        /* Warnings Panel */
        .warnings-panel {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 24px;
            margin-bottom: 24px;
        }}

        .warning-item {{
            background-color: var(--warning-glow);
            border: 1px solid var(--warning);
            border-radius: 6px;
            color: #fffbdf;
            padding: 12px 16px;
            margin-bottom: 10px;
            font-size: 13.5px;
        }}

        .no-warnings {{
            color: var(--text-secondary);
            font-size: 13.5px;
            font-style: italic;
        }}

        /* Transaction Log */
        .log-panel {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 24px;
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13.5px;
            text-align: left;
        }}

        th {{
            color: var(--text-secondary);
            font-weight: 600;
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
        }}

        tr:hover td {{
            background-color: rgba(255, 255, 255, 0.02);
        }}

        .no-trades {{
            text-align: center;
            color: var(--text-secondary);
            padding: 30px;
            font-style: italic;
        }}

        .direction-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            color: #ffffff;
        }}

        .direction-badge.long {{
            background-color: var(--primary);
        }}

        .direction-badge.short {{
            background-color: var(--danger);
        }}

        .pnl-positive {{
            color: var(--primary);
            font-weight: 600;
        }}

        .pnl-negative {{
            color: var(--danger);
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <h1 class="header-title">{title_header}</h1>
            <div class="header-meta">
                <span>Report: <strong>{report_type_label}</strong></span>
                <span>Strategy: <strong>{strategy_name_esc}</strong></span>
                <span>Generated At: <strong>{generated_at_esc}</strong></span>
            </div>
        </header>

        <!-- Financial Disclaimer -->
        <div class="disclaimer-card">
            <div class="disclaimer-icon">⚠</div>
            <div class="disclaimer-text">
                <strong>Financial Safety Notice & Disclaimer</strong>
                This report is for research and backtesting purposes only. Backtested performance does not guarantee future results.
            </div>
        </div>

        <!-- KPI Grid -->
        <div class="kpi-grid">
            <div class="kpi-card {pnl_color_class}">
                <div class="kpi-title">Total Net Profit</div>
                <div class="kpi-value">${total_pnl:,.2f}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Profit Factor</div>
                <div class="kpi-value">{pf_str}</div>
            </div>
            <div class="kpi-card negative">
                <div class="kpi-title">Max Drawdown</div>
                <div class="kpi-value">${max_drawdown:,.2f}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Win Rate</div>
                <div class="kpi-value">{win_rate * 100:.1f}%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Total Trades</div>
                <div class="kpi-value">{total_trades}</div>
            </div>
        </div>

        <!-- Details Grid -->
        <div class="details-grid">
            <!-- Strategy Profile -->
            <div class="panel">
                <h2 class="panel-title">Strategy Profile</h2>
                <ul class="info-list" style="margin-bottom: 20px;">
                    <li><span class="label">Name</span><span class="value">{strategy_name_esc}</span></li>
                    <li><span class="label">Generator Version</span><span class="value">{gen_version_esc}</span></li>
                    <li><span class="label">Random Seed</span><span class="value">{seed_esc}</span></li>
                    <li><span class="label">Rule Versions</span><span class="value">{rule_versions_esc}</span></li>
                </ul>
                <h3 class="panel-title" style="font-size: 14px; margin-bottom: 10px; border: none; padding: 0;">Strategy Logic Blocks</h3>
                <div class="rules-container">
                    <div class="rule-item {"inactive" if long_entry_desc == "Inactive" else ""}">
                        <div class="rule-name">Long Entry</div>
                        <div class="rule-code">{long_entry_desc_esc}</div>
                    </div>
                    <div class="rule-item {"inactive" if long_exit_desc == "Inactive" else ""}">
                        <div class="rule-name">Long Exit</div>
                        <div class="rule-code">{long_exit_desc_esc}</div>
                    </div>
                    <div class="rule-item {"inactive" if short_entry_desc == "Inactive" else ""}">
                        <div class="rule-name">Short Entry</div>
                        <div class="rule-code">{short_entry_desc_esc}</div>
                    </div>
                    <div class="rule-item {"inactive" if short_exit_desc == "Inactive" else ""}">
                        <div class="rule-name">Short Exit</div>
                        <div class="rule-code">{short_exit_desc_esc}</div>
                    </div>
                </div>
            </div>

            <!-- Backtest Settings -->
            <div class="panel">
                <h2 class="panel-title">Backtest Settings & Assumptions</h2>
                <ul class="info-list" style="margin-bottom: 24px;">
                    <li><span class="label">Execution Model</span><span class="value">{exec_model_esc}</span></li>
                    <li><span class="label">Signal Confirmation</span><span class="value">{sig_conf_esc}</span></li>
                    <li><span class="label">Initial Capital</span><span class="value">${init_cap:,.2f}</span></li>
                    <li><span class="label">Commission per Side</span><span class="value">${comm:,.2f}</span></li>
                    <li><span class="label">Slippage per Side (Ticks)</span><span class="value">{slip}</span></li>
                    <li><span class="label">Tick Size</span><span class="value">{tick_sz}</span></li>
                </ul>
                
                <h2 class="panel-title" style="margin-top: 10px;">Sub-Metrics Details</h2>
                <ul class="info-list">
                    <li><span class="label">Winning Trades</span><span class="value" style="color: var(--primary);">{winning_trades}</span></li>
                    <li><span class="label">Losing Trades</span><span class="value" style="color: var(--danger);">{losing_trades}</span></li>
                    <li><span class="label">Average Trade PnL</span><span class="value">{"+" if avg_trade > 0 else ""}${avg_trade:,.2f}</span></li>
                </ul>
            </div>
        </div>

        <!-- Warnings Panel -->
        <div class="warnings-panel">
            <h2 class="panel-title">System Log & Execution Warnings</h2>
            {warnings_list_html}
        </div>

        <!-- Transaction Log -->
        <div class="log-panel">
            <h2 class="panel-title">Detailed Transaction Log</h2>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Direction</th>
                        <th>Entry Time</th>
                        <th>Entry Price</th>
                        <th>Exit Time</th>
                        <th>Exit Price</th>
                        <th>PnL</th>
                        <th>Exit Reason</th>
                    </tr>
                </thead>
                <tbody>
                    {trade_rows_html}
                </tbody>
            </table>
        </div>
    </div>
"""
    # ── validation evidence section ──────────────────────────────────────
    if validation_result:
        html_out += _format_html_validation(validation_result)
    else:
        html_out += ('<div class="panel" style="margin-top:24px;"><h2 class="panel-title">'
                     'Validation Evidence</h2><p style="color:#8e8e93;font-style:italic;">'
                     'No validation evidence was included in this report.</p></div>')
                     
    # ── multi-instrument evidence section ────────────────────────────────
    if multi_instrument_result:
        html_out += _format_html_multi_instrument(multi_instrument_result)

    html_out += "\n</body>\n</html>\n"
    return html_out


# ---------------------------------------------------------------------------
# Validation evidence formatters
# ---------------------------------------------------------------------------


def _format_markdown_validation(vr: dict) -> str:
    lines = ["\n## Validation Evidence\n"]
    ds = vr.get("data_source", "")
    if ds:
        lines.append(f"- **Data Source**: {ds}")
    if vr.get("precheck_failed"):
        elim = vr.get("elimination_result", {}) or {}
        reason = (elim.get("failed_rules", []) or ["Unknown"])[0]
        lines.append(f"- **Precheck**: FAILED — {reason}")

    sm = vr.get("split_metadata", {})
    lines.append(f"- **Split**: Train={sm.get('train_rows','?')}, "
                 f"Val={sm.get('validation_rows','?')}, OOS={sm.get('oos_rows','?')}")
    bm = vr.get("baseline_metrics", {})
    lines.append(f"- **Baseline**: PnL={bm.get('total_pnl',0):,.0f}, "
                 f"PF={bm.get('profit_factor',0):.2f}, Trades={bm.get('total_trades',0)}")
    oos = vr.get("oos_metrics", {}) or {}
    if oos and oos.get("total_trades", 0) is not None:
        lines.append(f"- **OOS**: PnL={oos.get('total_pnl',0):,.0f}, "
                     f"PF={oos.get('profit_factor',0):.2f}, Trades={oos.get('total_trades',0)}, "
                     f"Max DD={oos.get('max_drawdown_pnl',0):,.0f}")
    for s in vr.get("stress_results", []):
        deg = s.get("degradation", {}).get("total_pnl", 0)
        passed = "OK" if s.get("passed") else "FAIL"
        name = s.get("test_name", "?")
        lines.append(f"- **Stress ({name})**: {passed} PnL d={deg:.1%}")

        # Detail sub-lines for remove_best_n_trades.
        if name == "remove_best_n_trades":
            assumptions = s.get("assumptions", {}) or {}
            if assumptions:
                n_val = assumptions.get("n", "?")
                removed = assumptions.get("removed_count", "?")
                surviving = assumptions.get("surviving_count", "?")
                total = removed + surviving if isinstance(removed, int) and isinstance(surviving, int) else "?"
                pnl_loss = assumptions.get("pnl_loss_ratio", "?")
                if isinstance(pnl_loss, float):
                    pnl_loss = f"{pnl_loss:.3f}"
                threshold = (s.get("threshold", {}) or {}).get("max_pnl_loss", "?")
                if isinstance(threshold, float):
                    threshold = f"{threshold:.2f}"
                lines.append(f"  - Removed: {removed} of {total} trades (n={n_val}, "
                             f"pnl_loss={pnl_loss}, threshold={threshold})")
            for w in (s.get("warnings", []) or []):
                lines.append(f"  - WARNING: {w}")

        # Detail sub-lines for price_noise (Task 062L-Impl).
        if name == "price_noise":
            assumptions = s.get("assumptions", {}) or {}
            detail = _format_price_noise_detail_text(assumptions)
            if detail:
                lines.append(f"  - {detail}")
            for w in (s.get("warnings", []) or []):
                lines.append(f"  - WARNING: {w}")
    mc = vr.get("monte_carlo_summary", {}) or {}
    ps = (mc.get("percentile_summary", {}) or {}).get("total_pnl", {}) or {}
    if ps:
        lines.append(f"- **MC** ({mc.get('iterations','?')} iter): "
                     f"p05={ps.get('p5','?'):,.0f} p50={ps.get('p50','?'):,.0f} p95={ps.get('p95','?'):,.0f}")
    bootstrap_md = vr.get("bootstrap_monte_carlo_result", {}) or {}
    if bootstrap_md:
        ci = bootstrap_md.get("confidence_intervals", {}) or {}
        if ci:  # only show when CI data is non-empty
            stability = bootstrap_md.get("stability_score", "?")
            if isinstance(stability, float):
                stability = f"{stability:.2f}"
            lines.append(f"- **Bootstrap MC** ({bootstrap_md.get('iterations','?')} iter): "
                         f"Stability={stability}")
            for key, label, fmt in [("total_pnl", "PnL", ",.0f"), ("profit_factor", "PF", ".2f"), ("max_drawdown_pnl", "Max DD", ",.0f")]:
                d = ci.get(key, {})
                if d:
                    lines.append(f"  - {label} 95% CI [{d.get('ci_lower',0):{fmt}} — {d.get('ci_upper',0):{fmt}}] "
                                 f"mean={d.get('ci_mean',0):{fmt}}")
    # MC worst-case equity evidence (Task 063F-Impl).
    wc_curve = mc.get("worst_case_equity_curve")
    if isinstance(wc_curve, list) and len(wc_curve) >= 2:
        curve_type, curve_note = _format_mc_equity_curve_type(
            mc.get("worst_case_equity_curve_type", "trade_step")
        )
        start_eq = wc_curve[0]
        end_eq = wc_curve[-1]
        pct = ((end_eq - start_eq) / abs(start_eq)) * 100 if abs(start_eq) > 1e-9 else 0.0
        lines.append(f"- **MC Worst-Case Equity** ({curve_type}): "
                     f"Start={start_eq:,.0f}, End={end_eq:,.0f} ({pct:+.1f}%)")
        lines.append(f"  - *Note: {curve_note}*")
    wf = vr.get("walk_forward_summary", {}) or {}
    if wf:
        lines.append(f"- **WF**: {wf.get('pass_count','?')}/{wf.get('window_count','?')} "
                     f"passed ({(wf.get('pass_rate',0) or 0)*100:.0f}%)")
        if "average_wfe" in wf or "median_wfe" in wf:
            avg_wfe = wf.get("average_wfe")
            med_wfe = wf.get("median_wfe")
            def_cnt = wf.get("defined_wfe_count", 0)
            undef_cnt = wf.get("undefined_wfe_count", 0)
            avg_str = f"{avg_wfe:.2f}" if avg_wfe is not None else "N/A"
            med_str = f"{med_wfe:.2f}" if med_wfe is not None else "N/A"
            lines.append(f"- **WF Efficiency**: Avg={avg_str}, Median={med_str}, Defined Windows={def_cnt}, Undefined Windows={undef_cnt}")
    windows = wf.get("windows") or []
    equity_windows = [w for w in windows
                      if isinstance(w.get("equity_curve"), list) and len(w.get("equity_curve", [])) >= 2]
    if equity_windows:
        MAX = 5
        lines.append(f"\n- **WF Equity by Window**:")
        lines.append("  | # | Start | End | Change | Result |")
        lines.append("  |---|---|---|---|:---:|")
        for w in equity_windows[:MAX]:
            curve = w["equity_curve"]
            start = curve[0]
            end = curve[-1]
            pct = (end - start) / abs(start) * 100 if abs(start) > 1e-9 else 0.0
            status = "PASSED" if w.get("passed") else "FAILED"
            lines.append(f"  | {w.get('index', '?')} | {start:,.0f} | {end:,.0f} | {pct:+.1f}% | {status} |")
        if len(equity_windows) > MAX:
            lines.append(f"  | ... | — | — | {len(equity_windows) - MAX} more | ... |")
    wfm = vr.get("walk_forward_matrix_summary", {}) or {}
    if wfm:
        total = wfm.get("config_count", 0)
        tested = wfm.get("tested_count", 0)
        insufficient = wfm.get("insufficient_data_count", 0)
        best = wfm.get("best_pass_rate_config") or {}
        worst = wfm.get("worst_pass_rate_config") or {}
        best_id = best.get("config_id", "N/A") if best else "N/A"
        worst_id = worst.get("config_id", "N/A") if worst else "N/A"
        best_rate = (best.get("pass_rate", 0) * 100) if best else 0
        worst_rate = (worst.get("pass_rate", 0) * 100) if worst else 0
        lines.append(
            f"- **WF Matrix**: {tested}/{total} configs tested, insufficient={insufficient}, "
            f"Best={best_id} ({best_rate:.0f}%), Worst={worst_id} ({worst_rate:.0f}%)"
        )
    elim = vr.get("elimination_result", {}) or {}
    if elim.get("passed"):
        lines.append("- **Elimination**: PASSED")
    else:
        lines.append(f"- **Elimination**: ELIMINATED — {'; '.join(elim.get('failed_rules',[]))}")
    # Show enabled thresholds.
    config_snap = elim.get("config_snapshot", {}) or {}
    enabled = [f"{k}={v}" for k, v in config_snap.items()
               if v is not None and v is not False and k != "require_optional"]
    if enabled:
        lines.append(f"  - Thresholds applied: {', '.join(enabled)}")
    # Show warnings.
    elim_warnings = elim.get("warnings", []) or []
    for w in elim_warnings:
        lines.append(f"  - Warning: {w}")
    return "\n".join(lines) + "\n"


def _format_html_validation(vr: dict) -> str:
    parts = ['<div class="panel" style="margin-top:24px;">',
             '<h2 class="panel-title">Validation Evidence</h2>']
    ds = vr.get("data_source", "")
    if ds:
        parts.append(f'<p><b>Data Source:</b> {html.escape(ds)}</p>')
    if vr.get("precheck_failed"):
        elim = vr.get("elimination_result", {}) or {}
        reason = (elim.get("failed_rules", []) or ["Unknown"])[0]
        parts.append(f'<p><b>Precheck:</b> <span style="color:#ef5350;font-weight:bold;">'
                     f'FAILED</span> — {html.escape(reason)}</p>')

    sm = vr.get("split_metadata", {})
    parts.append(f'<p><b>Split:</b> Train={sm.get("train_rows","?")}, '
                 f'Val={sm.get("validation_rows","?")}, OOS={sm.get("oos_rows","?")}</p>')
    bm = vr.get("baseline_metrics", {})
    parts.append(f'<p><b>Baseline:</b> PnL={bm.get("total_pnl",0):,.0f}, '
                 f'PF={bm.get("profit_factor",0):.2f}, Trades={bm.get("total_trades",0)}</p>')
    oos = vr.get("oos_metrics", {}) or {}
    if oos and oos.get("total_trades", 0) is not None:
        parts.append(f'<p><b>OOS:</b> PnL={oos.get("total_pnl",0):,.0f}, '
                     f'PF={oos.get("profit_factor",0):.2f}, Trades={oos.get("total_trades",0)}, '
                     f'Max DD={oos.get("max_drawdown_pnl",0):,.0f}</p>')
    for s in vr.get("stress_results", []):
        deg = s.get("degradation", {}).get("total_pnl", 0)
        raw_name = s.get("test_name", "?")
        name = html.escape(str(raw_name))
        parts.append(f'<p><b>Stress ({name}):</b> PnL d={deg:.1%}</p>')

        # Detail sub-lines for remove_best_n_trades.
        if raw_name == "remove_best_n_trades":
            assumptions = s.get("assumptions", {}) or {}
            if assumptions:
                n_val = assumptions.get("n", "?")
                removed = assumptions.get("removed_count", "?")
                surviving = assumptions.get("surviving_count", "?")
                total = removed + surviving if isinstance(removed, int) and isinstance(surviving, int) else "?"
                pnl_loss = assumptions.get("pnl_loss_ratio", "?")
                if isinstance(pnl_loss, float):
                    pnl_loss = f"{pnl_loss:.3f}"
                threshold = (s.get("threshold", {}) or {}).get("max_pnl_loss", "?")
                if isinstance(threshold, float):
                    threshold = f"{threshold:.2f}"
                parts.append(f'<div class="stress-detail">Removed: {html.escape(str(removed))} '
                             f'of {html.escape(str(total))} trades '
                             f'(n={html.escape(str(n_val))}, pnl_loss={html.escape(str(pnl_loss))}, '
                             f'threshold={html.escape(str(threshold))})</div>')
            for w in (s.get("warnings", []) or []):
                parts.append(f'<div class="warning-item">⚠ {html.escape(w)}</div>')

        # Detail sub-lines for price_noise (Task 062L-Impl).
        if raw_name == "price_noise":
            assumptions = s.get("assumptions", {}) or {}
            detail = _format_price_noise_detail_text(assumptions)
            if detail:
                parts.append(f'<div class="stress-detail">{html.escape(detail)}</div>')
            for w in (s.get("warnings", []) or []):
                parts.append(f'<div class="warning-item">⚠ {html.escape(w)}</div>')
    mc = vr.get("monte_carlo_summary", {}) or {}
    ps = (mc.get("percentile_summary", {}) or {}).get("total_pnl", {}) or {}
    if ps:
        parts.append(f'<p><b>MC</b> ({mc.get("iterations","?")} iter): '
                     f'p05={ps.get("p5","?"):,.0f} p50={ps.get("p50","?"):,.0f} p95={ps.get("p95","?"):,.0f}</p>')
    bootstrap_html = vr.get("bootstrap_monte_carlo_result", {}) or {}
    if bootstrap_html:
        ci = bootstrap_html.get("confidence_intervals", {}) or {}
        if ci:  # only show when CI data is non-empty
            stability = bootstrap_html.get("stability_score", "?")
            if isinstance(stability, float):
                stability = f"{stability:.2f}"
            parts.append(f'<p><b>Bootstrap MC</b> ({bootstrap_html.get("iterations","?")} iter): '
                         f'Stability={stability}</p>')
            for key, label, fmt in [("total_pnl", "PnL", ",.0f"), ("profit_factor", "PF", ".2f"), ("max_drawdown_pnl", "Max DD", ",.0f")]:
                d = ci.get(key, {})
                if d:
                    parts.append(f'<div class="stress-detail">'
                                 f'{label} 95% CI [{d.get("ci_lower",0):{fmt}} — {d.get("ci_upper",0):{fmt}}] '
                                 f'mean={d.get("ci_mean",0):{fmt}}</div>')
    # MC worst-case equity evidence (Task 063F-Impl).
    wc_curve = mc.get("worst_case_equity_curve")
    if isinstance(wc_curve, list) and len(wc_curve) >= 2:
        curve_type, curve_note = _format_mc_equity_curve_type(
            mc.get("worst_case_equity_curve_type", "trade_step")
        )
        start_eq = wc_curve[0]
        end_eq = wc_curve[-1]
        pct = ((end_eq - start_eq) / abs(start_eq)) * 100 if abs(start_eq) > 1e-9 else 0.0
        parts.append(f'<p><b>MC Worst-Case Equity</b> ({html.escape(curve_type)}): '
                     f'Start={start_eq:,.0f}, End={end_eq:,.0f} ({pct:+.1f}%)</p>')
        parts.append(f'<p><i>{html.escape(curve_note)}</i></p>')
    wf = vr.get("walk_forward_summary", {}) or {}
    if wf:
        parts.append(f'<p><b>WF:</b> {wf.get("pass_count","?")}/{wf.get("window_count","?")} '
                     f'passed ({(wf.get("pass_rate",0) or 0)*100:.0f}%)</p>')
        if "average_wfe" in wf or "median_wfe" in wf:
            avg_wfe = wf.get("average_wfe")
            med_wfe = wf.get("median_wfe")
            def_cnt = wf.get("defined_wfe_count", 0)
            undef_cnt = wf.get("undefined_wfe_count", 0)
            avg_str = f"{avg_wfe:.2f}" if avg_wfe is not None else "N/A"
            med_str = f"{med_wfe:.2f}" if med_wfe is not None else "N/A"
            parts.append(f'<p><b>WF Efficiency:</b> Avg={avg_str}, Median={med_str}, Defined Windows={def_cnt}, Undefined Windows={undef_cnt}</p>')
    windows = wf.get("windows") or []
    equity_windows = [w for w in windows
                      if isinstance(w.get("equity_curve"), list) and len(w.get("equity_curve", [])) >= 2]
    if equity_windows:
        MAX = 5
        parts.append('<p><b>WF Equity by Window</b></p>')
        parts.append('<table><thead><tr><th>#</th><th>Start</th><th>End</th><th>Change</th><th>Result</th></tr></thead><tbody>')
        for w in equity_windows[:MAX]:
            curve = w["equity_curve"]
            start = curve[0]
            end = curve[-1]
            pct = (end - start) / abs(start) * 100 if abs(start) > 1e-9 else 0.0
            pnl_class = "pnl-positive" if pct >= 0 else "pnl-negative"
            status = "PASSED" if w.get("passed") else "FAILED"
            parts.append(f'<tr><td>{w.get("index","?")}</td><td>{start:,.0f}</td><td>{end:,.0f}</td>'
                         f'<td class="{pnl_class}">{pct:+.1f}%</td><td>{status}</td></tr>')
        if len(equity_windows) > MAX:
            parts.append(f'<tr><td colspan="5">... {len(equity_windows) - MAX} more windows ...</td></tr>')
        parts.append('</tbody></table>')
    wfm = vr.get("walk_forward_matrix_summary", {}) or {}
    if wfm:
        total = wfm.get("config_count", 0)
        tested = wfm.get("tested_count", 0)
        insufficient = wfm.get("insufficient_data_count", 0)
        best = wfm.get("best_pass_rate_config") or {}
        worst = wfm.get("worst_pass_rate_config") or {}
        best_id = html.escape(str(best.get("config_id", "N/A"))) if best else "N/A"
        worst_id = html.escape(str(worst.get("config_id", "N/A"))) if worst else "N/A"
        best_rate = (best.get("pass_rate", 0) * 100) if best else 0
        worst_rate = (worst.get("pass_rate", 0) * 100) if worst else 0
        parts.append(
            f'<p><b>WF Matrix:</b> {tested}/{total} configs tested, insufficient={insufficient}, '
            f'Best={best_id} ({best_rate:.0f}%), Worst={worst_id} ({worst_rate:.0f}%)</p>'
        )
    elim = vr.get("elimination_result", {}) or {}
    if elim.get("passed"):
        parts.append('<p><b>Elimination:</b> <span style="color:#26a69a;font-weight:bold;">PASSED</span></p>')
    else:
        rules = "; ".join(html.escape(r) for r in elim.get("failed_rules", []))
        parts.append(f'<p><b>Elimination:</b> <span style="color:#ef5350;font-weight:bold;">ELIMINATED</span> — {rules}</p>')
    # Enabled thresholds.
    config_snap = elim.get("config_snapshot", {}) or {}
    enabled = [f"{k}={v}" for k, v in config_snap.items()
               if v is not None and v is not False and k != "require_optional"]
    if enabled:
        parts.append(f'<p style="margin-left:1em;"><b>Thresholds applied:</b> {html.escape(", ".join(enabled))}</p>')
    # Warnings.
    elim_warnings = elim.get("warnings", []) or []
    for w in elim_warnings:
        parts.append(f'<p style="margin-left:1em;"><b>Warning:</b> {html.escape(w)}</p>')
    parts.append('</div>')
    return "\n".join(parts)


def _format_price_noise_detail_text(assumptions: dict) -> str:
    """Format price-noise assumptions for Markdown and escaped HTML report output."""
    details: list[str] = []
    noise_pct = assumptions.get("noise_pct")
    if isinstance(noise_pct, (int, float)) and not isinstance(noise_pct, bool):
        details.append(f"noise_pct={noise_pct:.1%}")
    elif noise_pct is not None:
        details.append(f"noise_pct={noise_pct}")

    if "iterations" in assumptions:
        details.append(f"iterations={assumptions.get('iterations')}")
    if "method" in assumptions:
        details.append(f"method={assumptions.get('method')}")
    if "research_only" in assumptions:
        details.append(f"research_only={assumptions.get('research_only')}")
    return ", ".join(details)


def _format_mc_equity_curve_type(raw_curve_type: object) -> tuple[str, str]:
    """Return display type and honesty note for MC worst-case equity evidence."""
    curve_type = str(raw_curve_type or "trade_step")
    display_type = curve_type.replace("_", "-")
    if curve_type == "trade_step":
        note = "trade-step curve from surviving trades only; not a bar-by-bar equity curve."
    else:
        note = f"{display_type} curve type is not verified as bar-by-bar equity."
    return display_type, note


def _sanitize_md(text: str) -> str:
    if not text:
        return ""
    return str(text).replace("\n", " ").replace("\r", "").replace("|", "\\|")


def _format_markdown_multi_instrument(mir: "MultiInstrumentBacktestResult") -> str:
    lines = ["\n## Multi-Instrument Evidence\n"]
    
    agg = mir.aggregate_metrics
    lines.append("### Aggregate Metrics (Successful Runs Only)")
    lines.append(f"- **Instruments**: {mir.success_count} passed / {mir.failure_count} failed (Total: {mir.instrument_count})")
    lines.append(f"- **Total Trades**: {agg.get('total_trades_sum', 0)}")
    lines.append(f"- **Mean Total PnL**: ${agg.get('mean_total_pnl', 0.0):,.2f}")
    lines.append(f"- **Median Total PnL**: ${agg.get('median_total_pnl', 0.0):,.2f}")
    lines.append(f"- **Min Total PnL**: ${agg.get('min_total_pnl', 0.0):,.2f}")
    lines.append(f"- **Max Total PnL**: ${agg.get('max_total_pnl', 0.0):,.2f}")
    lines.append(f"- **Worst Max Drawdown**: ${agg.get('worst_max_drawdown_pnl', 0.0):,.2f}")
    pf = agg.get('mean_profit_factor')
    pf_str = f"{pf:.2f}" if pf is not None else "N/A"
    lines.append(f"- **Mean Profit Factor**: {pf_str}\n")

    lines.append("### Per-Instrument Breakdown")
    lines.append("| Instrument | Status | Trades | Net Profit | Profit Factor | Max Drawdown | Notes |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    
    for r in mir.per_instrument:
        safe_label = _sanitize_md(r.label)
        if r.success:
            m = r.metrics
            pf_val = m.get('profit_factor', 0.0)
            pf_str = "N/A" if pf_val == 999.0 else f"{pf_val:.2f}"
            lines.append(f"| {safe_label} | PASSED | {m.get('total_trades',0)} | ${m.get('total_pnl',0.0):,.2f} | {pf_str} | ${m.get('max_drawdown_pnl',0.0):,.2f} | - |")
        else:
            safe_err = _sanitize_md(r.error_message)
            lines.append(f"| {safe_label} | FAILED | - | - | - | - | {safe_err} |")

    if mir.warnings:
        lines.append("\n### Warnings")
        for w in mir.warnings:
            lines.append(f"- {_sanitize_md(w)}")

    return "\n".join(lines) + "\n"


def _format_html_multi_instrument(mir: "MultiInstrumentBacktestResult") -> str:
    agg = mir.aggregate_metrics
    pf = agg.get('mean_profit_factor')
    pf_str = f"{pf:.2f}" if pf is not None else "N/A"
    
    html_out = '<div class="panel" style="margin-top:24px;">'
    html_out += '<h2 class="panel-title">Multi-Instrument Evidence</h2>'
    html_out += '<h3 style="font-size: 14px; margin-bottom: 10px;">Aggregate Metrics (Successful Runs Only)</h3>'
    html_out += '<ul class="info-list" style="margin-bottom: 24px;">'
    html_out += f'<li><span class="label">Instruments</span><span class="value">{mir.success_count} passed / {mir.failure_count} failed (Total: {mir.instrument_count})</span></li>'
    html_out += f'<li><span class="label">Total Trades</span><span class="value">{agg.get("total_trades_sum", 0)}</span></li>'
    html_out += f'<li><span class="label">Mean Total PnL</span><span class="value">${agg.get("mean_total_pnl", 0.0):,.2f}</span></li>'
    html_out += f'<li><span class="label">Median Total PnL</span><span class="value">${agg.get("median_total_pnl", 0.0):,.2f}</span></li>'
    html_out += f'<li><span class="label">Min Total PnL</span><span class="value">${agg.get("min_total_pnl", 0.0):,.2f}</span></li>'
    html_out += f'<li><span class="label">Max Total PnL</span><span class="value">${agg.get("max_total_pnl", 0.0):,.2f}</span></li>'
    html_out += f'<li><span class="label">Worst Max Drawdown</span><span class="value">${agg.get("worst_max_drawdown_pnl", 0.0):,.2f}</span></li>'
    html_out += f'<li><span class="label">Mean Profit Factor</span><span class="value">{pf_str}</span></li>'
    html_out += '</ul>'
    
    html_out += '<h3 style="font-size: 14px; margin-bottom: 10px;">Per-Instrument Breakdown</h3>'
    html_out += '<div style="overflow-x: auto;"><table><thead><tr><th>Instrument</th><th>Status</th><th>Trades</th><th>Net Profit</th><th>Profit Factor</th><th>Max Drawdown</th><th>Notes</th></tr></thead><tbody>'
    
    for r in mir.per_instrument:
        label_esc = html.escape(r.label)
        if r.success:
            m = r.metrics
            pf_val = m.get('profit_factor', 0.0)
            pf_str = "N/A" if pf_val == 999.0 else f"{pf_val:.2f}"
            pnl_val = m.get('total_pnl', 0.0)
            pnl_class = "pnl-positive" if pnl_val > 0 else "pnl-negative" if pnl_val < 0 else ""
            pnl_sign = "+" if pnl_val > 0 else ""
            
            html_out += f'<tr><td>{label_esc}</td><td><span class="direction-badge long">PASSED</span></td>'
            html_out += f'<td>{m.get("total_trades",0)}</td><td class="{pnl_class}">{pnl_sign}${pnl_val:,.2f}</td>'
            html_out += f'<td>{pf_str}</td><td>${m.get("max_drawdown_pnl",0.0):,.2f}</td><td>-</td></tr>'
        else:
            err_esc = html.escape(str(r.error_message))
            html_out += f'<tr><td>{label_esc}</td><td><span class="direction-badge short">FAILED</span></td>'
            html_out += f'<td>-</td><td>-</td><td>-</td><td>-</td><td>{err_esc}</td></tr>'
            
    html_out += '</tbody></table></div>'
    
    if mir.warnings:
        html_out += '<h3 style="font-size: 14px; margin-top: 24px; margin-bottom: 10px;">Warnings</h3>'
        for w in mir.warnings:
            html_out += f'<div class="warning-item">⚠ {html.escape(w)}</div>'
            
    html_out += '</div>'
    return html_out
