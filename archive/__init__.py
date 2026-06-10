"""Quant Strategy Lab — Reproducible Experiment Archive

Design-phase package. Contains manifest, verifier, integrity checking, a first-pass
builder collector, folder exporter, and importer verification skeleton. Database
import is not yet implemented.
"""


__all__ = [
    "ArchiveIntegrityError",
    "ArchiveManifest",
    "ArchiveVerifier",
    "DatasetSnapshotResult",
    "write_dataset_snapshot",
    "ArchiveBuilder",
    "ArchiveBuilderError",
    "MissingStrategyError",
    "MissingDatasetError",
    "MissingDatasetSnapshotError",
    "MissingValidationResultError",
    "StrategyValidationFailedError",
    "MissingDisclaimerError",
    "ArchiveExporter",
    "ArchiveExporterError",
    "ExportDataUnavailableError",
    "ArchiveImporter",
    "ArchiveImporterError",
    "IncompatibleSchemaError",
    "ConfigSnapshotEvidence",
    "ConfigSnapshotComparison",
    "ConfigSnapshotComparisonSummary",
    "ConfigSnapshotRestorePlanEntry",
    "build_config_restore_plan",
    "compare_config_snapshots",
    "summarize_config_comparisons",
    "config_evidence_to_dict",
    "archive_preview_to_dict",
    "ArchiveImportPlan",
    "IImportCollisionDetector",
    "ArchiveImportPreview",
]

from archive.manifest import ArchiveManifest, ArchiveIntegrityError
from archive.verifier import ArchiveVerifier
from archive.dataset_snapshot import DatasetSnapshotResult, write_dataset_snapshot
from archive.builder import (
    ArchiveBuilder,
    ArchiveBuilderError,
    MissingStrategyError,
    MissingDatasetError,
    MissingDatasetSnapshotError,
    MissingValidationResultError,
    StrategyValidationFailedError,
    MissingDisclaimerError,
)
from archive.exporter import ArchiveExporter, ArchiveExporterError, ExportDataUnavailableError
from archive.importer import (
    ArchiveImporter,
    ArchiveImporterError,
    IncompatibleSchemaError,
    ConfigSnapshotEvidence,
    ConfigSnapshotComparison,
    ConfigSnapshotComparisonSummary,
    ConfigSnapshotRestorePlanEntry,
    build_config_restore_plan,
    compare_config_snapshots,
    summarize_config_comparisons,
    config_evidence_to_dict,
    archive_preview_to_dict,
    ArchiveImportPlan,
    IImportCollisionDetector,
    ArchiveImportPreview,
)
