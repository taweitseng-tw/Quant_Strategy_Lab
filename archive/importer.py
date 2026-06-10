"""ArchiveImporter — verification skeleton for reproducible experiment archives.

Reads and validates manifest schema version compatibility, runs integrity checks,
and returns an import plan. No database or filesystem mutations.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
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
class ConfigSnapshotEvidence:
    """Read-only manifest evidence for one archived project config snapshot."""

    filename: str
    sha256: str


@dataclass(frozen=True)
class ConfigSnapshotComparison:
    """Read-only comparison result for one archived config snapshot vs current project config.

    Fields
    ------
    filename : str
        The config filename (e.g. instruments.json).
    status : str
        One of: ``match``, ``different``, ``missing_current``, ``no_archive_evidence``.
    archive_sha256 : str or None
        The SHA-256 hex digest from the archive manifest, if available.
    current_sha256 : str or None
        The SHA-256 hex digest of the current project config file on disk,
        or None if the file does not exist.
    """
    filename: str
    status: str = "unknown"
    archive_sha256: str | None = None
    current_sha256: str | None = None


@dataclass(frozen=True)
class ConfigSnapshotComparisonSummary:
    """Immutable summary counts for config snapshot comparisons.

    Fields
    ------
    total : int
        Total number of known config filenames compared (always 3).
    match : int
        Count of comparisons with status ``match``.
    different : int
        Count of comparisons with status ``different``.
    missing_current : int
        Count of comparisons with status ``missing_current``.
    no_archive_evidence : int
        Count of comparisons with status ``no_archive_evidence``.
    """
    total: int = 0
    match: int = 0
    different: int = 0
    missing_current: int = 0
    no_archive_evidence: int = 0


@dataclass(frozen=True)
class ConfigSnapshotRestorePlanEntry:
    """Read-only evidence entry describing a recommended action for one
    config snapshot file during a future restore.

    Fields
    ------
    filename : str
        The config filename (e.g. instruments.json).
    comparison_status : str
        The raw comparison status from ``ConfigSnapshotComparison``.
    recommended_action : str
        One of:
        ``no_action_for_match``
        ``review_difference``
        ``can_restore_missing_current``
        ``no_archive_snapshot``
    reason : str
        Human-readable explanation of the recommendation.
    """
    filename: str
    comparison_status: str
    recommended_action: str
    reason: str


@dataclass(frozen=True)
class ConfigSnapshotRestorePlanSummary:
    """Immutable summary counts for a restore plan.

    Fields
    ------
    total : int
        Total number of restore plan entries.
    no_action_for_match : int
        Count of entries with action ``no_action_for_match``.
    review_difference : int
        Count of entries with action ``review_difference``.
    can_restore_missing_current : int
        Count of entries with action ``can_restore_missing_current``.
    no_archive_snapshot : int
        Count of entries with action ``no_archive_snapshot``.
    unknown : int
        Count of entries with any other action string.
    """
    total: int = 0
    no_action_for_match: int = 0
    review_difference: int = 0
    can_restore_missing_current: int = 0
    no_archive_snapshot: int = 0
    unknown: int = 0


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
    config_snapshot_comparisons : tuple[ConfigSnapshotComparison, ...]
        Optional read-only comparison between archived config snapshots and
        current project config files. Empty when no project config directory
        is provided.
    config_snapshot_summary : ConfigSnapshotComparisonSummary
        Immutable summary counts derived from *config_snapshot_comparisons*.
        Zero counts when no project config directory is provided.
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
    config_snapshot_comparisons: tuple[ConfigSnapshotComparison, ...] = ()
    config_snapshot_summary: ConfigSnapshotComparisonSummary = field(
        default_factory=ConfigSnapshotComparisonSummary
    )


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
    config_snapshot_evidence : tuple[ConfigSnapshotEvidence, ...]
        Immutable filename/hash evidence for every config snapshot file.
        Empty tuple when no config files are present.
    """
    archive_root: Path
    archive_version: str
    experiment_name: str
    files: tuple[str, ...]
    verified: bool
    config_snapshot_files: tuple[str, ...] = ()
    config_snapshot_evidence: tuple[ConfigSnapshotEvidence, ...] = ()


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


