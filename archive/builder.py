"""ArchiveBuilder — first-pass collector for reproducible experiment archives.

Collects strategy, dataset, validation, and disclaimer metadata from an
``ArchiveDataSource`` (or caller-provided values) and produces an
``ArchiveManifest``.  Does NOT write archive folders, copy files, or
produce zip output.
"""

from __future__ import annotations

import datetime
from typing import Any, Protocol

from archive.manifest import ArchiveManifest


# ---------------------------------------------------------------------------
# Exception hierarchy for hard failures
# ---------------------------------------------------------------------------


class ArchiveBuilderError(Exception):
    """Base for all ArchiveBuilder hard-failure errors."""


class MissingStrategyError(ArchiveBuilderError):
    """Strategy not found or lacks valid JSON definition."""


class MissingDatasetError(ArchiveBuilderError):
    """Dataset metadata not found."""


class MissingDatasetSnapshotError(ArchiveBuilderError):
    """Dataset snapshot file does not exist."""


class MissingValidationResultError(ArchiveBuilderError):
    """Validation result not found for strategy."""


class StrategyValidationFailedError(ArchiveBuilderError):
    """Validation result indicates that the strategy failed validation."""


class MissingDisclaimerError(ArchiveBuilderError):
    """Disclaimer text was not provided."""


# ---------------------------------------------------------------------------
# Data-source protocol
# ---------------------------------------------------------------------------


class ArchiveDataSource(Protocol):
    """Interface for repository reads needed by ArchiveBuilder."""

    def get_strategy(self, strategy_uid: str) -> dict[str, Any] | None: ...
    def get_dataset(self, dataset_id: int) -> dict[str, Any] | None: ...
    def get_validation_result(self, strategy_uid: str) -> dict[str, Any] | None: ...


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


class ArchiveBuilder:
    """First-pass collector that produces an ``ArchiveManifest``.

    The builder does NOT write folders, zip archives, or copy files.
    It only gathers metadata, validates required inputs, and returns
    a manifest.
    """

    ARCHIVE_VERSION = "1.0.0"

    def __init__(self, data_source: ArchiveDataSource) -> None:
        self._data = data_source

    def build(
        self,
        strategy_uid: str,
        dataset_snapshot_path: str,
        disclaimer_text: str,
        experiment_name: str | None = None,
    ) -> ArchiveManifest:
        """Collect required materials and produce an ``ArchiveManifest``.

        Parameters
        ----------
        strategy_uid : str
        dataset_snapshot_path : str
            Filesystem path to the CSV snapshot (must exist on disk).
        disclaimer_text : str
            Non-empty financial-disclaimer string.
        experiment_name : str or None
            Defaults to the strategy name.

        Returns
        -------
        ArchiveManifest

        Raises
        ------
        MissingStrategyError
        MissingDatasetError
        MissingDatasetSnapshotError
        MissingValidationResultError
        MissingDisclaimerError
        """
        from pathlib import Path

        # -- strategy -------------------------------------------------------
        strategy = self._data.get_strategy(strategy_uid)
        if strategy is None:
            raise MissingStrategyError(
                f"Strategy '{strategy_uid}' not found in data source."
            )
        strategy_json = strategy.get("strategy_json")
        if not strategy_json:
            raise MissingStrategyError(
                f"Strategy '{strategy_uid}' has no strategy_json."
            )

        # -- dataset --------------------------------------------------------
        dataset_id = strategy.get("dataset_id")
        if not dataset_id:
            raise MissingDatasetError(
                f"Strategy '{strategy_uid}' has no dataset_id."
            )
        dataset = self._data.get_dataset(dataset_id)
        if dataset is None:
            raise MissingDatasetError(
                f"Dataset id={dataset_id} not found for strategy '{strategy_uid}'."
            )

        # -- dataset snapshot file must exist --------------------------------
        snap = Path(dataset_snapshot_path)
        if not snap.is_file():
            raise MissingDatasetSnapshotError(
                f"Dataset snapshot file not found: {dataset_snapshot_path}"
            )

        # -- validation result -----------------------------------------------
        validation = self._data.get_validation_result(strategy_uid)
        if validation is None:
            raise MissingValidationResultError(
                f"No validation result for strategy '{strategy_uid}'."
            )
        if validation.get("passed") is False:
            raise StrategyValidationFailedError(
                f"Strategy '{strategy_uid}' failed validation."
            )

        # -- disclaimer ------------------------------------------------------
        if not disclaimer_text or not disclaimer_text.strip():
            raise MissingDisclaimerError(
                "Disclaimer text is empty or missing."
            )

        # -- build manifest metadata -----------------------------------------
        now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        name = experiment_name or strategy.get("name", strategy_uid)

        # Required relative file paths for the future archive folder structure
        files: list[str] = [
            "disclaimer.txt",
            "strategy.json",
            "dataset_meta.json",
            "validation_result.json",
            "ohlcv_snapshot.csv",
        ]
        
        # content_hashes remains empty in this first-pass builder phase, as it is a
        # metadata collector. The hashes will be computed and filled in by the
        # future ArchiveExporter after writing the actual files to disk.
        content_hashes: dict[str, str] = {}

        return ArchiveManifest(
            archive_version=self.ARCHIVE_VERSION,
            experiment_name=name,
            generated_at=now,
            generator_version=strategy.get("generator_version", "unknown"),
            files=files,
            content_hashes=content_hashes,
            disclaimer_path="disclaimer.txt",
        )
