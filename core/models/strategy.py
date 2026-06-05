"""Strategy model — MVP four-block structure.

Each strategy has four independent blocks:
  - Long Entry
  - Long Exit
  - Short Entry
  - Short Exit

Each block contains one or more conditions combined with AND / OR logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Condition:
    """A single rule condition, e.g. ``close > sma(20)``.

    For MVP the only supported indicator is ``"SMA"`` with params ``{"period": N}``
    and a numeric comparison operator.
    """

    indicator: str           # "SMA" (MVP)
    params: dict             # {"period": 20}
    operator: str            # ">" or "<"
    # The value to compare against — either a float literal or the string
    # "close" to compare against the current bar's close.
    left: str = "close"      # "close" (MVP)
    right: float | str = 0.0


@dataclass
class StrategyBlock:
    """One block (entry or exit) with a list of conditions and a logic gate."""

    conditions: list[Condition] = field(default_factory=list)
    logic: str = "AND"  # "AND" or "OR"


@dataclass
class RiskManagement:
    """Intra-bar risk management constraints."""
    stop_loss_ticks: float | None = None
    take_profit_ticks: float | None = None
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None
    close_end_of_session: bool = False
    session_end_time: str | None = None


@dataclass
class Strategy:
    """MVP four-block strategy template (PRD §7.1)."""

    name: str
    long_entry: StrategyBlock = field(default_factory=StrategyBlock)
    long_exit: StrategyBlock = field(default_factory=StrategyBlock)
    short_entry: StrategyBlock = field(default_factory=StrategyBlock)
    short_exit: StrategyBlock = field(default_factory=StrategyBlock)
    risk_management: RiskManagement = field(default_factory=RiskManagement)