def _sha256_hex_for_file(path: Path) -> str:
    """Compute SHA-256 hex digest for a file on disk."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_config_snapshots(
    plan: ArchiveImportPlan,
    project_config_dir: Path,
) -> tuple[ConfigSnapshotComparison, ...]:
    """Compare archived config snapshot evidence against current project config files.

    For each known config filename, the result status is one of:

    * ``match`` — archive and current file exist with identical SHA-256.
    * ``different`` — archive and current file exist with different hashes.
    * ``missing_current`` — archive has evidence but no current file on disk.
    * ``no_archive_evidence`` — no archive evidence exists; current file
      may or may not exist (the comparison only reports what the archive
      knows about).

    Parameters
    ----------
    plan : ArchiveImportPlan
        A verified import plan with config snapshot evidence.
    project_config_dir : Path
        Path to the active project's ``config/`` directory.

    Returns
    -------
    tuple[ConfigSnapshotComparison, ...]
        One comparison per known config filename, in a stable order.
        Always has exactly 3 entries (one per known config name).
    """
    archive_evidence = {e.filename: e.sha256 for e in plan.config_snapshot_evidence}
    results: list[ConfigSnapshotComparison] = []

    for name in sorted(_CONFIG_SNAPSHOT_NAMES):
        archive_hash = archive_evidence.get(name)

        if archive_hash is None:
            results.append(ConfigSnapshotComparison(
                filename=name,
                status="no_archive_evidence",
                archive_sha256=None,
                current_sha256=None,
            ))
            continue

        current_path = project_config_dir / name
        if not current_path.is_file():
            results.append(ConfigSnapshotComparison(
                filename=name,
                status="missing_current",
                archive_sha256=archive_hash,
                current_sha256=None,
            ))
            continue

        current_hash = _sha256_hex_for_file(current_path)
        status = "match" if archive_hash == current_hash else "different"
        results.append(ConfigSnapshotComparison(
            filename=name,
            status=status,
            archive_sha256=archive_hash,
            current_sha256=current_hash,
        ))

    return tuple(results)


def summarize_config_comparisons(
    comparisons: tuple[ConfigSnapshotComparison, ...],
) -> ConfigSnapshotComparisonSummary:
    """Derive summary counts from a tuple of config snapshot comparisons.

    Parameters
    ----------
    comparisons : tuple[ConfigSnapshotComparison, ...]
        Comparison results from ``compare_config_snapshots()``.

    Returns
    -------
    ConfigSnapshotComparisonSummary
        Immutable summary with counts for each status.
    """
    match = sum(1 for c in comparisons if c.status == "match")
    different = sum(1 for c in comparisons if c.status == "different")
    missing_current = sum(1 for c in comparisons if c.status == "missing_current")
    no_archive_evidence = sum(
        1 for c in comparisons if c.status == "no_archive_evidence"
    )
    return ConfigSnapshotComparisonSummary(
        total=len(comparisons),
        match=match,
        different=different,
        missing_current=missing_current,
        no_archive_evidence=no_archive_evidence,
    )


def _comparison_to_dict(c: ConfigSnapshotComparison) -> dict[str, Any]:
    """Serialize one ConfigSnapshotComparison to a plain dict."""
    return {
        "filename": c.filename,
        "status": c.status,
        "archive_sha256": c.archive_sha256,
        "current_sha256": c.current_sha256,
    }


_RECOMMENDED_ACTION: dict[str, str] = {
    "match": "no_action_for_match",
    "different": "review_difference",
    "missing_current": "can_restore_missing_current",
    "no_archive_evidence": "no_archive_snapshot",
}

_REASON: dict[str, str] = {
    "match": "Archived config matches current project config; no action needed.",
    "different": "Archived config differs from current project config. Manual review recommended.",
    "missing_current": "Config file exists in the archive snapshot but is missing from the current project. Can be restored.",
    "no_archive_evidence": "No archived config snapshot exists for this file. Current project config is not affected.",
}


def build_config_restore_plan(
    comparisons: tuple[ConfigSnapshotComparison, ...],
) -> tuple[ConfigSnapshotRestorePlanEntry, ...]:
    """Derive a read-only restore-plan preview from config snapshot comparisons.

    Each comparison is mapped to a recommended action without writing any files.

    Parameters
    ----------
    comparisons : tuple[ConfigSnapshotComparison, ...]
        Comparison results from ``compare_config_snapshots()``.

    Returns
    -------
    tuple[ConfigSnapshotRestorePlanEntry, ...]
        One entry per comparison, in the same order.
    """
    return tuple(
        ConfigSnapshotRestorePlanEntry(
            filename=c.filename,
            comparison_status=c.status,
            recommended_action=_RECOMMENDED_ACTION.get(c.status, "unknown"),
            reason=_REASON.get(c.status, "No recommendation available."),
        )
        for c in comparisons
    )


def summarize_config_restore_plan(
    plan: tuple[ConfigSnapshotRestorePlanEntry, ...],
) -> ConfigSnapshotRestorePlanSummary:
    """Derive action-count summary from a restore plan.

    Parameters
    ----------
    plan : tuple[ConfigSnapshotRestorePlanEntry, ...]
        Restore plan entries from ``build_config_restore_plan()``.

    Returns
    -------
    ConfigSnapshotRestorePlanSummary
        Immutable summary with counts for each known action type.
    """
    no_action_for_match = sum(1 for e in plan if e.recommended_action == "no_action_for_match")
    review_difference = sum(1 for e in plan if e.recommended_action == "review_difference")
    can_restore = sum(1 for e in plan if e.recommended_action == "can_restore_missing_current")
    no_archive = sum(1 for e in plan if e.recommended_action == "no_archive_snapshot")
    known = no_action_for_match + review_difference + can_restore + no_archive
    unknown = len(plan) - known
    return ConfigSnapshotRestorePlanSummary(
        total=len(plan),
        no_action_for_match=no_action_for_match,
        review_difference=review_difference,
        can_restore_missing_current=can_restore,
        no_archive_snapshot=no_archive,
        unknown=unknown,
    )


def _evidence_to_dict(e: ConfigSnapshotEvidence) -> dict[str, str]:
    """Serialize one ConfigSnapshotEvidence to a plain dict."""
    return {"filename": e.filename, "sha256": e.sha256}


def _summary_to_dict(s: ConfigSnapshotComparisonSummary) -> dict[str, int]:
    """Serialize ConfigSnapshotComparisonSummary to a plain dict."""
    return {
        "total": s.total,
        "match": s.match,
        "different": s.different,
        "missing_current": s.missing_current,
        "no_archive_evidence": s.no_archive_evidence,
    }


def config_evidence_to_dict(
    preview: ArchiveImportPreview,
) -> dict[str, Any]:
    """Serialize all config snapshot evidence from an ArchiveImportPreview
    to a plain, JSON-compatible dict.

    Parameters
    ----------
    preview : ArchiveImportPreview
        The immutable import preview (e.g. from ``build_preview()``).

    Returns
    -------
    dict
        ``{filename: ..., sha256: ..., comparisons: [...], summary: {...}}``
        All values are plain Python dicts/lists; no dataclasses.
    """
    restore_plan = build_config_restore_plan(preview.config_snapshot_comparisons)
    restore_summary = summarize_config_restore_plan(restore_plan)
    return {
        "config_snapshot_files": list(preview.plan.config_snapshot_files),
        "config_snapshot_evidence": [
            _evidence_to_dict(e) for e in preview.plan.config_snapshot_evidence
        ],
        "config_snapshot_comparisons": [
            _comparison_to_dict(c) for c in preview.config_snapshot_comparisons
        ],
        "config_snapshot_summary": _summary_to_dict(preview.config_snapshot_summary),
        "config_snapshot_restore_plan": [
            {
                "filename": e.filename,
                "comparison_status": e.comparison_status,
                "recommended_action": e.recommended_action,
                "reason": e.reason,
            }
            for e in restore_plan
        ],
        "config_snapshot_restore_plan_summary": {
            "total": restore_summary.total,
            "no_action_for_match": restore_summary.no_action_for_match,
            "review_difference": restore_summary.review_difference,
            "can_restore_missing_current": restore_summary.can_restore_missing_current,
            "no_archive_snapshot": restore_summary.no_archive_snapshot,
            "unknown": restore_summary.unknown,
        },
    }


def archive_preview_to_dict(preview: ArchiveImportPreview) -> dict[str, Any]:
    """Serialize an ArchiveImportPreview to a plain, JSON-compatible dict."""
    return {
        "plan": {
            "archive_root": str(preview.plan.archive_root),
            "archive_version": preview.plan.archive_version,
            "experiment_name": preview.plan.experiment_name,
            "files": list(preview.plan.files),
            "verified": preview.plan.verified,
        },
        "strategy_uid": preview.strategy_uid,
        "strategy_name": preview.strategy_name,
        "dataset_id": preview.dataset_id,
        "dataset_symbol": preview.dataset_symbol,
        "dataset_timeframe": preview.dataset_timeframe,
        "validation_passed": preview.validation_passed,
        "strategy_collision": preview.strategy_collision,
        "dataset_collision": preview.dataset_collision,
        "config": config_evidence_to_dict(preview),
    }


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

        config_snapshot_files = tuple(
            f for f in manifest.files if f in _CONFIG_SNAPSHOT_NAMES
        )

        return ArchiveImportPlan(
            archive_root=self.archive_dir,
            archive_version=manifest.archive_version,
            experiment_name=manifest.experiment_name,
            files=tuple(manifest.files),
            verified=verified,
            config_snapshot_files=config_snapshot_files,
            config_snapshot_evidence=tuple(
                ConfigSnapshotEvidence(filename=f, sha256=manifest.content_hashes[f])
                for f in config_snapshot_files
                if f in manifest.content_hashes
            ),
        )

    def build_preview(
        self,
        collision_detector: IImportCollisionDetector | None = None,
        *,
        project_config_dir: str | Path | None = None,
    ) -> ArchiveImportPreview:
        """Verify the archive and build a read-only import preview/dry-run summary.

        Parameters
        ----------
        collision_detector : IImportCollisionDetector or None
            Optional read-only collision detector to check strategy and dataset status.
        project_config_dir : str, Path, or None
            Optional active project config directory for read-only config
            snapshot comparison evidence.

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

        config_snapshot_comparisons = ()
        if project_config_dir is not None:
            config_snapshot_comparisons = compare_config_snapshots(
                plan, Path(project_config_dir)
            )

        config_snapshot_summary = (
            summarize_config_comparisons(config_snapshot_comparisons)
            if config_snapshot_comparisons
            else ConfigSnapshotComparisonSummary()
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
            config_snapshot_comparisons=config_snapshot_comparisons,
            config_snapshot_summary=config_snapshot_summary,
        )
