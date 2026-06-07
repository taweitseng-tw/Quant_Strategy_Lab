"""Archive manifest model and integrity error type."""

from __future__ import annotations

from dataclasses import dataclass, field


class ArchiveIntegrityError(Exception):
    """Raised when an archive fails integrity verification."""


@dataclass
class ArchiveManifest:
    """Metadata and file listing for a reproducible experiment archive.

    Fields
    ------
    archive_version : str
        Schema version, e.g. ``"1.0.0"``.
    experiment_name : str
        Human-readable name for the archived experiment.
    generated_at : str
        ISO-8601 timestamp of archive creation.
    generator_version : str
        QSL software version at archive time.
    files : list[str]
        Relative paths to all files in the archive.
    content_hashes : dict[str, str]
        ``{filename: sha256_hex}`` for every file in ``files``.
    disclaimer_path : str
        Path to ``disclaimer.txt`` inside the archive.
    """

    archive_version: str
    experiment_name: str
    generated_at: str
    generator_version: str
    files: list[str] = field(default_factory=list)
    content_hashes: dict[str, str] = field(default_factory=dict)
    disclaimer_path: str = "disclaimer.txt"
