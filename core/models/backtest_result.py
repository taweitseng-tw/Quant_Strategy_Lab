"""Backtest result models — structured outputs from the backtest engine.

Per AGENTS.md §6.3 the backtest MUST produce:
  - trades
  - equity_curve
  - drawdown_curve
  - metrics
  - assumptions
  - warnings
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Trade:
    """A single completed trade."""

    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    direction: str          # "long" or "short"
    entry_price: float
    exit_price: float
    quantity: int = 1
    pnl: float = 0.0
    exit_reason: str = ""   # "signal", "end_of_data"


@dataclass
class BacktestResult:
    """Structured output of a single-instrument, single-position backtest."""

    trades: list[Trade] = field(default_factory=list)
    equity_curve: pd.DataFrame | None = None   # columns: datetime, equity
    drawdown_curve: pd.DataFrame | None = None  # columns: datetime, drawdown
    metrics: dict = field(default_factory=dict)
    assumptions: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
