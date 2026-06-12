"""Background workers for Quant Strategy Lab — runs long operations off the UI thread."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

import pandas as pd

from app.services.data_service import DataService
from core.models.dataset import DatasetMeta
from data_engine.quality_checker import DataQualityReport


class ImportWorker(QThread):
    """Background thread that executes :func:`DataService.import_file`.

    Signals
    -------
    progress_updated(str)
        Emitted with a human-readable stage name (e.g. "Reading file...",
        "Importing and normalizing data...", "Checking quality...") as the
        import progresses.  Connect this to update UI without blocking.
    success(pd.DataFrame, DatasetMeta, DataQualityReport)
        Emitted on successful import.
    failure(str)
        Emitted with an error message on exception.
    """

    progress_updated = Signal(str)
    success = Signal(object, object, object)  # df, meta, quality
    failure = Signal(str)

    def __init__(
        self,
        file_path: str | Path,
        data_service: DataService,
        symbol: str = "RESEARCH",
        timeframe: str = "1min",
        session_start: str | None = None,
        session_end: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._file_path = file_path
        self._project_path = getattr(data_service, "project_path", None)
        self._symbol = symbol
        self._timeframe = timeframe
        self._session_start = session_start
        self._session_end = session_end

    def run(self) -> None:
        try:
            self.progress_updated.emit("Reading file...")
            source_path = Path(self._file_path)
            if not source_path.is_file():
                raise FileNotFoundError(f"Source file not found: {source_path}")

            self.progress_updated.emit("Importing, normalizing, and checking quality...")
            worker_service = DataService(project_path=self._project_path)
            df, meta, quality = worker_service.import_file(
                self._file_path,
                symbol=self._symbol,
                timeframe=self._timeframe,
                session_start=self._session_start,
                session_end=self._session_end,
            )

            self.progress_updated.emit("Finalizing...")
            self.success.emit(df, meta, quality)
        except Exception as exc:
            self.failure.emit(DataService.get_actionable_import_error(exc))


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

    def run(self) -> None:
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

    def run(self) -> None:
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


from core.models.strategy import Strategy
from core.models.instrument import InstrumentProfile
from app.services.validation_pipeline_service import PipelineConfig, run_validation_pipeline


class ValidationWorker(QThread):
    """Background thread that executes :func:`run_validation_pipeline`.

    Signals
    -------
    progress_updated(str)
        Coarse stage label such as "Splitting data..." or "Running Monte Carlo...".
    success(object)
        Emitted with the ``PipelineResult`` on successful completion.
    failure(str)
        Emitted with an error message on exception.
    """

    progress_updated = Signal(str)
    success = Signal(object)
    failure = Signal(str)

    def __init__(
        self,
        df: pd.DataFrame,
        strategy: Strategy,
        config: PipelineConfig,
        *,
        instrument: InstrumentProfile | None = None,
        data_source: str = "",
        commission: float = 2.0,
        is_mock: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._df = df.copy(deep=True) if isinstance(df, pd.DataFrame) else df
        self._strategy = strategy
        self._config = config
        self._instrument = instrument
        self._data_source = data_source
        self._commission = commission
        self._is_mock = is_mock
        self._stop_requested = False

    def stop(self) -> None:
        """Request the worker to stop at the next boundary check."""
        self._stop_requested = True

    def run(self) -> None:
        try:
            self.progress_updated.emit("Splitting data and running backtest...")
            if self._stop_requested:
                self.failure.emit("Validation cancelled by user.")
                return
            result = run_validation_pipeline(
                self._df,
                self._strategy,
                config=self._config,
                instrument=self._instrument,
                data_source=self._data_source,
                commission=self._commission,
            )
            if self._stop_requested:
                self.failure.emit("Validation cancelled by user.")
                return
            self.progress_updated.emit("Finalizing...")
            self.success.emit(result)
        except Exception as exc:
            self.failure.emit(str(exc))
