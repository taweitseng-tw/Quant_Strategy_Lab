"""ArchiveImporter — verification skeleton for reproducible experiment archives.

Reads and validates manifest schema version compatibility, runs integrity checks,
and returns an import plan. No database or filesystem mutations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from archive.manifest import ArchiveManifest, ArchiveIntegrityError


class ArchiveImporterError(Exception):
    """Base exception for all ArchiveImporter errors."""


class IncompatibleSchemaError(ArchiveImporterError):
    """Raised when the archive schema version is incompatible, missing, or malformed."""


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
    """
    archive_root: Path
    archive_version: str
    experiment_name: str
    files: tuple[str, ...]
    verified: bool


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
        )
