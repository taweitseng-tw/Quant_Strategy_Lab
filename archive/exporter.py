"""ArchiveExporter — folder writer first pass for reproducible experiment archives.

Takes an ArchiveBuilder and a data source, exports strategy artifacts to a
folder, computes SHA-256 hashes, and writes the manifest.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    from archive.builder import ArchiveBuilder, ArchiveDataSource
    from archive.manifest import ArchiveManifest


class ArchiveExporterError(Exception):
    """Base exception for all ArchiveExporter errors."""


class ExportDataUnavailableError(ArchiveExporterError):
    """Raised when data needed for export is missing or unavailable in the data source."""


class ArchiveExporter:
    """Exports experiment details to a folder and completes the manifest."""

    def __init__(self, builder: ArchiveBuilder, data_source: ArchiveDataSource) -> None:
        self.builder = builder
        self.data_source = data_source

    def export(
        self,
        strategy_uid: str,
        dataset_snapshot_path: str,
        disclaimer_text: str,
        output_dir: str | Path,
        experiment_name: str | None = None,
    ) -> Path:
        """Export all strategy materials to output_dir and write manifest.json.

        Parameters
        ----------
        strategy_uid : str
        dataset_snapshot_path : str
            File path to the CSV dataset snapshot.
        disclaimer_text : str
        output_dir : str or Path
            The destination directory.
        experiment_name : str or None

        Returns
        -------
        Path
            The path to the output directory.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. Run the builder first to validate all required parameters and data.
        # This will raise any validation/missing resource errors.
        manifest = self.builder.build(
            strategy_uid=strategy_uid,
            dataset_snapshot_path=dataset_snapshot_path,
            disclaimer_text=disclaimer_text,
            experiment_name=experiment_name,
        )

        # Retrieve backend details for exporting
        strategy = self.data_source.get_strategy(strategy_uid)
        if strategy is None:
            raise ExportDataUnavailableError(
                f"Strategy '{strategy_uid}' is missing or unavailable for export."
            )
        dataset_id = strategy.get("dataset_id")
        if not dataset_id:
            raise ExportDataUnavailableError(
                f"Strategy '{strategy_uid}' has no dataset_id in the data source."
            )
        dataset = self.data_source.get_dataset(dataset_id)
        if dataset is None:
            raise ExportDataUnavailableError(
                f"Dataset id={dataset_id} is missing or unavailable for export."
            )
        validation = self.data_source.get_validation_result(strategy_uid)
        if validation is None:
            raise ExportDataUnavailableError(
                f"Validation result for strategy '{strategy_uid}' is missing or unavailable for export."
            )

        # 2. Write disclaimer.txt
        disclaimer_file = output_path / "disclaimer.txt"
        disclaimer_bytes = disclaimer_text.encode("utf-8")
        disclaimer_file.write_bytes(disclaimer_bytes)

        # 3. Write strategy.json
        strategy_file = output_path / "strategy.json"
        strategy_json = strategy["strategy_json"]
        if isinstance(strategy_json, str):
            strategy_bytes = strategy_json.encode("utf-8")
        else:
            strategy_bytes = json.dumps(strategy_json, indent=2).encode("utf-8")
        strategy_file.write_bytes(strategy_bytes)

        # 4. Write dataset_meta.json
        dataset_meta_file = output_path / "dataset_meta.json"
        dataset_meta_bytes = json.dumps(dataset, indent=2).encode("utf-8")
        dataset_meta_file.write_bytes(dataset_meta_bytes)

        # 5. Write validation_result.json
        val_file = output_path / "validation_result.json"
        val_bytes = json.dumps(validation, indent=2).encode("utf-8")
        val_file.write_bytes(val_bytes)

        # 6. Copy dataset CSV snapshot
        snapshot_dest = output_path / "ohlcv_snapshot.csv"
        shutil.copy2(dataset_snapshot_path, snapshot_dest)
        snapshot_bytes = snapshot_dest.read_bytes()

        # 7. Compute SHA-256 hashes of the exact written bytes
        manifest.content_hashes = {
            "disclaimer.txt": hashlib.sha256(disclaimer_bytes).hexdigest(),
            "strategy.json": hashlib.sha256(strategy_bytes).hexdigest(),
            "dataset_meta.json": hashlib.sha256(dataset_meta_bytes).hexdigest(),
            "validation_result.json": hashlib.sha256(val_bytes).hexdigest(),
            "ohlcv_snapshot.csv": hashlib.sha256(snapshot_bytes).hexdigest(),
        }

        # 8. Write manifest.json
        manifest.write_to_folder(output_path)

        return output_path
