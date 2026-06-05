"""GA background worker — runs GA search off the UI thread.

Emits Qt signals so the main window can update the UI on completion
or failure without blocking the event loop.
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

import pandas as pd

from core.models.instrument import InstrumentProfile
from app.services.ga_service import GASearchConfig, GASearchResult, run_ga_search


class GAWorker(QThread):
    """Background thread that executes :func:`run_ga_search`.

    Signals
    -------
    success(GASearchResult, str)
        Emitted with (result, source_label) on successful completion.
    failure(str)
        Emitted with an error message string on exception.
    finished()
        Always emitted when the thread exits (inherited from QThread).
    """

    success = Signal(object, str)   # (GASearchResult, source_label)
    failure = Signal(str)           # error message

    def __init__(
        self,
        df: pd.DataFrame,
        config: GASearchConfig,
        source_label: str,
        *,
        instrument: InstrumentProfile | None = None,
        parent=None,
        **backtest_kwargs,
    ) -> None:
        super().__init__(parent)
        self._df = df.copy(deep=True) if isinstance(df, pd.DataFrame) else df
        self._config = config
        self._source_label = source_label
        self._instrument = instrument
        self._backtest_kwargs = backtest_kwargs

    def run(self) -> None:  # noqa: D102 — QThread override
        try:
            result = run_ga_search(
                self._df,
                config=self._config,
                instrument=self._instrument,
                **self._backtest_kwargs,
            )
            self.success.emit(result, self._source_label)
        except Exception as exc:
            self.failure.emit(str(exc))

from app.services.gp_service import GPSearchConfig, GPSearchResult, run_gp_search

class GPWorker(QThread):
    """Background thread that executes :func:`run_gp_search`.

    Signals
    -------
    success(GPSearchResult, str)
        Emitted with (result, source_label) on successful completion.
    failure(str)
        Emitted with an error message string on exception.
    finished()
        Always emitted when the thread exits (inherited from QThread).
    """

    success = Signal(object, str)   # (GPSearchResult, source_label)
    failure = Signal(str)           # error message

    def __init__(
        self,
        df: pd.DataFrame,
        config: GPSearchConfig,
        source_label: str,
        *,
        instrument: InstrumentProfile | None = None,
        parent=None,
        **backtest_kwargs,
    ) -> None:
        super().__init__(parent)
        self._df = df.copy(deep=True) if isinstance(df, pd.DataFrame) else df
        self._config = config
        self._source_label = source_label
        self._instrument = instrument
        self._backtest_kwargs = backtest_kwargs

    def run(self) -> None:  # noqa: D102 — QThread override
        try:
            result = run_gp_search(
                self._df,
                config=self._config,
                instrument=self._instrument,
                **self._backtest_kwargs,
            )
            self.success.emit(result, self._source_label)
        except Exception as exc:
            self.failure.emit(str(exc))
