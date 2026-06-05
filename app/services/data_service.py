"""Service layer for Data operations — Task 012 / Task 019A / Task 032D."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
import pandas as pd

from core.models.dataset import DatasetMeta
from data_engine.importers.csv_importer import CsvImporter
from data_engine.quality_checker import DataQualityReport, check_quality
from repository.dataset_repo import DatasetRepository
from repository.db import DatabaseManager

logger = logging.getLogger(__name__)


class DataService:
    """Service to handle importing, loading, and slicing of datasets.

    Delegates parsing to CsvImporter and runs data quality checks after
    normalization.  When a :class:`DatabaseManager` is provided via
    :meth:`set_db`, imported :class:`DatasetMeta` is automatically persisted
    to the active project's SQLite database.

    If no active project is available, uses a temporary directory as the
    project root for local file persistence and skips database writes.
    """

    def __init__(self, project_path: Path | str | None = None) -> None:
        self.project_path: Path | None = None
        self.importer = CsvImporter()
        self._db: DatabaseManager | None = None
        self._dataset_repo: DatasetRepository | None = None

        if project_path:
            self.set_project_path(project_path)

    def set_project_path(self, path: Path | str | None) -> None:
        """Set the active project path."""
        self.project_path = Path(path).resolve() if path else None

    def set_db(self, db: DatabaseManager | None) -> None:
        """Set (or clear) the database handle for metadata persistence.

        When set, every call to :meth:`import_file` will also persist
        the :class:`DatasetMeta` into the project database.  Pass ``None``
        to disable persistence (e.g. when no project is open).
        """
        self._db = db
        self._dataset_repo = DatasetRepository(db) if db else None

    def import_file(
        self,
        source_path: Path | str,
        symbol: str = "RESEARCH",
        timeframe: str = "1min",
    ) -> tuple[pd.DataFrame, DatasetMeta, DataQualityReport]:
        """Import a CSV/TXT OHLCV file and run quality checks.

        Parameters
        ----------
        source_path : Path or str
        symbol : str
        timeframe : str

        Returns
        -------
        tuple
            (normalized_df, dataset_meta, quality_report)

            - **quality_report.passed** is ``True`` when no errors were found.
              Warning-only reports (gaps, outliers) still pass and the data
              is usable for research.
            - When *quality_report.passed* is ``False``, callers should
              inspect ``quality_report.errors`` before using the data.
        """
        source = Path(source_path).resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Source file not found: {source}")

        # Fallback to temp directory if no active project is open
        root_dir = self.project_path
        if root_dir is None:
            temp_root = Path(tempfile.gettempdir()) / "qsl_temp_project"
            temp_root.mkdir(parents=True, exist_ok=True)
            root_dir = temp_root
            logger.info(f"No active project. Using temp project root for normalization: {root_dir}")

        normalized_df, meta = self.importer.import_file(
            source_path=source,
            project_root=root_dir,
            symbol=symbol,
            timeframe=timeframe,
        )

        # Run quality checks on the normalized output.
        quality_report = check_quality(
            normalized_df,
            expected_freq_minutes=_timeframe_to_minutes(timeframe),
            outlier_pct_threshold=5.0,
        )

        if not quality_report.passed:
            logger.warning(
                f"Data quality check FAILED for {source}: "
                f"{quality_report.errors}"
            )
        elif quality_report.warnings:
            logger.info(
                f"Data quality check passed with warnings for {source}: "
                f"{quality_report.warnings}"
            )

        # ── Persist metadata when an active project database is available ──
        if self._dataset_repo is not None:
            try:
                self._dataset_repo.save(meta)
                logger.info(f"Dataset metadata persisted: {meta.name}")
            except Exception:
                logger.exception("Failed to persist dataset metadata — continuing in-memory only.")

        return normalized_df, meta, quality_report

    @staticmethod
    def get_render_subset(df: pd.DataFrame, max_rows: int = 2000) -> pd.DataFrame:
        """Slice a DataFrame to the most recent N rows for responsive UI rendering."""
        if len(df) > max_rows:
            return df.tail(max_rows).copy()
        return df


def _timeframe_to_minutes(tf: str) -> int | None:
    """Convert a timeframe string like '1min' or '5min' to integer minutes."""
    tf_lower = tf.lower().replace(" ", "")
    for suffix in ("min", "m"):
        if tf_lower.endswith(suffix):
            try:
                return int(tf_lower[:-len(suffix)])
            except ValueError:
                return None
    return None
