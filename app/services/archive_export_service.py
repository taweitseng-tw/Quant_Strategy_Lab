"""Archive export service — application-layer boundary for archive export.

Wraps ArchiveBuilder + ArchiveExporter, injecting repository-like data
sources and handling failure modes at the service level.  No PySide6 or
UI imports.
"""

from __future__ import annotations

from pathlib import Path

from archive.builder import (
    ArchiveBuilder,
    ArchiveBuilderError,
    ArchiveDataSource,
    MissingStrategyError,
    MissingDatasetError,
    MissingDatasetSnapshotError,
    MissingValidationResultError,
    MissingDisclaimerError,
    StrategyValidationFailedError,
)
from archive.exporter import ArchiveExporter, ArchiveExporterError


_DEFAULT_DISCLAIMER = (
    "This archive is for research and backtesting purposes only. "
    "Backtested performance does not guarantee future results. "
    "Not financial advice. No live trading."
)


class ArchiveExportServiceError(Exception):
    """Base exception for ArchiveExportService failures.

    The ``__cause__`` chain carries the underlying exception from
    the Builder or Exporter.
    """


def _disclosure() -> str:
    """Return the standard non-financial-advice disclaimer."""
    return _DEFAULT_DISCLAIMER


class ArchiveExportService:
    """Application-level orchestration for archive export.

    Parameters
    ----------
    data_source : ArchiveDataSource
        Provides strategy, dataset, and validation results.
    """

    def __init__(self, data_source: ArchiveDataSource) -> None:
        self._data_source = data_source
        self._builder = ArchiveBuilder(data_source)

    def export_strategy_archive(
        self,
        strategy_uid: str,
        dataset_snapshot_path: str,
        output_dir: str | Path,
        disclaimer_text: str | None = None,
        experiment_name: str | None = None,
        config_sources: dict[str, str] | None = None,
    ) -> Path:
        """Build and export a strategy archive to *output_dir*.

        Parameters
        ----------
        strategy_uid : str
        dataset_snapshot_path : str
            Filesystem path to the CSV dataset snapshot.
        output_dir : str or Path
            Destination directory for the archive folder.
        disclaimer_text : str or None
            Defaults to the standard research disclaimer.
        experiment_name : str or None
            Defaults to the strategy name.
        config_sources : dict or None
            Optional mapping ``{archive_filename: source_path}`` for
            additional files to copy (e.g. project config files).
            Missing source paths are silently skipped.

        Returns
        -------
        Path
            The output directory containing ``manifest.json`` and exported files.

        Raises
        ------
        ArchiveExportServiceError
            If any required archive input is missing or the export fails.
            The underlying error is preserved in ``__cause__``.
        """
        exporter = ArchiveExporter(self._builder, self._data_source)
        disclaimer = disclaimer_text or _disclosure()
        try:
            return exporter.export(
                strategy_uid=strategy_uid,
                dataset_snapshot_path=dataset_snapshot_path,
                disclaimer_text=disclaimer,
                output_dir=Path(output_dir),
                experiment_name=experiment_name,
                config_sources=config_sources,
            )
        except (ArchiveBuilderError, ArchiveExporterError) as exc:
            raise ArchiveExportServiceError(
                f"Failed to export archive for strategy '{strategy_uid}': {exc}"
            ) from exc
