"""Instrument profile model — matches PRD §8.1.6.

Defines the contract size, tick granularity, and cost parameters that the
backtest engine uses to convert price movement into dollar PnL.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InstrumentProfile:
    """Trading instrument configuration for backtest PnL calculation.

    All monetary values are in the instrument's ``currency``.
    """

    symbol: str
    name: str = ""
    market: str = ""
    tick_size: float = 1.0
    point_value: float = 1.0          # Dollar value of 1 price-unit move
    commission_value: float = 0.0     # Per-side commission in dollars
    slippage_ticks: float = 0.0       # Default per-side slippage (ticks)
    currency: str = "USD"
    session_template: str = ""        # Name of session template (future use)
    session_start: str = ""           # Session start time e.g. "08:30"
    session_end: str = ""             # Session end time e.g. "13:30"
