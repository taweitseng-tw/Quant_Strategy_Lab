"""ArchiveImporter — verification skeleton for reproducible experiment archives.

Reads and validates manifest schema version compatibility, runs integrity checks,
and returns an import plan. No database or filesystem mutations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Any

from archive.manifest import ArchiveManifest, ArchiveIntegrityError


class ArchiveImporterError(Exception):
    """Base exception for all ArchiveImporter errors."""


class IncompatibleSchemaError(ArchiveImporterError):
    """Raised when the archive schema version is incompatible, missing, or malformed."""


class IImportCollisionDetector(Protocol):
    """Protocol for checking database collisions during archive import preview."""

    def strategy_exists(self, strategy_uid: str) -> bool:
        """Check if a strategy with the given UID already exists."""
        ...

    def dataset_exists(self, dataset_id: int, symbol: str, timeframe: str) -> bool:
        """Check if a dataset with the given ID or symbol/timeframe properties already exists."""
        ...


@dataclass(frozen=True)
class ArchiveImportPreview:
    """Immutable preview summary of an archive import dry-run.

    Fields
    ------
    plan : ArchiveImportPlan
        The verified import plan.
    strategy_uid : str
        The unique identifier of the strategy to be imported.
    strategy_name : str
        The name of the strategy to be imported.
    dataset_id : int
        The ID of the dataset reference.
    dataset_symbol : str
        The market symbol of the dataset.
    dataset_timeframe : str
        The timeframe of the dataset.
    validation_passed : bool
        Whether the strategy validation result passed.
    strategy_collision : bool
        True if the strategy UID already exists in the workspace.
    dataset_collision : bool
        True if the dataset already exists.
    """
    plan: ArchiveImportPlan
    strategy_uid: str
    strategy_name: str
    dataset_id: int
    dataset_symbol: str
    dataset_timeframe: str
    validation_passed: bool
    strategy_collision: bool
    dataset_collision: bool


@dataclass(frozen=True)
class ArchiveImportPlan:
    """Immutable import plan and verification summary for an archive.

    Fields
    ------
    archive_root : Path
        Filesystem path to the verified archive directory.
    archive_version : str
        The schema version of the archive.
    experiment_name : str
        Human-readable name of the archived experiment.
    files : tuple[str, ...]
        List of files contained in the archive.
    verified : bool
        True if all integrity checks passed.
    config_snapshot_files : tuple[str, ...]
        Subset of *files* that match known project config filenames
        (instruments.json, sessions.json, app_settings.json).
        Empty tuple when no config files are present.
    """
    archive_root: Path
    archive_version: str
    experiment_name: str
    files: tuple[str, ...]
    verified: bool
    config_snapshot_files: tuple[str, ...] = ()


def _get_major_version(version_str: str | None) -> int:
    """Extract and validate the major version from an archive version string."""
    if not version_str or not isinstance(version_str, str):
        raise IncompatibleSchemaError("Archive version is missing or invalid.")
    
    parts = version_str.strip().split(".")
    if not parts or not parts[0]:
        raise IncompatibleSchemaError(f"Archive version '{version_str}' is malformed.")
    
    major_str = parts[0]
    if not major_str.isdigit():
        raise IncompatibleSchemaError(f"Archive version '{version_str}' has non-numeric major version.")
    
    return int(major_str)


# Known project config filenames that may appear as archive snapshot files.
_CONFIG_SNAPSHOT_NAMES: frozenset[str] = frozenset({
    "instruments.json",
    "sessions.json",
    "app_settings.json",
})


class ArchiveImporter:
    """Verification skeleton for importing reproducible strategy archives.

    Parameters
    ----------
    archive_dir : str | Path
        Path to the archive folder root.
    """

    def __init__(self, archive_dir: str | Path) -> None:
        self.archive_dir = Path(archive_dir)

    def verify(self) -> ArchiveImportPlan:
        """Locate, read, and verify the archive directory.

        Returns
        -------
        ArchiveImportPlan
            The verification result and import plan if successful.

        Raises
        ------
        ArchiveImporterError
            If the manifest is missing, malformed, or has an incompatible version.
        ArchiveIntegrityError
            If file integrity verification fails.
        """
        manifest_path = self.archive_dir / ArchiveManifest.MANIFEST_FILENAME
        if not manifest_path.is_file():
            raise ArchiveImporterError(
                f"Manifest file '{ArchiveManifest.MANIFEST_FILENAME}' not found in '{self.archive_dir}'"
            )

        try:
            manifest = ArchiveManifest.read_from_folder(self.archive_dir)
        except KeyError as e:
            if "archive_version" in str(e):
                raise IncompatibleSchemaError("Archive version is missing in manifest.") from e
            raise ArchiveImporterError(f"Failed to read or parse manifest: missing field {e}") from e
        except Exception as e:
            raise ArchiveImporterError(f"Failed to read or parse manifest: {e}") from e

        # Validate schema version compatibility (major version must be exactly 1)
        major = _get_major_version(manifest.archive_version)
        if major != 1:
            raise IncompatibleSchemaError(
                f"Incompatible archive version '{manifest.archive_version}'. Supported major version is 1."
            )

        # Delegate content verification
        from archive.verifier import ArchiveVerifier
        verifier = ArchiveVerifier(manifest, self.archive_dir)
        verified = verifier.verify_all()

        return ArchiveImportPlan(
            archive_root=self.archive_dir,
            archive_version=manifest.archive_version,
            experiment_name=manifest.experiment_name,
            files=tuple(manifest.files),
            verified=verified,
            config_snapshot_files=tuple(
                f for f in manifest.files if f in _CONFIG_SNAPSHOT_NAMES
            ),
        )

    def build_preview(self, collision_detector: IImportCollisionDetector | None = None) -> ArchiveImportPreview:
        """Verify the archive and build a read-only import preview/dry-run summary.

        Parameters
        ----------
        collision_detector : IImportCollisionDetector or None
            Optional read-only collision detector to check strategy and dataset status.

        Returns
        -------
        ArchiveImportPreview
            The immutable preview/summary.

        Raises
        ------
        ArchiveImporterError
            If any payload file cannot be read or is malformed JSON.
        ArchiveIntegrityError
            If verification fails.
        """
        # 1. Verification phase (propagates ArchiveIntegrityError or ArchiveImporterError)
        plan = self.verify()

        # 2. Read and parse strategy.json
        strategy_path = self.archive_dir / "strategy.json"
        try:
            strategy_data = json.loads(strategy_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ArchiveImporterError(f"Failed to read or parse strategy payload: {e}") from e

        # 3. Read and parse dataset_meta.json
        dataset_meta_path = self.archive_dir / "dataset_meta.json"
        try:
            dataset_data = json.loads(dataset_meta_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ArchiveImporterError(f"Failed to read or parse dataset metadata: {e}") from e

        # 4. Read and parse validation_result.json
        val_path = self.archive_dir / "validation_result.json"
        try:
            val_data = json.loads(val_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ArchiveImporterError(f"Failed to read or parse validation result: {e}") from e

        # Extract values
        strategy_uid = strategy_data.get("strategy_uid")
        if not strategy_uid:
            raise ArchiveImporterError("strategy.json is missing required field 'strategy_uid'")

        strategy_name = strategy_data.get("name") or plan.experiment_name

        dataset_id = dataset_data.get("id")
        dataset_symbol = dataset_data.get("symbol")
        dataset_timeframe = dataset_data.get("timeframe")
        if dataset_id is None or dataset_symbol is None or dataset_timeframe is None:
            raise ArchiveImporterError(
                "dataset_meta.json is missing required fields (id, symbol, timeframe)"
            )

        validation_passed = val_data.get("passed")
        if validation_passed is None:
            raise ArchiveImporterError("validation_result.json is missing required field 'passed'")

        # 5. Collision checks
        strategy_collision = False
        dataset_collision = False
        if collision_detector is not None:
            strategy_collision = collision_detector.strategy_exists(strategy_uid)
            dataset_collision = collision_detector.dataset_exists(
                dataset_id, dataset_symbol, dataset_timeframe
            )

        return ArchiveImportPreview(
            plan=plan,
            strategy_uid=strategy_uid,
            strategy_name=strategy_name,
            dataset_id=dataset_id,
            dataset_symbol=dataset_symbol,
            dataset_timeframe=dataset_timeframe,
            validation_passed=validation_passed,
            strategy_collision=strategy_collision,
            dataset_collision=dataset_collision,
        )
