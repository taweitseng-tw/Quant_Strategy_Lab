"""Archive import preview service - read-only application-layer facade.

Wraps ArchiveImporter.build_preview() and archive_preview_to_dict(),
returning plain dict data for future UI/report callers.
No PySide6 or UI imports.
"""

from __future__ import annotations

from pathlib import Path

from archive.importer import (
    ArchiveImporter,
    ArchiveImporterError,
    IImportCollisionDetector,
    IncompatibleSchemaError,
    archive_preview_to_dict,
)
from archive.manifest import ArchiveIntegrityError


class ArchiveImportPreviewServiceError(Exception):
    """Base exception for ArchiveImportPreviewService failures.

    The ``__cause__`` chain carries the underlying archive-layer error.
    """


class ArchiveImportPreviewService:
    """Read-only service that builds an archive import preview and returns
    plain dict data suitable for UI/report serialization.

    This service performs no writes and does not import UI libraries.
    """

    def build_preview(
        self,
        archive_dir: str | Path,
        *,
        collision_detector: IImportCollisionDetector | None = None,
        project_config_dir: str | Path | None = None,
    ) -> dict:
        """Verify an archive and return plain dict preview evidence.

        Parameters
        ----------
        archive_dir : str or Path
            Path to the archive folder root.
        collision_detector : IImportCollisionDetector or None
            Optional read-only detector for strategy and dataset collisions.
        project_config_dir : str, Path, or None
            Optional active project config directory for read-only config
            snapshot comparison evidence.

        Returns
        -------
        dict
            JSON-compatible full archive import preview data.

        Raises
        ------
        ArchiveImportPreviewServiceError
            If the archive cannot be read, verified, or previewed.
            The underlying error is preserved in ``__cause__``.
        """
        try:
            importer = ArchiveImporter(archive_dir)
            preview = importer.build_preview(
                collision_detector,
                project_config_dir=project_config_dir,
            )
            return archive_preview_to_dict(preview)
        except (
            ArchiveImporterError,
            IncompatibleSchemaError,
            ArchiveIntegrityError,
        ) as exc:
            raise ArchiveImportPreviewServiceError(
                f"Failed to build archive import preview: {exc}"
            ) from exc
