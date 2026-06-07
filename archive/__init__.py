"""Quant Strategy Lab — Reproducible Experiment Archive

Design-phase package. Currently contains manifest, verifier, and integrity
checking only.  Full archive builder / exporter / importer not yet implemented.
"""

__all__ = [
    "ArchiveIntegrityError",
    "ArchiveManifest",
    "ArchiveVerifier",
    "DatasetSnapshotResult",
    "write_dataset_snapshot",
]

from archive.manifest import ArchiveManifest, ArchiveIntegrityError
from archive.verifier import ArchiveVerifier
from archive.dataset_snapshot import DatasetSnapshotResult, write_dataset_snapshot
