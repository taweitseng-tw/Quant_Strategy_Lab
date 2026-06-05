"""Backtest metrics — computed from trade list and equity/drawdown curves."""

from __future__ import annotations

import pandas as pd

from core.models.backtest_result import Trade


def compute_metrics(
    trades: list[Trade],
    drawdown_curve: pd.DataFrame | None = None,
) -> dict:
    """Compute key performance metrics from a list of completed trades.

    Parameters
    ----------
    trades : list[Trade]
    drawdown_curve : DataFrame or None
        Optional ``datetime, drawdown`` DataFrame from the backtest.
        When provided, ``max_drawdown_pnl`` is taken from this curve
        (which includes intra-trade drawdown).  Falls back to
        cumulative-trade-PnL drawdown when None.

    Returns a dict with:
      - total_trades, winning_trades, losing_trades
      - win_rate
      - total_pnl, avg_trade
      - gross_profit, gross_loss, profit_factor
      - max_drawdown_pnl
    """
    if not trades:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "avg_trade": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "profit_factor": 0.0,
            "max_drawdown_pnl": 0.0,
        }

    winners = [t for t in trades if t.pnl > 0]
    losers = [t for t in trades if t.pnl <= 0]

    total_pnl = sum(t.pnl for t in trades)
    gross_profit = sum(t.pnl for t in winners)
    gross_loss = abs(sum(t.pnl for t in losers))

    # Profit factor: gross_profit / gross_loss.  If no losing trades, ∞ → cap at
    # a large sentinel to keep the dict JSON-serialisable.
    if gross_loss == 0:
        profit_factor = 999.0 if gross_profit > 0 else 0.0
    else:
        profit_factor = gross_profit / gross_loss

    # Max drawdown — prefer the drawdown curve when available (it includes
    # intra-trade drawdown that closed-trade PnL misses).
    if drawdown_curve is not None and "drawdown" in drawdown_curve.columns:
        max_dd = float(drawdown_curve["drawdown"].max())
    else:
        # Fallback: peak-to-valley from cumulative trade PnL.
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        for t in trades:
            cumulative += t.pnl
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd

    return {
        "total_trades": len(trades),
        "winning_trades": len(winners),
        "losing_trades": len(losers),
        "win_rate": len(winners) / len(trades) if trades else 0.0,
        "total_pnl": total_pnl,
        "avg_trade": total_pnl / len(trades) if trades else 0.0,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": round(profit_factor, 4),
        "max_drawdown_pnl": max_dd,
    }
