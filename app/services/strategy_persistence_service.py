"""Strategy persistence service — saves and loads Strategy objects via the
repository layer.

Provides a thin service wrapper around :class:`repository.strategy_repo.StrategyRepository`
so consumers (UI controllers, GA orchestrators) don't interact with the
repository database handle directly.

No GUI imports.  No backtest/validation logic.
"""

from __future__ import annotations

import copy

from core.models.strategy import Strategy
from repository.db import DatabaseManager
from repository.strategy_repo import StrategyRepository

# Default prefix for GA best-strategy labels.
GA_BEST_PREFIX = "ga_best_"


class StrategyPersistenceService:
    """Service for persisting and retrieving Strategy models.

    Wraps :class:`StrategyRepository` with a named-label convention so
    callers can save/load by a simple string label (e.g. ``"latest"``)
    rather than tracking repository row ids.
    """

    def __init__(self, db: DatabaseManager) -> None:
        self._repo = StrategyRepository(db)

    # ------------------------------------------------------------------
    # save
    # ------------------------------------------------------------------

    def save_best_strategy(
        self,
        strategy: Strategy,
        label: str = "latest",
        prefix: str = GA_BEST_PREFIX,
    ) -> str:
        """Persist *strategy* under ``{prefix}{label}``.

        The stored copy uses the canonical label as its name. The caller's
        Strategy object is never mutated. Existing entries with the same
        label are overwritten.

        Parameters
        ----------
        strategy : Strategy
            The strategy to persist.
        label : str
            Human-readable suffix (e.g. ``"latest"``, ``"gen5_best"``).
        prefix : str
            Namespace prefix — defaults to ``"ga_best_"``.

        Returns
        -------
        str
            The canonical name used for storage (``{prefix}{label}``).
        """
        store_name = f"{prefix}{label}"
        stored_strategy = copy.deepcopy(strategy)
        stored_strategy.name = store_name
        self._repo.save(stored_strategy)

        return store_name

    # ------------------------------------------------------------------
    # load
    # ------------------------------------------------------------------

    def load_best_strategy(
        self,
        label: str = "latest",
        prefix: str = GA_BEST_PREFIX,
    ) -> Strategy | None:
        """Load a previously saved strategy by label.

        Parameters
        ----------
        label : str
            Label suffix used at save time.
        prefix : str
            Must match the prefix used at save time.

        Returns
        -------
        Strategy or None
            ``None`` if no strategy was saved under that label.
        """
        store_name = f"{prefix}{label}"
        return self._repo.get_by_name(store_name)

    # ------------------------------------------------------------------
    # list
    # ------------------------------------------------------------------

    def list_all_raw(self) -> list[dict]:
        """Return every saved strategy as raw dicts (for archive export)."""
        return self._repo.list_all_raw()

    def list_saved_strategies(self, prefix: str = GA_BEST_PREFIX) -> list[Strategy]:
        """Return all strategies whose names start with *prefix*."""
        all_strats = self._repo.list_all()
        return [s for s in all_strats if s.name.startswith(prefix)]

    def delete_best_strategy(
        self,
        label: str = "latest",
        prefix: str = GA_BEST_PREFIX,
    ) -> bool:
        """Delete a previously saved strategy by label.

        Returns ``True`` if a row was removed.
        """
        store_name = f"{prefix}{label}"
        return self._repo.delete(store_name)
