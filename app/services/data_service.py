"""Service layer for Data operations."""

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
    normalization. When a DatabaseManager is provided via set_db, imported
    DatasetMeta is automatically persisted to the active project's SQLite
    database.
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
        """Set or clear the database handle for metadata persistence."""
        self._db = db
        self._dataset_repo = DatasetRepository(db) if db else None

    def import_file(
        self,
        source_path: Path | str,
        symbol: str = "RESEARCH",
        timeframe: str = "1min",
    ) -> tuple[pd.DataFrame, DatasetMeta, DataQualityReport]:
        """Import a CSV/TXT OHLCV file and run quality checks."""
        source = Path(source_path).resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Source file not found: {source}")

        root_dir = self.project_path
        if root_dir is None:
            temp_root = Path(tempfile.gettempdir()) / "qsl_temp_project"
            temp_root.mkdir(parents=True, exist_ok=True)
            root_dir = temp_root
            logger.info(
                "No active project. Using temp project root for normalization: %s",
                root_dir,
            )

        normalized_df, meta = self.importer.import_file(
            source_path=source,
            project_root=root_dir,
            symbol=symbol,
            timeframe=timeframe,
        )

        quality_report = check_quality(
            normalized_df,
            expected_freq_minutes=_timeframe_to_minutes(timeframe),
            outlier_pct_threshold=5.0,
        )

        if not quality_report.passed:
            logger.warning(
                "Data quality check FAILED for %s: %s",
                source,
                quality_report.errors,
            )
        elif quality_report.warnings:
            logger.info(
                "Data quality check passed with warnings for %s: %s",
                source,
                quality_report.warnings,
            )

        if self._dataset_repo is not None:
            try:
                self._dataset_repo.save(meta)
                logger.info("Dataset metadata persisted: %s", meta.name)
            except Exception:
                logger.exception(
                    "Failed to persist dataset metadata; continuing in-memory only."
                )

        return normalized_df, meta, quality_report

    def get_dataset_raw_by_id(self, dataset_id: int) -> dict | None:
        """Return a dataset row as a raw dict, or None."""
        if self._dataset_repo is None:
            return None
        return self._dataset_repo.get_raw_by_id(dataset_id)

    @staticmethod
    def get_render_subset(df: pd.DataFrame, max_rows: int = 2000) -> pd.DataFrame:
        """Slice a DataFrame to the most recent N rows for responsive UI rendering."""
        if len(df) > max_rows:
            return df.tail(max_rows).copy()
        return df

    @staticmethod
    def get_expected_format_guide() -> str:
        """Return a human-readable description of the expected OHLCV file format."""
        return (
            "Columns: Date, Time, Open, High, Low, Close, TotalVolume\n"
            "Date: YYYY/MM/DD or YYYY-MM-DD\n"
            "Time: HH:MM:SS  |  OHLC: numeric prices  |  TotalVolume: integer\n\n"
            "Example:\n"
            "2026/01/01,09:00:00,100.0,105.0,95.0,101.0,1000"
        )

    @staticmethod
    def get_actionable_import_error(e: Exception) -> str:
        """Convert a raw import exception into an actionable user-facing message."""
        msg = str(e)
        if isinstance(e, FileNotFoundError):
            return (
                f"File not found: {msg}\n"
                "Please check that the file exists and try again."
            )
        if "no data rows" in msg.lower():
            return (
                "The file appears to be empty or contains no data rows.\n"
                "Please check the file content and try again."
            )
        if "failed to read csv" in msg.lower() or "parsing" in msg.lower():
            return (
                f"Could not read the file as CSV: {msg}\n"
                "Ensure the file is a plain CSV or TXT file with OHLCV columns "
                "(Date, Time, Open, High, Low, Close, TotalVolume)."
            )
        if "missing" in msg.lower() or "column" in msg.lower():
            return (
                f"Missing expected columns: {msg}\n"
                "The file must contain: Date, Time, Open, High, Low, Close, TotalVolume."
            )
        if "normalizererror" in msg.lower() or "normalize" in msg.lower():
            return (
                f"Data normalization failed: {msg}\n"
                "Check that numeric columns (Open, High, Low, Close) contain valid numbers."
            )
        return (
            f"Import failed: {msg}\n"
            "Check that the file is a valid OHLCV CSV/TXT file with the expected format."
        )

    @staticmethod
    def format_quality_evidence(quality: DataQualityReport) -> str:
        """Format a DataQualityReport into a compact multi-line summary string.

        Returns a tooltip-ready string with pass/fail status, warning/error
        counts, and the first few issue descriptions.
        """
        lines: list[str] = []
        if quality.passed:
            lines.append("Quality: Passed")
        else:
            lines.append(f"Quality: Failed ({len(quality.errors)} error(s))")
        if quality.warnings:
            lines.append(f"{len(quality.warnings)} warning(s):")
            for w in quality.warnings[:3]:
                lines.append(f"  - {w}")
            if len(quality.warnings) > 3:
                lines.append(f"  ... and {len(quality.warnings) - 3} more")
        if not quality.passed:
            lines.append(f"{len(quality.errors)} error(s):")
            for e in quality.errors[:3]:
                lines.append(f"  - {e}")
            if len(quality.errors) > 3:
                lines.append(f"  ... and {len(quality.errors) - 3} more")
        return "\n".join(lines)


def _timeframe_to_minutes(tf: str) -> int | None:
    """Convert a timeframe string like '1min' or '5min' to integer minutes."""
    tf_lower = tf.lower().replace(" ", "")
    for suffix in ("min", "m"):
        if tf_lower.endswith(suffix):
            try:
                return int(tf_lower[: -len(suffix)])
            except ValueError:
                return None
    return None
